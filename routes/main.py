from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import ClassRoom, Project, Notification, Attendance, Message, ClassEnrollment

main_bp = Blueprint("main", __name__)

@main_bp.get("/")
def index():
    return render_template("index.html")

@main_bp.get("/dashboard")
@login_required
def dashboard():
    if current_user.role == "teacher":
        classes = ClassRoom.query.filter_by(teacher_id=current_user.id).all()
        projects = Project.query.join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id).all()
    else:
        classes = [e.classroom for e in current_user.memberships]
        projects = Project.query.join(Project.members).filter_by(id=current_user.id).all()
    unread = Notification.query.filter_by(user_id=current_user.id, read_at=None).count()
    return render_template("dashboard.html", classes=classes, projects=projects, unread=unread)

@main_bp.get("/profile")
@login_required
def profile():
    stats = current_user.attendance_stats() if current_user.role == "student" else None
    return render_template("profile.html", stats=stats)

@main_bp.get("/notifications")
@login_required
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", items=items)
