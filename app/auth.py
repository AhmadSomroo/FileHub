from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .forms import LoginForm, ChangePasswordForm
from .models import User
from . import db, limiter

auth_bp = Blueprint("auth", __name__, url_prefix="")

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    from .utils import log_audit_event
    
    if current_user.is_authenticated:
        return redirect(url_for("files_bp.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if user exists
        if user:
            # Check if account is deactivated
            if not user.is_active:
                log_audit_event(
                    action="login_blocked",
                    status="blocked",
                    user=user,
                    details="Account is deactivated"
                )
                flash("Your account has been deactivated. Please contact the administrator.", "danger")
                return render_template("login.html", form=form)
            
            # Check if account is locked
            if user.is_locked():
                from datetime import datetime
                time_remaining = (user.locked_until - datetime.utcnow()).total_seconds()
                minutes = int(time_remaining // 60)
                seconds = int(time_remaining % 60)
                
                # Log blocked login attempt
                log_audit_event(
                    action="login_blocked",
                    status="blocked",
                    user=user,
                    details=f"Account locked. Time remaining: {minutes}m {seconds}s"
                )
                
                flash(f"Account locked due to multiple failed login attempts. Try again in {minutes}m {seconds}s.", "danger")
                return render_template("login.html", form=form)
            
            # Check password
            if user.check_password(form.password.data):
                # Successful login - reset failed attempts
                user.reset_failed_logins()
                db.session.commit()
                login_user(user)
                
                # Log successful login
                log_audit_event(
                    action="login_success",
                    status="success",
                    user=user,
                    details=f"User role: {user.role.value}, First login: {user.first_login}"
                )
                
                # enforce first-login password change
                if user.first_login:
                    flash("Change your temporary password before continuing.", "warning")
                    return redirect(url_for("auth.change_password"))
                next_page = request.args.get("next") or url_for("files_bp.dashboard")
                return redirect(next_page)
            else:
                # Wrong password - record failed attempt
                user.record_failed_login()
                db.session.commit()
                
                # Log failed login
                log_audit_event(
                    action="login_failed",
                    status="failed",
                    user=user,
                    details=f"Invalid password. Attempts: {user.failed_login_attempts}/3"
                )
                
                remaining_attempts = 3 - user.failed_login_attempts
                if remaining_attempts > 0:
                    flash(f"Invalid username or password. {remaining_attempts} attempt(s) remaining before lockout.", "danger")
                else:
                    flash("Account locked for 3 minutes due to multiple failed login attempts.", "danger")
        else:
            # User doesn't exist - show generic error to prevent username enumeration
            # Log failed attempt with username (for security monitoring)
            log_audit_event(
                action="login_failed",
                status="failed",
                user=None,
                details=f"Unknown username: {form.username.data}"
            )
            flash("Invalid username or password", "danger")
    
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    from .utils import log_audit_event
    
    # Log logout before clearing session
    log_audit_event(
        action="logout",
        status="success",
        user=current_user,
        details="User logged out"
    )
    
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        current_user.first_login = False
        db.session.commit()
        flash("Password changed successfully", "success")
        return redirect(url_for("files_bp.dashboard"))
    return render_template("change_password.html", form=form, is_first_login=current_user.first_login)
