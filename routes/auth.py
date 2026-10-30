from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User
from forms import RegistrationForm, LoginForm

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        role = form.role.data
        user = User(name=form.name.data.strip(), email=form.email.data.lower().strip(), role=role,
                    student_id=(form.student_id.data.strip() or None) if role == "student" else None)
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("That email or student ID is already registered.", "danger")
        else:
            login_user(user)
            flash("Your account has been created.", "success")
            return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)

@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
