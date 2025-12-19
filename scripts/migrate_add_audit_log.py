#!/usr/bin/env python3
"""
Migration script to add audit_logs table
Run this once to update your existing database
"""
from app import create_app, db

app = create_app()

with app.app_context():
    try:
        # Create audit_logs table
        print("Creating audit_logs table...")
        db.create_all()
        print("✓ audit_logs table created successfully")
        
        print("\n✅ Migration completed successfully!")
        print("Audit logging is now enabled for:")
        print("  - Login attempts (success/failed/blocked)")
        print("  - Logout events")
        print("  - File uploads")
        print("  - File downloads")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("If the table already exists, this is normal.")
