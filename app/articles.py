from pydoc import describe

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db

bp = Blueprint('app/articles', __name__, url_prefix='/articles')

@bp.route('/browse', methods=('GET', 'POST'))
def browse():
    db = get_db()
    tag_filter = request.args.get('tag', '').strip().lower()

    # Fetch all tags for dropdown
    all_tags = db.execute('SELECT name FROM tag ORDER BY name ASC').fetchall()
    try:
        user_role = db.execute('SELECT role FROM user WHERE id = ?', (g.user['id'],)).fetchone()[0]
    except TypeError:
        user_role = "NONE"


    query = '''
        SELECT DISTINCT p.id, p.title, p.description, p.body, p.created, p.author_id, u.username
        FROM post p
        JOIN user u ON p.author_id = u.id
        LEFT JOIN post_tag pt ON p.id = pt.post_id
        LEFT JOIN tag t ON pt.tag_id = t.id
    '''
    conditions = []
    params = []
    conditions.append('p.type = "ARTICLE"')
    if tag_filter:
        conditions.append('t.name = ?')
        params.append(tag_filter)

    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)

    query += ' ORDER BY p.created DESC'

    posts = db.execute(query, params).fetchall()
    return render_template('articles/browse_all_articles.html', posts=posts, all_tags=all_tags, selected_tag=tag_filter,user_role=user_role)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        raw_tags = request.form['tags']
        tag_names = [t.strip().lower() for t in raw_tags.split(',') if t.strip()]
        body = request.form['quill-html']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO post (title, description, body, author_id, type)'
                ' VALUES (?, ?, ?, ?, ?)',
                (title,description, body, g.user['id'], "ARTICLE")
            )
            post_id = cursor.lastrowid
            for name in tag_names:
                tag = cursor.execute('SELECT id FROM tag WHERE name = ?', (name,)).fetchone()
                if not tag:
                    cursor.execute('INSERT INTO tag (name) VALUES (?)', (name,))
                    tag_id = cursor.lastrowid
                else:
                    tag_id = tag['id']
                cursor.execute('INSERT INTO post_tag (post_id, tag_id) VALUES (?, ?)', (post_id, tag_id))
                db.commit()
            return redirect(url_for('app/home.index'))

    return render_template('articles/create.html')

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
        'SELECT p.id, title, p.description, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

def get_post_tags(post_id: int) -> list[str]:
    rows = get_db().execute(
        'SELECT t.name '
        'FROM tag t '
        'JOIN post_tag pt ON pt.tag_id = t.id '
        'WHERE pt.post_id = ? '
        'ORDER BY t.name ASC',
        (post_id,),
    ).fetchall()
    return [r['name'] for r in rows]


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        raw_tags = request.form.get('tags', '')
        tag_names = [t.strip().lower() for t in raw_tags.split(',') if t.strip()]
        body = request.form['quill-html']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.cursor()

            cursor.execute(
                'UPDATE post SET title = ?,description = ?, body = ?'
                ' WHERE id = ?',
                (title, description, body, id)
            )

            cursor.execute('DELETE FROM post_tag WHERE post_id = ?', (id,))
            for name in tag_names:
                tag = cursor.execute('SELECT id FROM tag WHERE name = ?', (name,)).fetchone()
                if not tag:
                    cursor.execute('INSERT INTO tag (name) VALUES (?)', (name,))
                    tag_id = cursor.lastrowid
                else:
                    tag_id = tag['id']
                cursor.execute(
                    'INSERT INTO post_tag (post_id, tag_id) VALUES (?, ?)',
                    (id, tag_id)
                )

            db.commit()
            return redirect(url_for('app/home.index'))

    existing_tags = ", ".join(get_post_tags(id))
    return render_template('articles/update.html', post=post, existing_tags=existing_tags)

def get_comments(id):
     comments = get_db().execute(
         'SELECT pc.id AS id, '
         'pc.body AS body, '
         'pc.created AS created, '
         'u.username AS username, '
         'pc.author_id AS author_id '
         'FROM post_comments pc JOIN user u ON pc.author_id = u.id '
         'WHERE pc.post_id = ?',
        (id,)).fetchall()
     return comments

def add_comment(id, author, body):
    db = get_db()
    db.execute("INSERT INTO post_comments (post_id, author_id, body) VALUES (?, ?, ?)",
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
    a = jsonify(html=render_template("articles/processcomments.html", comments=comments,
                                     get_comment_like_count = get_comment_like_count)) # Fetch after insertion
    print(a)
    return a



@bp.route('/<int:id>/article',methods=('GET',))
def article(id):
    post = get_post_unauth(id)
    comments = get_comments(id)
    likes = get_db().execute("SELECT COUNT(*) FROM like WHERE post_id = ?", (id,)).fetchone()[0]
    liked_btn = ""
    try:
        has_liked = get_db().execute('SELECT 1 FROM like WHERE user_id = ? AND post_id = ?',(g.user['id'],id)).fetchone()[0]
    except:
        has_liked = 0
    if has_liked < 1:
        liked_btn = "Like"

    else:
        liked_btn = "Unlike"
    return render_template('articles/article.html', post=post, comments=comments,
                           likes = likes, liked_btn = liked_btn,
                           get_comment_like_count = get_comment_like_count)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('app/home.index'))

@bp.route('/commentdelete/<int:id>', methods=['POST'])
@login_required
def commentdelete(id):
    db = get_db()
    db.execute('DELETE FROM post_comments WHERE id = ?', (id,))
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
        response = jsonify(
            number=get_db().execute("SELECT COUNT(*) FROM like WHERE post_id = ?", (post_id,)).fetchone()[0],
            btn_text="Unlike")

    else:
        get_db().execute('DELETE FROM like WHERE user_id = ? AND post_id = ?',(g.user['id'],post_id))
        get_db().commit()
        response = jsonify(number = get_db().execute("SELECT COUNT(*) FROM like WHERE post_id = ?", (post_id,)).fetchone()[0], btn_text = "Like")
    print(response)
    return response


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
        response = jsonify(
            number=get_db().execute("SELECT COUNT(*) FROM like WHERE comment_id = ?", (comment_id,)).fetchone()[0],
            btn_text="Unlike")

    else:
        get_db().execute('DELETE FROM like WHERE user_id = ? AND comment_id = ?',(g.user['id'],comment_id))
        get_db().commit()
        response = jsonify(number = get_db().execute("SELECT COUNT(*) FROM like WHERE comment_id = ?", (comment_id,)).fetchone()[0], btn_text = "Like")
    print(response)
    return response, 200