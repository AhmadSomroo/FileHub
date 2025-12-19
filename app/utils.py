import uuid
import os
import hashlib
from typing import Tuple
from werkzeug.utils import secure_filename
from flask import current_app
from .models import User, File

def allowed_file(filename: str) -> bool:
    """
    Check if the file extension is allowed.
    Returns True if file has an allowed extension, False otherwise.
    """
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']

def get_file_extension(filename: str) -> str:
    """Get the file extension from filename"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def validate_file_size(file_storage) -> Tuple[bool, str]:
    """
    Validate file size before processing.
    Returns (is_valid, error_message)
    """
    # Check if file has content
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)  # Reset to beginning
    
    max_size = current_app.config['MAX_CONTENT_LENGTH']
    
    if file_size == 0:
        return False, "File is empty."
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        return False, f"File size exceeds maximum allowed size of {max_mb:.0f} MB."
    
    return True, ""

def unique_filename(original_filename: str) -> str:
    safe = secure_filename(original_filename)
    uid = uuid.uuid4().hex
    return f"{uid}_{safe}"

def file_path_for(stored_filename: str) -> str:
    return os.path.join(current_app.config['UPLOAD_FOLDER'], stored_filename)

def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.
    Returns hex digest of the hash.
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def verify_file_integrity(file_path: str, expected_hash: str) -> Tuple[bool, str]:
    """
    Verify file integrity by comparing hash.
    Returns (is_valid, message)
    """
    try:
        if not os.path.exists(file_path):
            return False, "File not found"
        
        current_hash = calculate_file_hash(file_path)
        
        if current_hash == expected_hash:
            return True, "File integrity verified"
        else:
            return False, "File integrity check failed - file may be corrupted or tampered with"
    
    except Exception as e:
        return False, f"Error verifying file: {str(e)}"


def can_view_file(user, file_obj):
    """
    Return True if `user` can view `file_obj` based on permissions.
    Uses the permission field from the File model.
    """
    from .models import PermissionEnum, RoleEnum
    
    # Admin can see everything
    if user.is_admin():
        return True
    
    # Owner can always see their own files
    if file_obj.owner_id == user.id:
        return True
    
    # Check permission levels
    if file_obj.permission == PermissionEnum.public:
        return True
    elif file_obj.permission == PermissionEnum.staff_teacher:
        return user.is_staff() or user.is_teacher()
    elif file_obj.permission == PermissionEnum.teacher_only:
        return user.is_teacher()
    elif file_obj.permission == PermissionEnum.private:
        return False  # Only owner (already checked above)
    
    return False

def log_audit_event(action, status, user=None, details=None):
    """
    Log an audit event to the database.
    
    Args:
        action: Type of action (login_success, login_failed, file_upload, etc.)
        status: Status of the action (success, failed, blocked)
        user: User object (optional, for anonymous actions)
        details: Additional details as string or dict
    """
    from flask import request
    from .models import AuditLog
    from . import db
    import json
    
    try:
        # Get IP address
        ip_address = request.remote_addr if request else None
        
        # Get user agent
        user_agent = request.headers.get('User-Agent', '')[:255] if request else None
        
        # Convert details to JSON string if it's a dict
        if isinstance(details, dict):
            details = json.dumps(details)
        
        # Create audit log entry
        log_entry = AuditLog(
            user_id=user.id if user else None,
            username=user.username if user else None,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            status=status
        )
        
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        # Don't let logging errors break the application
        print(f"Audit logging error: {e}")
        db.session.rollback()
