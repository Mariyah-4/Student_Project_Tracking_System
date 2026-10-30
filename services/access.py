from functools import wraps
from flask import abort
from flask_login import current_user
from models import Project, ClassRoom, ClassEnrollment

def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator

def can_access_project(project):
    if current_user.role == "teacher":
        return project.classroom is not None and project.classroom.teacher_id == current_user.id
    return current_user in project.members

def get_project_or_404(project_id):
    from flask import abort
    project = Project.query.get_or_404(project_id)
    if not can_access_project(project):
        abort(403)
    return project

def get_class_or_404(class_id):
    from flask import abort
    classroom = ClassRoom.query.get_or_404(class_id)
    allowed = classroom.teacher_id == current_user.id if current_user.role == "teacher" else ClassEnrollment.query.filter_by(classroom_id=class_id, student_id=current_user.id).first() is not None
    if not allowed:
        abort(403)
    return classroom
