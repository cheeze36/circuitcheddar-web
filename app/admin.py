import functools
import re
#imports things needed for use of blue prints
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
#use for auth for now( might replace later)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db
import sqlite3

from app.auth import login_required
from app.db import get_db

bp = Blueprint('app/admin', __name__, url_prefix='/admin')

@bp.route('/admin_portal', methods=('GET', 'POST'))
@login_required
def admin_portal():
    if g.user['role'] != 'ADMIN':
        abort(403)
    else:
        db = get_db()
        users = db.execute(
            'SELECT id, username, email, role'
            ' FROM user'
            ' ORDER BY username DESC'
        ).fetchall()
        return render_template('admin/dashboard.html', users=users)

