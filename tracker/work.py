from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session, Response
)
from werkzeug.exceptions import abort

from tracker.auth import login_required
from tracker.db import get_db

import time
from datetime import datetime, date

bp = Blueprint('work', __name__, url_prefix='/work_entry')

# Preconditions: User logged in
# Postconditions: html rendered, redirect to 'in_progress' page upon button press
# Invariants:
@bp.route('/<username>/start', methods=('GET','POST'))
@login_required
def start(username):
    if request.method == 'POST':
        user_id = session.get('user_id')
        project = request.form['project']
        start = datetime.now().time()
        db = get_db()
        error = None

        if not project:
            error = 'Project is required.'

        try:
            task = db.execute(
                'SELECT max(task_num) FROM entry WHERE (author_id,project_title) = (?,?)', (user_id,project,)
            ).fetchone()
        except db.IntegrityError:
            error = 'Database error.'

        if not task['max(task_num)']:
            task_num = 1
        else:
            task_num = task['max(task_num)'] + 1

        if not task_num:
            error = 'Task number error.'

        if not start:
            error = 'Start time error.'

        if error is None:
            return redirect(url_for('work.in_progress', username=username, project=project, task_num=task_num, start=start))

        flash(error)

    return render_template('work/start.html')

@bp.route('/<username>/<project>/<task_num>/in_progress/<start>', methods=('GET','POST'))
@login_required
def in_progress(username, project, task_num, start):

    flash(start)

    if request.method == 'POST':
        user_id = session.get('user_id')
        finish = datetime.now().time()
        error = None
        start_time = datetime.strptime(start, '%H:%M:%S.%f').time()

        time_difference = datetime.combine(date.today(), finish) - datetime.combine(date.today(), start_time)
        duration = round(time_difference.total_seconds()/60, 2)

        if not finish:
            error = 'Finish time error.'

        if not duration:
            error = 'Duration error.'

        if error is None:
            return redirect(url_for('work.complete',username=username,project=project,task_num=task_num,start=start,finish=finish,duration=duration))

        flash(error)

    return render_template('work/in_progress.html')

@bp.route('/<username>/<project>/<task_num>/<start>/complete/<duration>/<finish>', methods=('GET','POST'))
@login_required
def complete(username,project,task_num, start, finish, duration):

    if request.method == 'POST':
        user_id = session.get('user_id')
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
                    "UPDATE entry SET (complexity,project_complete,summary) = (?,?,?) WHERE (author_id,project_title,task_num) = (?,?,?)",
                    (complexity,project_complete,summary),
                    (user_id,project,task_num),
                )
                db.commit()
            except db.IntegrityError:
                error = 'Database error.'
            try:
                db.execute(
                    "INSERT INTO entry (author_id,project_title,task_num,start,finish,duration,complexity,project_complete,summary) VALUES (?,?,?,?,?,?,?,?,?)",
                    (user_id,project,task_num,start,finish,duration,complexity,project_complete,summary),
                )
                db.commit()
            except db.IntegrityError:
                error = 'Database error.'
            return redirect(url_for('dashboard.user_dash', username=username))

        flash(error)

    return render_template('work/complete.html', project=project, task_num=task_num, duration=duration)


# load_logged_in_user function
# Runs before the the view functions to
# check if a user id is stored in the session.
# If so, gets that user's data from the database
# and stores it in g.user.
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    username = session.get('username')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
