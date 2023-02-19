from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session,
)
from werkzeug.exceptions import abort

from tracker.auth import login_required
from tracker.db import get_db

import time
import datetime

bp = Blueprint('work', __name__, url_prefix='/work_entry')

@bp.route('/<username>/start', methods=('GET','POST'))
def start(username):
    if request.method == 'POST':
        project = request.form['project']
        start = datetime.datetime.now()
        db = get_db()
        error = None

        if not project:
            error = 'Project is required.'

        if not start:
            error = 'Start time error.'

        error = f'{start}'

        if error is None:
            return redirect(url_for('work.in_progress', username=username, project=project, start=start))

        flash(error)

    return render_template('work/start.html')

@bp.route('/<username>/<project>/in_progress', methods=('GET','POST'))
def in_progress(username, project, start):

    # Set session variable to notify embedded timer to start
    session['timer_active'] = True

    if request.method == 'POST':
        finish = datetime.datetime.now()
        db = get_db()
        error = None

        # Set session variable to notify embedded timer to stop
        session['timer_active'] = False

        # For duration, subtract start from finish and convert to minutes
        t_delta = finish - start
        duration = t_delta.total_minutes()

        # For task_num, get the current max in the db for this project,
        # then increment by 1
        task_num = db.execute(
            'SELECT max(task_num) FROM entry WHERE project_title = (?)', (project,)
        ).fetchone() + 1

        if not finish:
            error = 'Finish time error.'

        if not duration:
            error = 'Duration error.'

        if error is None:
            return redirect(url_for('work.complete',username=username,project=project,start=start,finish=finish,duration=duration,task_num=task_num))

        flash(error)

    return render_template('work/in_progress.html')

@bp.route('/<username>/<project>/complete', methods=('GET','POST'))
def complete(username,project,start,finish,duration,task_num):
    if request.method == 'POST':
        complexity = request.form['complexity']
        project_complete = request.form['project_complete']
        summary = request.form['summary']
        db = get_db()
        error = None


        if complexity is None:
            # default complexity to 3
            complexity = 3

        if project_complete is None:
            # default project_complete to false
            project_complete = False

        if summary is None:
            error = 'Summary is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO entry (author_id,start,finish,duration,project_title,complexity,project_complete,summary,task_num) VALUES (?,?,?,?,?,?,?,?,?)",
                    (user_id,start,finish,duration,project,complexity,project_complete,summary,task_num),
                )
                db.commit()
            except db.IntegrityError:
                error = 'Database error.'
            return redirect(url_for('dashboard.user_dash', username=username))

        flash(error)

    return render_template('work/complete.html')

# Content to be embedded into display
@bp.route('/content')
def content():
    def timer():
        i = 0
        while session.get('timer_active') is True:
            yield str(i)
            time.sleep(60)
            i = i+1
        return Response(timer(10), mimetype='text/html')

# load_logged_in_user function
# Runs before the the view functions to
# check if a user id is stored in the session.
# If so, gets that user's data from the database
# and stores it in g.user.
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    username = session.get('username')
    session['timer_active'] = False

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
