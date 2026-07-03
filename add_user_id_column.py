# add_user_id_column.py
from app import app, db
from sqlalchemy import inspect, text

with app.app_context():
    inspector = inspect(db.engine)
    if 'bookings' not in inspector.get_table_names():
        print("ERROR: bookings table not found. Did you use the right DB?")
        raise SystemExit(1)

    cols = [c['name'] for c in inspector.get_columns('bookings')]
    if 'user_id' in cols:
        print("user_id column already exists. Nothing to do.")
    else:
        print("Adding 'user_id' column to bookings table...")
        db.session.execute(text("ALTER TABLE bookings ADD COLUMN user_id INTEGER"))
        db.session.commit()
        print("Done. 'user_id' column added.")
