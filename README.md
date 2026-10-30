# Student Project Tracking System (SPTS)

A Flask application for teacher/student accounts, class management, attendance, project collaboration, activity history, submissions, evaluation, messaging and announcements. No AI features are included.

## Features currently implemented

- Student and teacher registration/login with password hashing and role-based route protection.
- Teacher-created classes, enrollment codes, teacher enrollment by student email and announcements.
- Teacher attendance entry for Present, Absent and Late; students see their own records. Late counts as attended.
- Student projects, same-class collaborator invitations, task creation/status updates and project file uploads.
- Append-only project activity events for project creation, invitations, task changes, uploads, submissions and evaluation.
- Project submissions, teacher downloads, approval/revision status, marks and feedback.
- Direct teacher/student messages restricted to people sharing a class, plus notifications.
- SQLite local development and PostgreSQL production configuration.
- SQLAlchemy models, Flask-Migrate, CSRF protection, basic tests and GitHub Actions.

## Important scope notes

This is a functional first version, not a security audit or a fully hardened institutional product. Registration currently allows a user to choose Teacher or Student; for a real institution, teacher accounts should be provisioned or approved by an administrator. Uploaded files are stored on the application filesystem; Render's ordinary service filesystem is ephemeral, so production file persistence needs a persistent disk or object storage. Messaging is a simple inbox, not real-time chat. Attendance bulk upload from CSV, admin moderation, password reset, email delivery, richer reporting, and audit-log tamper-evidence are not included in this release.

Activity records have no edit/delete interface and are written by application services. A database administrator with direct database access can still alter rows; stronger tamper evidence requires database permissions and/or external immutable audit storage.

## 1. Run locally (beginner-friendly)

Install Python 3.11 or 3.12. Open a terminal in this project folder.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a long random `SECRET_KEY`. The example uses SQLite, so no database server is needed for the first local run.

Create the database tables:

```powershell
flask --app app db init
flask --app app db migrate -m "initial schema"
flask --app app db upgrade
```

If Flask-Migrate says the migrations directory already exists, do not run `db init` again. Run `flask --app app db migrate -m "schema update"` and then `flask --app app db upgrade`.

Start the server:

```powershell
flask --app app run --debug
```

Open `http://127.0.0.1:5000`.

Alternative fresh-database shortcut: `flask --app app init-db`. Use this only when starting with a brand-new empty database; for ongoing schema changes use migrations.

## 2. PostgreSQL setup

Create a PostgreSQL database using a trusted PostgreSQL provider. For local PostgreSQL, create a database and user, then set `DATABASE_URL` in `.env`:

```text
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/spts
```

Keep credentials private. Never commit `.env`. Run:

```powershell
flask --app app db upgrade
```

For Render, create a PostgreSQL database in the Render dashboard, copy its **Internal Database URL**, and set it as the web service environment variable `DATABASE_URL`. Render may supply a `postgres://` URL; the app normalizes it to the psycopg driver.

## 3. GitHub upload using the website

1. Open the new repository: https://github.com/Mariyah-4/Student-Project-Tracking-System
2. Choose **Add file → Upload files**.
3. Extract this ZIP on your computer first.
4. Open the extracted project folder and select its contents (including `.github`, `routes`, `services`, `templates`, `static`, and `tests`) and drag them into GitHub's upload area.
5. Wait for uploads to finish, enter a commit message such as `Add SPTS Flask application`, and choose **Commit changes**.
6. Confirm that `app.py`, `models.py`, `routes/`, `templates/`, and `.github/workflows/test.yml` appear in the repository.
7. Do not upload `.env`; only `.env.example` belongs in GitHub.

GitHub's browser upload has practical limits. If selecting the entire folder is awkward, upload the contents in smaller batches, preserving the folder paths. GitHub creates folders from the uploaded file paths; an empty folder is not stored.

## 4. Render deployment

1. Push/commit all project files to the new repository.
2. In Render, choose **New → PostgreSQL** and create a database in the same region as the web service.
3. Choose **New → Web Service**, connect only `Mariyah-4/Student-Project-Tracking-System`.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Add environment variables:
   - `SECRET_KEY`: a long random secret
   - `FLASK_CONFIG`: `production`
   - `DATABASE_URL`: the PostgreSQL **Internal Database URL**
7. Deploy. In the Render Shell (or a one-off command facility if available), run `flask --app app db upgrade`.
8. Check the deployment logs and open the service URL. Register one teacher and one student for a basic workflow test.

### File storage warning

Render's normal filesystem is ephemeral. Files uploaded by students can disappear after a deploy/restart unless you configure a persistent disk and set `UPLOAD_FOLDER` to its mount path, or replace local file storage with object storage. Do not treat local uploads as durable production storage without that configuration.

## 5. First manual test plan

- Register a teacher and create a class.
- Register a student and join using the class code.
- As teacher, mark Present, Absent and Late for a date; confirm student attendance percentage.
- As student, create a project, invite another student from the same class, add a task, update task status and upload a file.
- Submit a project file; as teacher, download it, request revision or approve it, enter marks and feedback.
- Confirm student sees the evaluation.
- Send a teacher/student message and post an announcement; confirm notifications appear.
- Open the project activity history and confirm events are visible.

## 6. Automated tests

```powershell
pytest -q
```

GitHub Actions runs the test suite on pushes and pull requests to `main`.

## 7. Project structure

```text
Student-Project-Tracking-System/
├── app.py
├── config.py
├── extensions.py
├── forms.py
├── models.py
├── requirements.txt
├── README.md
├── .env.example
├── routes/
├── services/
├── templates/
├── static/
├── tests/
├── migrations/       # generated by `flask db init`
├── uploads/
└── .github/workflows/test.yml
```

## Security reminders

- Set a strong production `SECRET_KEY`.
- Never commit `.env` or database credentials.
- Use HTTPS in production.
- Back up PostgreSQL.
- Add teacher approval/admin controls before real institutional use.
- Set a persistent upload location before accepting important student files.
- Consider malware scanning and stricter file-size/type policies for public deployments.
