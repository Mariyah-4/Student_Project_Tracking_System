import secrets, string
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import ClassRoom, ClassEnrollment, User, Announcement, Notification
from forms import ClassForm, EnrollForm, AnnouncementForm
from services.access import roles_required, get_class_or_404
from services.activity import notify

classes_bp = Blueprint("classes", __name__, url_prefix="/classes")

def make_code():
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(7))

@classes_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("teacher")
def create():
    form = ClassForm()
    if form.validate_on_submit():
        classroom = ClassRoom(name=form.name.data.strip(), description=form.description.data or "",
                              code=make_code(), teacher_id=current_user.id)
        db.session.add(classroom)
        db.session.commit()
        flash(f"Class created. Enrollment code: {classroom.code}", "success")
        return redirect(url_for("classes.detail", class_id=classroom.id))
    return render_template("classes/form.html", form=form, heading="Create class")

@classes_bp.post("/join")
@login_required
@roles_required("student")
def join():
    code = request.form.get("code", "").strip().upper()
    classroom = ClassRoom.query.filter_by(code=code).first()
    if not classroom:
        flash("No class matches that enrollment code.", "danger")
    elif ClassEnrollment.query.filter_by(classroom_id=classroom.id, student_id=current_user.id).first():
        flash("You are already enrolled.", "info")
    else:
        db.session.add(ClassEnrollment(classroom_id=classroom.id, student_id=current_user.id))
        db.session.commit()
        flash("You joined the class.", "success")
    return redirect(url_for("main.dashboard"))

@classes_bp.get("/<int:class_id>")
@login_required
def detail(class_id):
    classroom = get_class_or_404(class_id)
    students = [e.student for e in classroom.enrollments]
    announcements = Announcement.query.filter_by(classroom_id=class_id).order_by(Announcement.created_at.desc()).all()
    return render_template("classes/detail.html", classroom=classroom, students=students, announcements=announcements, announcement_form=AnnouncementForm(), enroll_form=EnrollForm())

@classes_bp.post("/<int:class_id>/announcement")
@login_required
@roles_required("teacher")
def announcement(class_id):
    classroom = get_class_or_404(class_id)
    form = AnnouncementForm()
    if form.validate_on_submit():
        item = Announcement(classroom=classroom, teacher_id=current_user.id, title=form.title.data.strip(), body=form.body.data.strip())
        db.session.add(item)
        for enrollment in classroom.enrollments:
            notify(enrollment.student, "New class announcement", item.title, url_for("classes.detail", class_id=classroom.id))
        db.session.commit()
        flash("Announcement posted.", "success")
    return redirect(url_for("classes.detail", class_id=class_id))

@classes_bp.post("/<int:class_id>/enroll")
@login_required
@roles_required("teacher")
def enroll(class_id):
    classroom = get_class_or_404(class_id)
    form = EnrollForm()
    if form.validate_on_submit():
        student = User.query.filter_by(email=form.email.data.lower().strip(), role="student").first()
        if not student:
            flash("No student account found with that email.", "danger")
        elif ClassEnrollment.query.filter_by(classroom_id=class_id, student_id=student.id).first():
            flash("Student is already enrolled.", "info")
        else:
            db.session.add(ClassEnrollment(classroom_id=class_id, student_id=student.id))
            notify(student, "Added to a class", f"You were enrolled in {classroom.name}.", url_for("classes.detail", class_id=classroom.id))
            db.session.commit()
            flash("Student enrolled.", "success")
    return redirect(url_for("classes.detail", class_id=classroom.id))
