import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pwp_api.backend import RedisBackend, RabbitBackend
from werkzeug.middleware.proxy_fix import ProxyFix


db = SQLAlchemy()
redis = RedisBackend(
    uri_string=os.environ["PWP_REDIS_URI"],
    passwd=os.environ["PWP_REDIS_PASSWD"]
)
rabbit = RabbitBackend(
    broker=os.environ["PWP_RABBIT_URI"],
    user=os.environ["PWP_RABBIT_USER"],
    passwd=os.environ["PWP_RABBIT_PASSWD"]
)

# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    """
    Creates the Flask app. Configuration can be pulled from three places:
    - dictionary as function argument, for tests
    - a configuration file "config.py" from the local instance folder root
    - the default development configuration hardcoded into this function

    Initiatializiation for the database and cache are done within this
    function. Likewise all CLI commands, converters, and blueprints are
    registered here before the Flask app object is returned.
    """

    app = Flask(__name__, instance_relative_config=True)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE="SimpleCache"
    )

    # Configuration overrides from config file and using proxyfix when not testing
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_prefix=1)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    # Register CLI commands, converters, and blueprint
    # Imports are placed here to avoid circular import issues
    from . import api
    from . import cli
    from .utils import GroupConverter
    import pwp_api.views as views
    app.cli.add_command(cli.init_db_command)
    app.cli.add_command(cli.generate_test_data)
    app.cli.add_command(cli.generate_master_key)
    app.cli.add_command(cli.clear_groups)
    app.url_map.converters["group"] = GroupConverter
    app.register_blueprint(api.api_bp)

    app.add_url_rule("/link-relations/", "namespace", views.link_relations)
    app.add_url_rule("/profiles/", "profiles", views.profiles)

    return app
