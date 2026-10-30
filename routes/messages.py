from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import User, Message, ClassEnrollment, ClassRoom, Project
from services.activity import notify

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")

def permitted(recipient):
    if current_user.role == "teacher":
        return ClassEnrollment.query.join(ClassRoom).filter(ClassRoom.teacher_id == current_user.id, ClassEnrollment.student_id == recipient.id).first() is not None
    return ClassEnrollment.query.join(ClassRoom).filter(ClassEnrollment.student_id == current_user.id, ClassRoom.teacher_id == recipient.id).first() is not None

@messages_bp.get("/")
@login_required
def inbox():
    messages = Message.query.filter((Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)).order_by(Message.created_at.desc()).all()
    contacts = User.query.filter(User.id != current_user.id, User.role != current_user.role).all()
    if current_user.role == "teacher":
        contacts = [u for u in contacts if permitted(u)]
    else:
        contacts = [u for u in contacts if permitted(u)]
    return render_template("messages/inbox.html", messages=messages, contacts=contacts)

@messages_bp.post("/send")
@login_required
def send():
    try:
        recipient_id = int(request.form.get("recipient_id", ""))
    except ValueError:
        abort(400)
    recipient = User.query.get_or_404(recipient_id)
    body = request.form.get("body", "").strip()
    if not body or len(body) > 5000 or not permitted(recipient):
        abort(400)
    db.session.add(Message(sender_id=current_user.id, recipient_id=recipient.id, body=body))
    notify(recipient, "New message", f"Message from {current_user.name}.", url_for("messages.inbox"))
    db.session.commit()
    flash("Message sent.", "success")
    return redirect(url_for("messages.inbox"))

@messages_bp.post("/<int:message_id>/read")
@login_required
def mark_read(message_id):
    message = Message.query.get_or_404(message_id)
    if message.recipient_id != current_user.id:
        abort(403)
    message.read_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("messages.inbox"))
