from pydoc import describe
import re

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

import sqlite3
from app.auth import login_required, USERNAME_REGEX, reset_password
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
        new_password = request.form.get('password')
        confirm = request.form.get('confirm')

        # Validate username
        if not re.match(USERNAME_REGEX, new_username):
            error = "Username must be 6 to 25 characters, using letters and numbers."

        # Update password via utility if provided
        if new_password:
            ok, perr = reset_password(user_id, new_password, confirm or "")
            if not ok and not error:
                error = perr

        if error is None:
            try:
                db.execute(
                    "UPDATE user SET username = ? WHERE id = ?",
                    (new_username, user_id)
                )
                db.commit()
                flash("Profile updated successfully.", "success")
                # Refresh g.user
                g.user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
            except sqlite3.IntegrityError:
                error = "Username already taken."

        if error:
            flash(error)

    # Data for profile sections
    my_posts = db.execute(
        'SELECT p.id, p.title, p.description, p.created, p.type '
        'FROM post p WHERE p.author_id = ? '
        'ORDER BY p.created DESC LIMIT 15',
        (user_id,)
    ).fetchall()

    liked_posts = db.execute(
        'SELECT DISTINCT p.id, p.title, p.description, p.created, p.type '
        'FROM like l JOIN post p ON l.post_id = p.id '
        'WHERE l.user_id = ? AND l.post_id IS NOT NULL '
        'ORDER BY p.created DESC LIMIT 15',
        (user_id,)
    ).fetchall()

    commented_posts = db.execute(
        'SELECT DISTINCT p.id, p.title, p.description, p.created, p.type '
        'FROM post_comments c JOIN post p ON c.post_id = p.id '
        'WHERE c.author_id = ? '
        'ORDER BY p.created DESC LIMIT 15',
        (user_id,)
    ).fetchall()

    return render_template('home/profile.html', user=g.user, my_posts=my_posts, liked_posts=liked_posts, commented_posts=commented_posts)

@bp.route('/profile/my-posts', methods=['GET'])
@login_required
def profile_my_posts():
    db = get_db()
    user_id = g.user['id']
    posts = db.execute(
        'SELECT p.id, p.title, p.description, p.created, p.type, p.author_id, u.username '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'WHERE p.author_id = ? '
        'ORDER BY p.created DESC',
        (user_id,)
    ).fetchall()
    return render_template('home/profile_my_posts.html', posts=posts)

@bp.route('/profile/liked-posts', methods=['GET'])
@login_required
def profile_liked_posts():
    db = get_db()
    user_id = g.user['id']
    posts = db.execute(
        'SELECT DISTINCT p.id, p.title, p.description, p.created, p.type, p.author_id, u.username '
        'FROM like l JOIN post p ON l.post_id = p.id '
        'JOIN user u ON p.author_id = u.id '
        'WHERE l.user_id = ? AND l.post_id IS NOT NULL '
        'ORDER BY p.created DESC',
        (user_id,)
    ).fetchall()
    return render_template('home/profile_liked_posts.html', posts=posts)

@bp.route('/profile/commented-posts', methods=['GET'])
@login_required
def profile_commented_posts():
    db = get_db()
    user_id = g.user['id']
    posts = db.execute(
        'SELECT DISTINCT p.id, p.title, p.description, p.created, p.type, p.author_id, u.username '
        'FROM post_comments c JOIN post p ON c.post_id = p.id '
        'JOIN user u ON p.author_id = u.id '
        'WHERE c.author_id = ? '
        'ORDER BY p.created DESC',
        (user_id,)
    ).fetchall()
    return render_template('home/profile_commented_posts.html', posts=posts)

