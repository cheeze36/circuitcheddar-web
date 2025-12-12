import functools
import re
#imports things needed for use of blue prints
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
#use for auth for now( might replace later)
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from app.db import get_db

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
PASSWORD_REGEX = r'^(?=.*\d).{8,}$'
USERNAME_REGEX = r'^[a-zA-Z][a-zA-Z0-9_]{5,25}$'


bp = Blueprint('app/auth', __name__, url_prefix='/auth')

""" ROUTES FOR AUTH """
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']
        terms = request.form.get('terms')
        db = get_db()
        error = None

        if not re.match(USERNAME_REGEX, username):
            error = "username must be 6 to 25 characters, using letters and numbers."
        if not re.match(EMAIL_REGEX, email):
            error = "A valid email address is required."
        elif not password:
            error = "Password is required."
        if not re.match(PASSWORD_REGEX, password):
            error = "Password must be at least 8 characters long and include a number."
        elif password != confirm:
            error = "Passwords do not match."
        elif not terms:
            error = "You must agree to the Terms and Services."

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password, email) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), email)
                )
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for('app/auth.login'))
            except sqlite3.IntegrityError:
                error = f"User {email} is already registered."


        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form["email"].strip().lower()
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE email = ?', (email,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('app/home.index'))

        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('app/home.index'))

""" BEFORE CHECK"""
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?',(user_id,)).fetchone()

""" DECORATORS  """
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('app/auth.login'))
        return view(**kwargs)
    return wrapped_view

""" UTILITIES """
def reset_password(user_id: int, new_password: str, confirm: str):
    """
    Validate and update the password for a given user.
    Returns (True, None) on success or (False, error_message) on failure.
    """
    db = get_db()
    error = None

    if not new_password:
        return False, "Password is required."

    if not re.match(PASSWORD_REGEX, new_password):
        error = "Password must be at least 8 characters long and include a number."
    elif new_password != confirm:
        error = "Passwords do not match."

    if error:
        return False, error

    db.execute(
        "UPDATE user SET password = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id)
    )
    db.commit()
    return True, None
