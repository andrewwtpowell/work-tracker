from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session,
)
from werkzeug.exceptions import abort

from tracker.auth import login_required
from tracker.db import get_db

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/<username>')
def user_dash(username):
    return render_template('dashboard/dash.html')

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
