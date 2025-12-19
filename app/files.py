from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
import os
from werkzeug.utils import secure_filename

from .models import File, User
from .forms import UploadForm
from .utils import can_view_file
from . import db, limiter

# Create a Blueprint for all file-related routes
files_bp = Blueprint('files_bp', __name__)

# Upload folder is managed by config and created in __init__.py


@files_bp.route('/', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute")
def dashboard():
    form = UploadForm()
    
    # Load all files with owner relationship preloaded
    files = File.query.options(joinedload(File.owner)).all()
    
    # Filter files visible to current user
    visible = [f for f in files if can_view_file(current_user, f)]
    
    # Map owner IDs to usernames - ONLY for visible files (security fix)
    visible_owner_ids = {f.owner_id for f in visible}
    owner_map = {u.id: u.username for u in User.query.filter(User.id.in_(visible_owner_ids)).all()}

    if form.validate_on_submit():
        uploaded_file = form.file.data
        if uploaded_file:
            from .utils import unique_filename, file_path_for, allowed_file, validate_file_size
            from .models import PermissionEnum
            
            original_name = secure_filename(uploaded_file.filename)
            
            # Validate file type
            if not allowed_file(original_name):
                flash("Invalid file type. Allowed types: Documents (doc, docx, txt, pdf), Spreadsheets (xls, xlsx, csv), Archives (zip, rar, 7z)", "danger")
                return redirect(url_for('files_bp.dashboard'))
            
            # Validate file size
            is_valid_size, size_error = validate_file_size(uploaded_file)
            if not is_valid_size:
                flash(size_error, "danger")
                return redirect(url_for('files_bp.dashboard'))
            
            # Generate unique filename and save
            stored_name = unique_filename(original_name)
            save_path = file_path_for(stored_name)
            
            try:
                uploaded_file.save(save_path)
            except Exception as e:
                flash("Error saving file. Please try again.", "danger")
                return redirect(url_for('files_bp.dashboard'))
            
            # Calculate file hash for integrity checking
            from .utils import calculate_file_hash
            file_hash = calculate_file_hash(save_path)
            file_size = os.path.getsize(save_path)

            # Role-specific permission enforcement
            requested_permission = form.permission.data
            
            if current_user.is_student():
                # Students can only upload with teacher_only permission
                final_permission = PermissionEnum.teacher_only
                if requested_permission != PermissionEnum.teacher_only.value:
                    flash("Students can only upload files visible to teachers and owner.", "warning")
            elif current_user.is_teacher():
                # Teachers can upload with teacher_only or public permissions
                if requested_permission in [PermissionEnum.teacher_only.value, PermissionEnum.public.value]:
                    final_permission = PermissionEnum(requested_permission)
                else:
                    final_permission = PermissionEnum.teacher_only
                    flash("Teachers can only set 'Teachers + Owner' or 'Public' permissions.", "warning")
            else:
                # Staff and admin can set any permission
                final_permission = PermissionEnum(requested_permission)

            # Save file in database with permissions and hash
            new_file = File(
                original_filename=original_name,
                stored_filename=stored_name,
                owner_id=current_user.id,
                permission=final_permission,
                mimetype=uploaded_file.content_type,
                file_hash=file_hash,
                file_size=file_size
            )
            db.session.add(new_file)
            db.session.commit()
            
            # Log file upload
            from .utils import log_audit_event
            log_audit_event(
                action="file_upload",
                status="success",
                user=current_user,
                details={
                    "filename": original_name,
                    "size": file_size,
                    "mimetype": uploaded_file.content_type,
                    "permission": final_permission.value,
                    "hash": file_hash[:16] + "..."  # Log partial hash
                }
            )
            
            flash("File uploaded successfully.", "success")
            return redirect(url_for('files_bp.dashboard'))

    return render_template(
        "dashboard.html",
        files=visible,
        owner_map=owner_map,
        UploadForm=form
    )


@files_bp.route('/uploads/<filename>')
@login_required
@limiter.limit("60 per minute")
def download_file(filename):
    # Sanitize filename to prevent path traversal
    filename = secure_filename(filename)
    
    # Fetch file object from database
    file_obj = File.query.filter_by(stored_filename=filename).first_or_404()
    
    # Check if user has permission to view/download
    if not can_view_file(current_user, file_obj):
        flash("You do not have permission to download this file.", "danger")
        return redirect(url_for('files_bp.dashboard'))
    
    # Verify file exists and is within upload folder (prevent path traversal)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
    
    if not os.path.abspath(file_path).startswith(upload_folder):
        flash("Invalid file path.", "danger")
        return redirect(url_for('files_bp.dashboard'))
    
    if not os.path.exists(file_path):
        flash("File not found.", "danger")
        return redirect(url_for('files_bp.dashboard'))
    
    # Verify file integrity if hash exists - BLOCK download if corrupted
    from .utils import verify_file_integrity, log_audit_event
    if file_obj.file_hash:
        is_valid, message = verify_file_integrity(file_path, file_obj.file_hash)
        
        if not is_valid:
            # Log integrity failure
            log_audit_event(
                action="file_integrity_failed",
                status="blocked",
                user=current_user,
                details={
                    "filename": file_obj.original_filename,
                    "file_id": file_obj.id,
                    "error": message,
                    "action": "download_blocked"
                }
            )
            
            # BLOCK the download - do not allow corrupted files
            flash("🚫 Download Blocked: File integrity check failed! The file is corrupted or has been tampered with. Please contact the administrator.", "danger")
            return redirect(url_for('files_bp.dashboard'))
    
    # Log successful file download
    log_audit_event(
        action="file_download",
        status="success",
        user=current_user,
        details={
            "filename": file_obj.original_filename,
            "file_id": file_obj.id,
            "owner": file_obj.owner.username,
            "permission": file_obj.permission.value,
            "integrity_check": "passed" if file_obj.file_hash else "no_hash"
        }
    )

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True, 
        download_name=file_obj.original_filename,
        mimetype=file_obj.mimetype
    )
