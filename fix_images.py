from app import app, db, Destination

SAFE_IMAGES = {
    # keep your exact names as stored in DB:
    "Bengaluru": "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=800&q=80",
    "Chennai": "https://images.unsplash.com/photo-1605100804749-29fd480b5c4c?w=800&q=80",
    "Kolkata": "https://images.unsplash.com/photo-1591886950606-3c85e4b9e1c1?w=800&q=80",
    "Hyderabad": "https://images.unsplash.com/photo-1599661046289-37fae5b9e2a3?w=800&q=80",
    "Jaipur": "https://images.unsplash.com/photo-1601121149487-8d31e0ed7a94?w=800&q=80",
    "Varanasi": "https://images.unsplash.com/photo-1599904741093-9a0b33e9e685?w=800&q=80",
    "Shimla": "https://images.unsplash.com/photo-1587638402813-cc25c8d3e3ec?w=800&q=80",
    "Dharamshala": "https://images.unsplash.com/photo-1614344007337-2df54e07de8d?w=800&q=80",
    "Mussoorie": "https://images.unsplash.com/photo-1609074643952-4b98124d9020?w=800&q=80",
    "Nainital": "https://images.unsplash.com/photo-1603262110263-fb0112e7cc33?w=800&q=80",
    "Ooty": "https://images.unsplash.com/photo-1580982325720-e1ffe6f4f8ee?w=800&q=80",
    "Coorg": "https://images.unsplash.com/photo-1591209627718-12e5b6a8ce73?w=800&q=80",
    "Munnar": "https://images.unsplash.com/photo-1629113942042-99d9f812778f?w=800&q=80",
    "Kochi": "https://images.unsplash.com/photo-1609167830220-e9c09614504b?w=800&q=80",
    "Thiruvananthapuram": "https://images.unsplash.com/photo-1608906901475-0e9b9c14c5f2?w=800&q=80",
    "Pondicherry": "https://images.unsplash.com/photo-1613397028132-3d75bd905dac?w=800&q=80",
    "Hampi": "https://images.unsplash.com/photo-1577447230728-1e7d05cb8d7e?w=800&q=80",
    "Mysore": "https://images.unsplash.com/photo-1589553801844-cb95d4d862fa?w=800&q=80",
    "Khajuraho": "https://images.unsplash.com/photo-1610020662184-4a26fdff9f88?w=800&q=80",
    "Bodh Gaya": "https://images.unsplash.com/photo-1623153545207-e8d7f8b615b8?w=800&q=80",
    "Gangtok": "https://images.unsplash.com/photo-1609137144815-fb1dfc0d9a02?w=800&q=80",
    "Darjeeling": "https://images.unsplash.com/photo-1598713537035-2e5d79f9f003?w=800&q=80",
    "Andaman Islands": "https://images.unsplash.com/photo-1520975869969-fd1a1a6cf9c9?w=800&q=80",
    "Lakshadweep": "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?w=800&q=80",
    "Konark Sun Temple": "https://images.unsplash.com/photo-1603376868712-75c22871a83b?w=800&q=80",
    "Madurai": "https://images.unsplash.com/photo-1625473813327-0f279d8482a5?w=800&q=80",
    "Varkala": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80",
    "Goa": "https://images.unsplash.com/photo-1548013146-72479768bada?w=800&q=80",
    "Rameswaram": "https://upload.wikimedia.org/wikipedia/commons/f/f1/Pamban_Bridge_Rameshwaram.jpg",
    "Mahabalipuram": "https://upload.wikimedia.org/wikipedia/commons/4/4a/Shore_Temple%2C_Mahabalipuram%2C_India.jpg",
    "Srinagar": "https://upload.wikimedia.org/wikipedia/commons/b/bc/Dal_Lake_Srinagar.jpg",
    "Shillong": "https://upload.wikimedia.org/wikipedia/commons/3/38/Wards_Lake%2C_Shillong.jpg"
}

with app.app_context():
    fixed, missing = 0, []
    for name, url in SAFE_IMAGES.items():
        d = Destination.query.filter_by(name=name).first()
        if not d:
            missing.append(name)
            continue
        d.image_url = url
        fixed += 1
    db.session.commit()
    print(f"✅ Updated {fixed} image URLs.")
    if missing:
        print("⚠️ Not found (name mismatch?):", missing)
