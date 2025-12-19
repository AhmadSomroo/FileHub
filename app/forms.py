from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from .models import RoleEnum, PermissionEnum
import re

def validate_strong_password(form, field):
    """
    Validate password strength:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    password = field.data
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter.")
    
    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least one digit.")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>).")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 80)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ChangePasswordForm(FlaskForm):
    password = PasswordField("New password", validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long."),
        validate_strong_password
    ])
    confirm = PasswordField("Confirm password", validators=[
        DataRequired(), 
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField("Change password")

class UploadForm(FlaskForm):
    file = FileField("File", validators=[DataRequired()])
    permission = SelectField("Permission", choices=[
        (PermissionEnum.private.value, "Private (owner only)"),
        (PermissionEnum.teacher_only.value, "Teachers + Owner"),
        (PermissionEnum.staff_teacher.value, "Staff + Teachers + Owner"),
        (PermissionEnum.public.value, "Public")
    ], validators=[DataRequired()])
    submit = SubmitField("Upload")

class CreateUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1,80)])
    role = SelectField("Role", choices=[
        (RoleEnum.student.value, "Student"),
        (RoleEnum.teacher.value, "Teacher"),
        (RoleEnum.staff.value, "Staff"),
        (RoleEnum.admin.value, "Admin")
    ], validators=[DataRequired()])
    temp_password = PasswordField("Temporary password", validators=[
        DataRequired(), 
        Length(min=8, message="Password must be at least 8 characters long."),
        validate_strong_password
    ])
    submit = SubmitField("Create")
