# show_bookings.py
from app import app, db, Booking, User

with app.app_context():
    print("Users:")
    users = User.query.order_by(User.id).all()
    if not users:
        print("  (no users)")
    for u in users:
        print(f"  id={u.id}  name={u.name!r}  email={u.email!r}")

    print("\nBookings (first 200):")
    bs = Booking.query.order_by(Booking.id).limit(200).all()
    if not bs:
        print("  (no bookings)")
    for b in bs:
        # Print fields safely (some older DB rows might not have user_id column)
        uid = getattr(b, "user_id", None)
        print(f"  id={b.id}  email={b.email!r}  user_id={uid}  dest_id={b.destination_id}  status={b.status}")