# Creates a Blueprint named 'auth'. Like the Application
# object, the Blueprint needs to know where it is defined,
# so __name__ is passed as the second argument. The
# url_prefix will be prepended to all the URLs associated
# with the Blueprint

import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from tracker.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# register view function
# Checks values entered and inserts data
# into database if entries are valid
@bp.route('/register', methods=('GET','POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

# login view function
# Compares values entered to existing database
# Redirects to index page if valid login provided
# otherwise gives error message
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('dashboard.user_dash', username=username))

        flash(error)

    return render_template('auth/login.html')

# load_logged_in_user function
# Runs before the the view functions to
# check if a user id is stored in the session.
# If so, gets that user's data from the database
# and stores it in g.user.
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.username = session.get('username')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

# logout function
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

# login required decorator function
# Wraps the views it is applied to.
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
