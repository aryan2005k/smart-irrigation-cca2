"""SQLite helper for optional scripts and extensions."""
import os, sqlite3
DATABASE=os.environ.get("DATABASE_PATH",os.path.join(os.path.dirname(__file__),"irrigation.db"))
def connect():
    os.makedirs(os.path.dirname(DATABASE),exist_ok=True)
    c=sqlite3.connect(DATABASE); c.row_factory=sqlite3.Row
    return c
