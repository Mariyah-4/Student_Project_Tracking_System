from models import User, ClassRoom, ClassEnrollment, Attendance, Project
from extensions import db

def register(client, name, email, role):
    return client.post("/register", data={
        "name": name, "email": email, "role": role, "student_id": "STU-1" if role == "student" else "",
        "password": "StrongPass123", "confirm_password": "StrongPass123"
    }, follow_redirects=True)

def test_home_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Project Tracking System" in response.data

def test_registration_and_login(client, app):
    response = register(client, "Test Student", "student@example.com", "student")
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="student@example.com").first()
        assert user is not None and user.check_password("StrongPass123")
    client.post("/logout")
    response = client.post("/login", data={"email": "student@example.com", "password": "StrongPass123"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome, Test Student" in response.data

def test_late_counts_as_attended(app):
    with app.app_context():
        teacher = User(name="Teacher", email="t@example.com", role="teacher", password_hash="x")
        student = User(name="Student", email="s@example.com", role="student", password_hash="x")
        db.session.add_all([teacher, student]); db.session.flush()
        classroom = ClassRoom(name="Web", code="ABC1234", teacher_id=teacher.id)
        db.session.add(classroom); db.session.flush()
        db.session.add(ClassEnrollment(classroom_id=classroom.id, student_id=student.id))
        db.session.add(Attendance(classroom_id=classroom.id, student_id=student.id, status="late", marked_by=teacher.id))
        db.session.commit()
        stats = student.attendance_stats(classroom.id)
        assert stats == {"total": 1, "attended": 1, "percentage": 100.0}
