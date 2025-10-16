from pydoc import describe

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

