from . import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime
import enum
from sqlalchemy import Enum, Column, Integer, String, Boolean, DateTime, ForeignKey, Text

class RoleEnum(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    staff = "staff"
    admin = "admin"

class PermissionEnum(str, enum.Enum):
    private = "private"                # owner only (owner file)
    teacher_only = "teacher_only"      # owner + teachers (and admin)
    staff_teacher = "staff_teacher"    # staff + teachers + admin
    public = "public"                  # everyone

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.student)
    first_login = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Brute force protection fields
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_locked(self):
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        if datetime.utcnow() < self.locked_until:
            return True
        # Lock expired, reset
        self.failed_login_attempts = 0
        self.locked_until = None
        return False
    
    def record_failed_login(self):
        """Record a failed login attempt and lock if threshold reached"""
        from datetime import timedelta
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 3:
            self.locked_until = datetime.utcnow() + timedelta(minutes=3)
    
    def reset_failed_logins(self):
        """Reset failed login attempts on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None

    def is_student(self):
        return self.role == RoleEnum.student

    def is_teacher(self):
        return self.role == RoleEnum.teacher

    def is_staff(self):
        return self.role == RoleEnum.staff

    def is_admin(self):
        return self.role == RoleEnum.admin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class File(db.Model):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)  # UUID_realname
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(Enum(PermissionEnum), nullable=False, default=PermissionEnum.teacher_only)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    mimetype = Column(String(255))
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for integrity checking
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    # Relationship to User
    owner = db.relationship('User', backref='files', lazy=True)

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(80), nullable=True)  # Store username in case user is deleted
    action = Column(String(50), nullable=False)  # login_success, login_failed, file_upload, file_download, etc.
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)  # JSON or text details about the action
    status = Column(String(20), nullable=False)  # success, failed, blocked
    
    # Relationship to User
    user = db.relationship('User', backref='audit_logs', lazy=True)
