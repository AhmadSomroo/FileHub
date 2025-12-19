from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .forms import CreateUserForm
from .models import User, RoleEnum
from . import db, limiter

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin access required.", "danger")
            return redirect(url_for("files_bp.dashboard"))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
@admin_required
def users():
    from flask import session
    
    # Retrieve and clear temporary password from session
    temp_password = session.pop('temp_password', None)
    temp_password_user = session.pop('temp_password_user', None)
    form = CreateUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("admin.users"))
        u = User(username=form.username.data, role=RoleEnum(form.role.data))
        u.set_password(form.temp_password.data)
        u.first_login = True
        u.is_active = True
        db.session.add(u)
        db.session.commit()
        
        # Log user creation
        from .utils import log_audit_event
        log_audit_event(
            action="user_created",
            status="success",
            user=current_user,
            details=f"Created user: {u.username}, role: {u.role.value}"
        )
        
        flash("User created.", "success")
        return redirect(url_for("admin.users"))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users, form=form, temp_password=temp_password, temp_password_user=temp_password_user)

@admin_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@admin_required
@limiter.limit("10 per minute")
def toggle_user_status(user_id):
    from .utils import log_audit_event
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.users"))
    
    # Toggle status
    user.is_active = not user.is_active
    status_text = "activated" if user.is_active else "deactivated"
    
    db.session.commit()
    
    # Log the action
    log_audit_event(
        action=f"user_{status_text}",
        status="success",
        user=current_user,
        details=f"{status_text.capitalize()} user: {user.username}"
    )
    
    flash(f"User {user.username} has been {status_text}.", "success")
    return redirect(url_for("admin.users"))

@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
@limiter.limit("5 per minute")
def reset_password(user_id):
    from flask import session
    from .utils import log_audit_event
    import secrets
    import string
    
    user = User.query.get_or_404(user_id)
    
    # Generate random temporary password
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
    
    # Reset password
    user.set_password(temp_password)
    user.first_login = True
    user.failed_login_attempts = 0
    user.locked_until = None
    
    db.session.commit()
    
    # Log the action
    log_audit_event(
        action="password_reset",
        status="success",
        user=current_user,
        details=f"Reset password for user: {user.username}"
    )
    
    # Store password in session temporarily (more secure than flash)
    session['temp_password'] = temp_password
    session['temp_password_user'] = user.username
    
    flash(f"Password reset for {user.username}. Click 'View Password' to see the temporary password.", "success")
    return redirect(url_for("admin.users"))
