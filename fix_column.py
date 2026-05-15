from app import app, db

with app.app_context():
    # allow very long URLs (up to 65k chars)
    db.session.execute(db.text("ALTER TABLE destinations MODIFY image_url TEXT"))
    db.session.commit()
    print("✅ image_url column changed to TEXT")
