#!/usr/bin/env python3
# attach_bookings.py
import sys
from app import app, db, Booking, User
from sqlalchemy import inspect

def main():
    if len(sys.argv) < 3:
        print("Usage: python attach_bookings.py <user_id> <email>")
        return

    user_id = int(sys.argv[1])
    email = sys.argv[2].strip().lower()

    with app.app_context():
        inspector = inspect(db.engine)
        can_set_user_id = 'bookings' in inspector.get_table_names() and 'user_id' in [c['name'] for c in inspector.get_columns('bookings')]

        user = db.session.get(User, user_id)
        if not user:
            print(f"User id {user_id} not found. Aborting.")
            return

        if can_set_user_id:
            q = Booking.query.filter(Booking.user_id == None, Booking.email.ilike(email)).all()
        else:
            q = Booking.query.filter(Booking.email.ilike(email)).all()

        print(f"Found {len(q)} booking(s) for email '{email}'.")

        if not q:
            return

        for b in q:
            if can_set_user_id:
                print(f" - Attaching booking {b.id} -> user_id {user_id}")
                b.user_id = user_id
            else:
                print(f" - Would attach booking {b.id} but cannot because 'user_id' column missing.")

        if can_set_user_id:
            db.session.commit()
            print("Committed changes.")
        else:
            print("No DB changes made (missing user_id column).")

if __name__ == "__main__":
    main()
