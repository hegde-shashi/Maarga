# Apply SQLite3 monkey-patch for ChromaDB compatibility on older Linux environments (like Azure App Services)
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

from flask import Flask
from backend.database.db import db
from backend.config import DB_USER, DB_HOST, DB_PASSWORD, DB_NAME, JWT_SECRET_KEY, PERSISTENT_DIR
import os
from datetime import timedelta
from flask_jwt_extended import JWTManager
import threading
from backend.services.job_processor import process_pending_jobs

from flask_cors import CORS
from backend.routes.auth_routes import auth_bp
from backend.routes.job_routes import job_bp
from backend.routes.resume_routes import resume_bp
from backend.routes.analysis_routes import analysis_bp
from backend.routes.settings_routes import settings_bp
from backend.routes.chat_routes import chat_bp
from backend.routes.mail_routes import mail_bp
from backend.routes.resume_generate_route import resume_gen_bp

app = Flask(__name__)


# Very important: Enable CORS so frontend domain can talk to backend domain!
CORS(app)

# Intelligent Database Configuration
if DB_HOST and DB_USER and DB_PASSWORD and DB_NAME:
    # Use PostgreSQL if credentials are provided
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
else:
    # Fallback to local SQLite inside the persistent file storage
    sqlite_path = os.path.join(PERSISTENT_DIR, "database.sqlite")
    # For Windows/Linux pathing, use absolute path format required by SQLAlchemy
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.abspath(sqlite_path)}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)



db.init_app(app)

def check_migrations():
    """Ensure database schema is up to date on startup."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    
    # helper for specific table migrations
    def safe_add_column(table_name, col_name, col_type_sql):
        try:
            if table_name in inspector.get_table_names():
                columns = [c["name"].lower() for c in inspector.get_columns(table_name)]
                if col_name.lower() not in columns:
                    print(f"Migration: Adding {col_name} to {table_name} table...")
                    # Quote table name for safety (reserved words)
                    quoted_table = f'"{table_name}"' if table_name in ("user", "users") else table_name
                    db.session.execute(text(f'ALTER TABLE {quoted_table} ADD COLUMN {col_name} {col_type_sql}'))
                    db.session.commit()
                    print(f"Successfully added {col_name} to {table_name}")
        except Exception as e:
            print(f"Migration failed for {table_name}.{col_name}: {e}")
            db.session.rollback()

    # User table migrations
    safe_add_column("user", "reset_token", "VARCHAR(255)")
    safe_add_column("user", "reset_token_expiry", "TIMESTAMP")

    # Jobs table migrations
    safe_add_column("jobs", "is_parsed", "BOOLEAN DEFAULT FALSE")
    safe_add_column("jobs", "raw_content", "TEXT")
    safe_add_column("jobs", "error_message", "TEXT")
    safe_add_column("jobs", "retry_count", "INTEGER DEFAULT 0")

    # Resume table migrations
    safe_add_column("resume", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # Analysis table migrations
    safe_add_column("analysis", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # Column type updates (mostly for Postgres)
    if "jobs" in inspector.get_table_names():
        print("Migration: Ensuring job table columns are TEXT...")
        for col in ["job_title", "job_id", "company", "location", "job_type", "progress", "experience_required"]:
            try:
                if "postgresql" in str(db.engine.url):
                    db.session.execute(text(f'ALTER TABLE jobs ALTER COLUMN {col} TYPE TEXT'))
            except Exception as e:
                print(f"Migration warning on column {col}: {e}")
        db.session.commit()

    # Cleanup orphaned analysis records
    try:
        if "analysis" in inspector.get_table_names() and "jobs" in inspector.get_table_names():
            print("Migration: Cleaning up orphaned analysis records...")
            db.session.execute(text('DELETE FROM analysis WHERE job_id NOT IN (SELECT id FROM jobs)'))
            db.session.commit()
    except Exception as e:
        print(f"Cleanup error: {e}")
        db.session.rollback()



with app.app_context():
    db.create_all()
    try:
        check_migrations()
    except Exception as e:
        print(f"Global Migration system error: {e}")
        db.session.rollback()

jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(job_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(mail_bp)
app.register_blueprint(resume_gen_bp)


if __name__ == "__main__":
    import os
    # Start the background worker thread only in the main process (not the reloader child)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        worker = threading.Thread(target=process_pending_jobs, args=(app,), daemon=True)
        worker.start()
        print("Background worker started.")
        
    app.run(debug=True, port=5001, use_reloader=True)