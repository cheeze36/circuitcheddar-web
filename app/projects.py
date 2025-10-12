from pydoc import describe

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint('app/projects', __name__, url_prefix='/projects')

@bp.route('/browse', methods=('GET', 'POST'))
def browse():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, description, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('projects/browse_all_projects.html', posts=posts)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        body = request.form['quill-html']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, description, body, author_id)'
                ' VALUES (?, ?, ?, ?)',
                (title,description, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('app/home.index'))

    return render_template('projects/create.html')

def get_post_unauth(id):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()
    return post

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('app/projects.index'))

    return render_template('projects/update.html', post=post)

def get_comments(id):
     comments = get_db().execute(
         'SELECT pc.id AS id, '
         'pc.body AS body, '
         'pc.created AS created, '
         'u.username AS username, '
         'pc.author_id AS author_id '
         'FROM project_comments pc JOIN user u ON pc.author_id = u.id '
         'WHERE pc.post_id = ?',
        (id,)).fetchall()
     return comments

def add_comment(id, author, body):
    db = get_db()
    db.execute("INSERT INTO project_comments (post_id, author_id, body) VALUES (?, ?, ?)",
        (id, author, body,))
    db.commit()

def get_comment_like_count(comment_id):
    try:
        has_liked = get_db().execute('SELECT 1 FROM like WHERE user_id = ? AND comment_id = ?',(g.user['id'],comment_id)).fetchone()[0]
        text = " Unlike"
    except:
        has_liked = 0
        text = "Like"
    return [get_db().execute("SELECT COUNT(*) FROM like WHERE comment_id = ?", (comment_id,)).fetchone()[0],text]

@bp.route("/processcomments", methods=('POST',))
@login_required
def processcomments():
    data = request.get_json()
    comment = data.get('comment', "").strip()
    post_id = data.get('id', 0)

    if comment:
        add_comment(post_id, g.user['id'], comment)

    comments = get_comments(post_id)
    a = jsonify(html=render_template("projects/processcomments.html", comments=comments,
                                     get_comment_like_count = get_comment_like_count)) # Fetch after insertion
    print(a)
    return a



@bp.route('/<int:id>/project',methods=('GET',))
def project(id):
    post = get_post_unauth(id)
    comments = get_comments(id)
    likes = get_db().execute("SELECT COUNT(*) FROM like WHERE post_id = ?", (id,)).fetchone()[0]
    liked_btn = ""
    try:
        has_liked = get_db().execute('SELECT 1 FROM like WHERE user_id = ? AND post_id = ?',(g.user['id'],post_id)).fetchone()[0]
    except:
        has_liked = 0
    if has_liked < 1:
        liked_btn = "Like"

    else:
        liked_btn = "Unlike"
    return render_template('projects/project.html', post=post, comments=comments,
                           likes = likes, liked_btn = liked_btn,
                           get_comment_like_count = get_comment_like_count)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('app/projects.index'))

@bp.route('/commentdelete/<int:id>', methods=['POST'])
@login_required
def commentdelete(id):
    db = get_db()
    db.execute('DELETE FROM project_comments WHERE id = ?', (id,))
    db.commit()
    return jsonify(success=True), 200

@bp.route('/likepost',methods=['POST'])
@login_required
def likepost():
    data = request.get_json()
    post_id = data.get('id', 0)
    try:
        has_liked = get_db().execute('SELECT 1 FROM like WHERE user_id = ? AND post_id = ?',(g.user['id'],post_id)).fetchone()[0]
    except:
        has_liked = 0
    if has_liked < 1:
        get_db().execute("INSERT INTO like (user_id, post_id) VALUES (?, ?)",
                   (g.user['id'], post_id))
        get_db().commit()
        responce = jsonify(
            number=get_db().execute("SELECT COUNT(*) FROM like WHERE post_id = ?", (post_id,)).fetchone()[0],
            btn_text="Unlike")

    else:
        get_db().execute('DELETE FROM like WHERE user_id = ? AND post_id = ?',(g.user['id'],post_id))
        get_db().commit()
        responce = jsonify(number = get_db().execute("SELECT COUNT(*) FROM like WHERE post_id = ?", (post_id,)).fetchone()[0], btn_text = "Like")
    print(responce)
    return responce


@bp.route('/likecomment',methods=['POST'])
@login_required
def likecomment():
    print("test")
    data = request.get_json()
    comment_id = data.get('comment_id', 0)
    try:
        has_liked = get_db().execute('SELECT 1 FROM like WHERE user_id = ? AND comment_id = ?',(g.user['id'],comment_id)).fetchone()[0]
    except:
        has_liked = 0
    if has_liked < 1:
        get_db().execute("INSERT INTO like (user_id, comment_id) VALUES (?, ?)",
                   (g.user['id'], comment_id))
        get_db().commit()
        responce = jsonify(
            number=get_db().execute("SELECT COUNT(*) FROM like WHERE comment_id = ?", (comment_id,)).fetchone()[0],
            btn_text="Unlike")

    else:
        get_db().execute('DELETE FROM like WHERE user_id = ? AND comment_id = ?',(g.user['id'],comment_id))
        get_db().commit()
        responce = jsonify(number = get_db().execute("SELECT COUNT(*) FROM like WHERE comment_id = ?", (comment_id,)).fetchone()[0], btn_text = "Like")
    print(responce)
    return responce, 200