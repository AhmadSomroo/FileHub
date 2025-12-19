#!/usr/bin/env python3
"""
Migration script to add file_hash and file_size columns to files table
Run this once to update your existing database
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add new columns if they don't exist
        with db.engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(text("PRAGMA table_info(files)"))
            columns = [row[1] for row in result]
            
            if 'file_hash' not in columns:
                print("Adding file_hash column...")
                conn.execute(text("ALTER TABLE files ADD COLUMN file_hash VARCHAR(64)"))
                conn.commit()
                print("✓ Added file_hash column")
            else:
                print("✓ file_hash column already exists")
            
            if 'file_size' not in columns:
                print("Adding file_size column...")
                conn.execute(text("ALTER TABLE files ADD COLUMN file_size INTEGER"))
                conn.commit()
                print("✓ Added file_size column")
            else:
                print("✓ file_size column already exists")
        
        # Calculate hashes for existing files
        from app.models import File
        from app.utils import calculate_file_hash, file_path_for
        import os
        
        files_without_hash = File.query.filter_by(file_hash=None).all()
        
        if files_without_hash:
            print(f"\nCalculating hashes for {len(files_without_hash)} existing files...")
            updated = 0
            
            for file_obj in files_without_hash:
                try:
                    file_path = file_path_for(file_obj.stored_filename)
                    if os.path.exists(file_path):
                        file_obj.file_hash = calculate_file_hash(file_path)
                        file_obj.file_size = os.path.getsize(file_path)
                        updated += 1
                        print(f"  ✓ {file_obj.original_filename}")
                    else:
                        print(f"  ✗ {file_obj.original_filename} (file not found)")
                except Exception as e:
                    print(f"  ✗ {file_obj.original_filename} (error: {e})")
            
            db.session.commit()
            print(f"\n✓ Updated {updated} files with hash values")
        else:
            print("\n✓ All files already have hash values")
        
        print("\n✅ Migration completed successfully!")
        print("File integrity checking is now enabled.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("If you're starting fresh, you can delete data.db and restart the app.")
