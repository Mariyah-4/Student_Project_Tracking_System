import sys
from pathlib import Path

import pytest

# Add the project root directory to Python's import path.

PROJECT_ROOT = Path(file).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from extensions import db

@pytest.fixture()
def app():
"""Create and configure a new application instance for each test."""
app = create_app("development")

app.config.update(
    TESTING=True,
    WTF_CSRF_ENABLED=False,
    SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

with app.app_context():
    db.create_all()
    yield app
    db.session.remove()
    db.drop_all()

@pytest.fixture()
def client(app):
"""Provide a test client for making requests to the application."""
return app.test_client()

@pytest.fixture()
def runner(app):
"""Provide a CLI test runner."""
return app.test_cli_runner()
