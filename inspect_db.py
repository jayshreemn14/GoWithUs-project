# inspect_db.py
from app import app, db, User, Booking
with app.app_context():
    print("Users:")
    for u in User.query.all():
        print(u.id, u.name, u.email)
    print("\nBookings (first 50):")
    for b in Booking.query.limit(50).all():
        print(b.id, b.email, getattr(b, 'user_id', None), b.destination_id, b.status)
