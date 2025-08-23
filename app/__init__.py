import os
import logging
import configparser
from flask import Flask, g, abort
from psycopg2 import pool

from .routes import register_routes

def create_app():
    app = Flask(__name__, static_folder='static')

    # Load config
    config = configparser.ConfigParser()
    if not config.read("test_config.ini"):
        raise RuntimeError("Configuration file 'config.ini' not found or unreadable.")

    # Secret key
    app.secret_key = config['appdata']['secret']
    if not app.secret_key:
        raise RuntimeError("SECRET_KEY is not set. Please set it in the environment.")

    # Create a DB pool
    app.config['DB_POOL'] = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=config["postgresql"]["host"],
        database=config["postgresql"]["database"],
        user=config["database_user"]["user"],
        password=config["database_user"]["password"],
    )

    # Before request: attach connection
    @app.before_request
    def before_request():
        try:
            g.db_conn = app.config['DB_POOL'].getconn()
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            abort(500)

    # Teardown request: release connection
    @app.teardown_request
    def teardown_request(exception):
        db_conn = g.pop('db_conn', None)
        if db_conn is not None:
            try:
                if exception:
                    db_conn.rollback()
                else:
                    db_conn.commit()
            except Exception as e:
                logging.error(f"Commit/Rollback error in teardown: {e}")
            finally:
                app.config['DB_POOL'].putconn(db_conn)

    # Register routes
    register_routes(app,config)

    return app