from pydoc import describe
import re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint('app/home', __name__,)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, description, body, type, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('home/index.html', posts=posts)
@bp.route('/about')
def about():
    return render_template('home/about.html')
@bp.route('/contact')
def contact():
    return render_template('home/contact.html')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    user_id = g.user['id']
    error = None

    if request.method == 'POST':
        new_username = request.form['username'].strip().lower()
        new_password = request.form['password']
        confirm = request.form['confirm']

        # Validate username
        if not re.match(USERNAME_REGEX, new_username):
            error = "Username must be 6 to 25 characters, using letters and numbers."

        # Validate password only if provided
        if new_password:
            if not re.match(PASSWORD_REGEX, new_password):
                error = "Password must be at least 8 characters long and include a number."
            elif new_password != confirm:
                error = "Passwords do not match."

        if error is None:
            try:
                db.execute(
                    "UPDATE user SET username = ? WHERE id = ?",
                    (new_username, user_id)
                )
                if new_password:
                    db.execute(
                        "UPDATE user SET password = ? WHERE id = ?",
                        (generate_password_hash(new_password), user_id)
                    )
                db.commit()
                flash("Profile updated successfully.", "success")
                # Refresh g.user
                g.user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
            except sqlite3.IntegrityError:
                error = "Username already taken."

        if error:
            flash(error)

    return render_template('home/profile.html', user=g.user)

