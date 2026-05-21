import os
from pathlib import Path

from flask import Flask

from .db import close_db, init_app
from .routes import register_routes


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    db_engine = os.environ.get("RMS_DB_ENGINE", "sqlite").lower()

    if db_engine == "mysql":
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY", "rms-secret-key"),
            DB_ENGINE="mysql",
            MYSQL={
                "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
                "port": int(os.environ.get("MYSQL_PORT", "3306")),
                "user": os.environ.get("MYSQL_USER", "root"),
                "password": os.environ.get("MYSQL_PASSWORD", ""),
                "database": os.environ.get("MYSQL_DATABASE", "restaurantdb"),
            },
            ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "admin"),
            ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "admin123"),
        )
    else:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY", "rms-secret-key"),
            DATABASE=str(Path(app.instance_path) / "restaurant_rms.db"),
            DB_ENGINE="sqlite",
            ADMIN_USERNAME=os.environ.get("ADMIN_USERNAME", "Rohit"),
            ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "Rohit123"),
        )

    init_app(app)
    register_routes(app)
    app.teardown_appcontext(close_db)

    return app
