from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager

project_members = db.Table(
    "project_members",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(40), unique=True, nullable=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # teacher or student
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    memberships = db.relationship("ClassEnrollment", back_populates="student", cascade="all, delete-orphan", foreign_keys="ClassEnrollment.student_id")
    taught_classes = db.relationship("ClassRoom", back_populates="teacher", cascade="all, delete-orphan")
    projects_created = db.relationship("Project", back_populates="creator", foreign_keys="Project.creator_id")
    sent_messages = db.relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def classes(self):
        return [enrollment.classroom for enrollment in self.memberships]

    def attendance_stats(self, classroom_id=None):
        query = Attendance.query.filter_by(student_id=self.id)
        if classroom_id:
            query = query.filter_by(classroom_id=classroom_id)
        records = query.all()
        total = len(records)
        attended = sum(1 for r in records if r.status in ("present", "late"))
        return {"total": total, "attended": attended, "percentage": round(attended * 100 / total, 2) if total else 0.0}

class ClassRoom(db.Model):
    __tablename__ = "classrooms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    teacher = db.relationship("User", back_populates="taught_classes")
    enrollments = db.relationship("ClassEnrollment", back_populates="classroom", cascade="all, delete-orphan")
    announcements = db.relationship("Announcement", back_populates="classroom", cascade="all, delete-orphan")
    attendance_records = db.relationship("Attendance", back_populates="classroom", cascade="all, delete-orphan")

class ClassEnrollment(db.Model):
    __tablename__ = "class_enrollments"
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    classroom = db.relationship("ClassRoom", back_populates="enrollments")
    student = db.relationship("User", back_populates="memberships")
    __table_args__ = (db.UniqueConstraint("classroom_id", "student_id", name="uq_class_student"),)

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attendance_date = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(12), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    classroom = db.relationship("ClassRoom", back_populates="attendance_records")
    student = db.relationship("User", foreign_keys=[student_id])
    marker = db.relationship("User", foreign_keys=[marked_by])
    __table_args__ = (db.UniqueConstraint("classroom_id", "student_id", "attendance_date", name="uq_attendance_day"),)

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default="")
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id"), nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="in_progress", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    creator = db.relationship("User", back_populates="projects_created", foreign_keys=[creator_id])
    classroom = db.relationship("ClassRoom")
    members = db.relationship("User", secondary=project_members, backref="collaborative_projects")
    tasks = db.relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")
    files = db.relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    activities = db.relationship("ProjectActivity", back_populates="project", cascade="all, delete-orphan", order_by="ProjectActivity.created_at.desc()")
    submissions = db.relationship("Submission", back_populates="project", cascade="all, delete-orphan")

class ProjectTask(db.Model):
    __tablename__ = "project_tasks"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default="")
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), default="todo", nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    project = db.relationship("Project", back_populates="tasks")
    assignee = db.relationship("User", foreign_keys=[assigned_to])
    creator = db.relationship("User", foreign_keys=[created_by])

class ProjectFile(db.Model):
    __tablename__ = "project_files"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), unique=True, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    project = db.relationship("Project", back_populates="files")
    uploader = db.relationship("User")

class ProjectActivity(db.Model):
    __tablename__ = "project_activities"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    previous_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    project = db.relationship("Project", back_populates="activities")
    actor = db.relationship("User")

class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    note = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="submitted", nullable=False)
    marks = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, default="")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    evaluated_at = db.Column(db.DateTime, nullable=True)
    project = db.relationship("Project", back_populates="submissions")
    student = db.relationship("User")

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = db.relationship("User", foreign_keys=[recipient_id])

class Announcement(db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    classroom = db.relationship("ClassRoom", back_populates="announcements")
    teacher = db.relationship("User")

class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    user = db.relationship("User")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
