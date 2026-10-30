from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Attendance, ClassEnrollment
from services.access import roles_required, get_class_or_404

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")

@attendance_bp.route("/class/<int:class_id>", methods=["GET", "POST"])
@login_required
def class_attendance(class_id):
    classroom = get_class_or_404(class_id)
    if current_user.role == "teacher":
        if request.method == "POST":
            day_text = request.form.get("attendance_date", "")
            try:
                day = date.fromisoformat(day_text)
            except ValueError:
                flash("Enter a valid date.", "danger")
                return redirect(url_for("attendance.class_attendance", class_id=class_id))
            for enrollment in classroom.enrollments:
                status = request.form.get(f"status_{enrollment.student_id}")
                if status not in ("present", "absent", "late"):
                    continue
                record = Attendance.query.filter_by(classroom_id=class_id, student_id=enrollment.student_id, attendance_date=day).first()
                if record:
                    record.status = status
                else:
                    db.session.add(Attendance(classroom_id=class_id, student_id=enrollment.student_id,
                                              attendance_date=day, status=status, marked_by=current_user.id))
            db.session.commit()
            flash("Attendance saved.", "success")
            return redirect(url_for("attendance.class_attendance", class_id=class_id))
        records = Attendance.query.filter_by(classroom_id=class_id).order_by(Attendance.attendance_date.desc()).all()
        return render_template("attendance/teacher.html", classroom=classroom, records=records, today=date.today().isoformat())
    records = Attendance.query.filter_by(classroom_id=class_id, student_id=current_user.id).order_by(Attendance.attendance_date.desc()).all()
    stats = current_user.attendance_stats(class_id)
    return render_template("attendance/student.html", classroom=classroom, records=records, stats=stats)
