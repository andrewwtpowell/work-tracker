import os

from flask import Flask

# Application Factory
def create_app(test_config=None):

    # Create and configure the Application
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'tracker.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize the database
    from . import db
    db.init_app(app)

    # Register the authentication blueprint
    from . import auth
    app.register_blueprint(auth.bp)

    # Register the dashboard blueprint
    from . import dashboard
    app.register_blueprint(dashboard.bp)

    # Register the work blueprint
    from . import work
    app.register_blueprint(work.bp)

    return app
