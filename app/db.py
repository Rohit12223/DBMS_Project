import sqlite3
from pathlib import Path

from flask import current_app, g


class MySQLConnectionWrapper:
    """Expose a sqlite-like API (execute/commit/rollback/close) for PyMySQL."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_db():
    if "db" not in g:
        engine = current_app.config.get("DB_ENGINE", "sqlite").lower()
        if engine == "mysql":
            import pymysql
            from pymysql.cursors import DictCursor

            cfg = current_app.config["MYSQL"]
            server_conn = pymysql.connect(
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                port=int(cfg.get("port", 3306)),
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=True,
            )
            with server_conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            server_conn.close()

            conn = pymysql.connect(
                host=cfg["host"],
                user=cfg["user"],
                password=cfg["password"],
                database=cfg["database"],
                port=int(cfg.get("port", 3306)),
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=False,
            )
            g.db = MySQLConnectionWrapper(conn)
        else:
            conn = sqlite3.connect(
                current_app.config["DATABASE"],
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db = conn
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _iter_mysql_statements(sql_text):
    buf = []
    for raw_line in sql_text.splitlines():
        line = raw_line.strip()
        if line.startswith("--"):
            continue
        buf.append(raw_line)
        if line.endswith(";"):
            stmt = "\n".join(buf).strip()
            buf = []
            if stmt:
                yield stmt
    tail = "\n".join(buf).strip()
    if tail:
        yield tail


def _mysql_has_customers_table(db):
    row = db.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name = 'Customers'
        """
    ).fetchone()
    return bool(row) and int(row["cnt"]) > 0


def init_db():
    db = get_db()
    engine = current_app.config.get("DB_ENGINE", "sqlite").lower()
    if engine == "mysql":
        schema_path = Path(current_app.root_path).parent / "schema_mysql.sql"
        text = schema_path.read_text(encoding="utf-8")
        for statement in _iter_mysql_statements(text):
            db.execute(statement)
        db.commit()
    else:
        schema_path = Path(current_app.root_path).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as schema_file:
            db.executescript(schema_file.read())
        db.commit()


def seed_admin_employee():
    db = get_db()
    existing = db.execute(
        "SELECT employee_id FROM Employees WHERE role = ? LIMIT 1",
        ("Admin",),
    ).fetchone()
    if existing is None:
        db.execute(
            """
            INSERT INTO Employees (name, role, shift)
            VALUES (?, ?, ?)
            """,
            ("System Admin", "Admin", "Full Day"),
        )
        db.commit()


def init_app(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    @app.before_request
    def ensure_database():
        engine = current_app.config.get("DB_ENGINE", "sqlite").lower()
        if engine == "mysql":
            db = get_db()
            if not _mysql_has_customers_table(db):
                init_db()
                seed_admin_employee()
        else:
            db_path = Path(current_app.config["DATABASE"])
            if not db_path.exists():
                init_db()
                seed_admin_employee()
