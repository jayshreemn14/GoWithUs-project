# seed.py - run this once to load destinations.json into DB
import requests, json, os
from app import app, db, Destination

BASE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(BASE, "destinations.json")
with app.app_context():
    db.drop_all()
    db.create_all()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            d = Destination(
                name = it.get("name"),
                location = it.get("location"),
                description = it.get("description"),
                image_url = it.get("image_url"),
                price = int(it.get("price") or 0),
                category = it.get("category"),
                rating = float(it.get("rating") or 4.5)
            )
            db.session.add(d)
        db.session.commit()
        print("Seeded", len(items))
    else:
        print("destinations.json not found")
