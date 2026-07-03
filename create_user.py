# create_user.py
from app import app, db, User
from werkzeug.security import generate_password_hash

NAME = "Jayshree"
EMAIL = "jayshreemn14@gmail.com"
PASSWORD = "Password123!"  # change as you like

with app.app_context():
    if User.query.filter_by(email=EMAIL).first():
        u = User.query.filter_by(email=EMAIL).first()
        print("User already exists:", u.id, u.email)
    else:
        u = User(name=NAME, email=EMAIL, password=generate_password_hash(PASSWORD))
        db.session.add(u)
        db.session.commit()
        print("Created user:", u.id, u.email)
