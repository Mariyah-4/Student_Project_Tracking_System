import os, uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import Submission, Project, ClassRoom
from services.access import roles_required, get_project_or_404
from services.activity import log_activity, notify

submissions_bp = Blueprint("submissions", __name__, url_prefix="/submissions")

@submissions_bp.post("/project/<int:project_id>")
@login_required
@roles_required("student")
def submit(project_id):
    project = get_project_or_404(project_id)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename or "." not in uploaded.filename:
        flash("Choose a file to submit.", "warning")
        return redirect(url_for("projects.detail", project_id=project.id))
    ext = uploaded.filename.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        flash("This file type is not allowed.", "danger")
        return redirect(url_for("projects.detail", project_id=project.id))
    original = secure_filename(uploaded.filename)
    stored = f"{uuid.uuid4().hex}_{original}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    uploaded.save(os.path.join(current_app.config["UPLOAD_FOLDER"], stored))
    item = Submission(project=project, submitted_by=current_user.id, stored_name=stored,
                      original_name=original, note=request.form.get("note", "").strip())
    db.session.add(item)
    log_activity(project, current_user, "project_submitted", f"Submitted {original}.", new_value=original)
    if project.classroom:
        notify(project.classroom.teacher, "Project submitted", f"{project.title} has a new submission.", url_for("submissions.teacher_inbox"))
    db.session.commit()
    flash("Project submitted to your teacher.", "success")
    return redirect(url_for("projects.detail", project_id=project.id))

@submissions_bp.get("/teacher")
@login_required
@roles_required("teacher")
def teacher_inbox():
    items = Submission.query.join(Project).join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id).order_by(Submission.submitted_at.desc()).all()
    return render_template("submissions/teacher.html", items=items)

@submissions_bp.get("/<int:submission_id>/download")
@login_required
def download(submission_id):
    item = Submission.query.get_or_404(submission_id)
    if current_user.role == "teacher":
        allowed = item.project.classroom and item.project.classroom.teacher_id == current_user.id
    else:
        allowed = current_user.id == item.submitted_by or current_user in item.project.members
    if not allowed:
        abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], item.stored_name, as_attachment=True, download_name=item.original_name)

@submissions_bp.post("/<int:submission_id>/evaluate")
@login_required
@roles_required("teacher")
def evaluate(submission_id):
    item = Submission.query.get_or_404(submission_id)
    if not item.project.classroom or item.project.classroom.teacher_id != current_user.id:
        abort(403)
    status = request.form.get("status")
    if status not in ("approved", "revision_requested"):
        abort(400)
    try:
        marks = float(request.form.get("marks", "")) if request.form.get("marks", "").strip() else None
        if marks is not None and not 0 <= marks <= 100:
            raise ValueError()
    except ValueError:
        flash("Marks must be between 0 and 100.", "danger")
        return redirect(url_for("submissions.teacher_inbox"))
    item.status = status
    item.marks = marks
    item.feedback = request.form.get("feedback", "").strip()
    item.evaluated_at = datetime.utcnow()
    log_activity(item.project, current_user, "submission_evaluated", f"Teacher marked submission as {status}.", new_value=f"{status}; marks={marks}")
    notify(item.student, "Submission evaluated", f"Your project '{item.project.title}' was evaluated.", url_for("projects.detail", project_id=item.project.id))
    db.session.commit()
    flash("Evaluation saved.", "success")
    return redirect(url_for("submissions.teacher_inbox"))
