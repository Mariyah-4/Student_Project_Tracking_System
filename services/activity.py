from models import ProjectActivity, Notification
from extensions import db

def log_activity(project, actor, action, description, previous_value=None, new_value=None):
    """Append-only project audit event. No edit/delete route is exposed."""
    event = ProjectActivity(
        project=project, actor=actor, action=action, description=description,
        previous_value=previous_value, new_value=new_value
    )
    db.session.add(event)
    return event

def notify(user, title, body, url=""):
    if user:
        db.session.add(Notification(user_id=user.id, title=title, body=body, url=url))
