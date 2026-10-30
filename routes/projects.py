import os, uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Project, ProjectTask, ProjectFile, User, ClassRoom
from forms import ProjectForm, TaskForm
from services.access import roles_required, get_project_or_404, can_access_project
from services.activity import log_activity, notify

projects_bp = Blueprint("projects", __name__, url_prefix="/projects")

def allowed_file(filename):
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

@projects_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("student")
def create():
    form = ProjectForm()
    form.classroom_id.choices = [(0, "Personal / no class")] + [(e.classroom.id, e.classroom.name) for e in current_user.memberships]
    if form.validate_on_submit():
        class_id = form.classroom_id.data or None
        project = Project(title=form.title.data.strip(), description=form.description.data or "",
                          classroom_id=class_id, creator=current_user)
        project.members.append(current_user)
        db.session.add(project)
        db.session.flush()
        log_activity(project, current_user, "project_created", "Created the project.")
        db.session.commit()
        return redirect(url_for("projects.detail", project_id=project.id))
    return render_template("projects/form.html", form=form, heading="Create project")

@projects_bp.get("/")
@login_required
def index():
    if current_user.role == "teacher":
        projects = Project.query.join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id).all()
    else:
        projects = Project.query.join(Project.members).filter_by(id=current_user.id).all()
    return render_template("projects/index.html", projects=projects)

@projects_bp.get("/<int:project_id>")
@login_required
def detail(project_id):
    project = get_project_or_404(project_id)
    task_form = TaskForm()
    task_form.assigned_to.choices = [(0, "Unassigned")] + [(m.id, m.name) for m in project.members]
    return render_template("projects/detail.html", project=project, task_form=task_form)

@projects_bp.post("/<int:project_id>/invite")
@login_required
@roles_required("student")
def invite(project_id):
    project = get_project_or_404(project_id)
    email = request.form.get("email", "").lower().strip()
    student = User.query.filter_by(email=email, role="student").first()
    if not student:
        flash("Student account not found.", "danger")
    elif student in project.members:
        flash("That student is already a collaborator.", "info")
    elif project.classroom_id and not any(e.student_id == student.id for e in project.classroom.enrollments):
        flash("Invitees must be enrolled in the same class.", "danger")
    else:
        project.members.append(student)
        log_activity(project, current_user, "member_invited", f"Invited {student.name}.", new_value=student.email)
        notify(student, "Project invitation", f"You were added to {project.title}.", url_for("projects.detail", project_id=project.id))
        db.session.commit()
        flash("Collaborator added.", "success")
    return redirect(url_for("projects.detail", project_id=project.id))

@projects_bp.post("/<int:project_id>/tasks")
@login_required
@roles_required("student")
def add_task(project_id):
    project = get_project_or_404(project_id)
    form = TaskForm()
    form.assigned_to.choices = [(0, "Unassigned")] + [(m.id, m.name) for m in project.members]
    if form.validate_on_submit():
        assignee = form.assigned_to.data or None
        if assignee and not any(m.id == assignee for m in project.members):
            abort(400)
        task = ProjectTask(project=project, title=form.title.data.strip(), description=form.description.data or "",
                           assigned_to=assignee, created_by=current_user.id)
        db.session.add(task)
        log_activity(project, current_user, "task_created", f"Created task: {task.title}.", new_value=task.title)
        db.session.commit()
        flash("Task added.", "success")
    return redirect(url_for("projects.detail", project_id=project.id))

@projects_bp.post("/<int:project_id>/tasks/<int:task_id>/status")
@login_required
@roles_required("student")
def task_status(project_id, task_id):
    project = get_project_or_404(project_id)
    task = ProjectTask.query.filter_by(id=task_id, project_id=project.id).first_or_404()
    new_status = request.form.get("status")
    if new_status not in ("todo", "doing", "done"):
        abort(400)
    old = task.status
    task.status = new_status
    log_activity(project, current_user, "task_status_changed", f"Changed task '{task.title}' status.", old, new_status)
    db.session.commit()
    return redirect(url_for("projects.detail", project_id=project.id))

@projects_bp.post("/<int:project_id>/upload")
@login_required
@roles_required("student")
def upload(project_id):
    project = get_project_or_404(project_id)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a file first.", "warning")
    elif not allowed_file(uploaded.filename):
        flash("This file type is not allowed.", "danger")
    else:
        original = secure_filename(uploaded.filename)
        stored = f"{uuid.uuid4().hex}_{original}"
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        uploaded.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored))
        db.session.add(ProjectFile(project=project, uploader_id=current_user.id, original_name=original, stored_name=stored))
        log_activity(project, current_user, "file_uploaded", f"Uploaded file: {original}.", new_value=original)
        db.session.commit()
        flash("File uploaded.", "success")
    return redirect(url_for("projects.detail", project_id=project.id))

@projects_bp.get("/files/<int:file_id>/download")
@login_required
def download_file(file_id):
    item = ProjectFile.query.get_or_404(file_id)
    if not can_access_project(item.project):
        abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], item.stored_name, as_attachment=True, download_name=item.original_name)
