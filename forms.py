from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class RegistrationForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    role = SelectField("Account type", choices=[("student", "Student"), ("teacher", "Teacher")], validators=[DataRequired()])
    student_id = StringField("Student ID (students only)", validators=[Optional(), Length(max=40)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")

class ClassForm(FlaskForm):
    name = StringField("Class name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Create class")

class EnrollForm(FlaskForm):
    email = StringField("Student email", validators=[DataRequired(), Email()])
    submit = SubmitField("Enroll student")

class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    body = TextAreaField("Announcement", validators=[DataRequired()])
    submit = SubmitField("Post announcement")

class ProjectForm(FlaskForm):
    title = StringField("Project title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[Optional()])
    classroom_id = SelectField("Class", coerce=int, choices=[], validators=[Optional()])
    submit = SubmitField("Create project")

class TaskForm(FlaskForm):
    title = StringField("Task title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[Optional()])
    assigned_to = SelectField("Assign to", coerce=int, choices=[], validators=[Optional()])
    submit = SubmitField("Add task")
