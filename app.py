# app.py
import os
import json
import threading
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'gowithus.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "dev-key"

db = SQLAlchemy(app)

# ---------------------------------------------------
# Load extra details from destinations.json
# ---------------------------------------------------
DEST_JSON_ITEMS = []
DEST_LOOKUP_BY_NAME = {}

json_path_global = os.path.join(BASE_DIR, "destinations.json")
if os.path.exists(json_path_global):
    try:
        with open(json_path_global, "r", encoding="utf-8") as f:
            DEST_JSON_ITEMS = json.load(f) or []
        for item in DEST_JSON_ITEMS:
            name = item.get("name")
            if name:
                DEST_LOOKUP_BY_NAME[name] = item
    except Exception:
        DEST_JSON_ITEMS = []
        DEST_LOOKUP_BY_NAME = {}


def extra_info_for(name: str):
    src = DEST_LOOKUP_BY_NAME.get(name) or {}
    return {
        "best_time_to_visit": src.get("best_time_to_visit"),
        "highlights": src.get("highlights") or src.get("attractions"),
        "activities": src.get("activities"),
    }


# ---------------------------------------------------
# Models
# ---------------------------------------------------
class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    price = db.Column(db.Integer)
    category = db.Column(db.String(80))
    rating = db.Column(db.Float, default=4.5)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    preferences = db.Column(db.Text, default='[]')  # JSON list stored as text


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    destination_id = db.Column(db.Integer, db.ForeignKey('destination.id'), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    guests = db.Column(db.Integer, default=1)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="confirmed")
    total_price = db.Column(db.Integer)

    # extra fields for booking UI
    phone = db.Column(db.String(30))
    accommodation_type = db.Column(db.String(50))
    special_requests = db.Column(db.Text)

    destination = db.relationship("Destination", backref="bookings", lazy=True)
    user = db.relationship("User", backref="bookings", lazy=True)


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def require_user_header():
    uid = request.headers.get("X-User-Id")
    if not uid:
        abort(401, "Missing X-User-Id header")
    user = User.query.get(int(uid))
    if not user:
        abort(403, "Invalid user token")
    return user


def fallback_price_for_category(cat):
    mapping = {
        'beach': 6000,
        'nature': 4500,
        'cultural': 3200,
        'mountain': 5000,
        'adventure': 5500,
        'city': 4000,
        'romantic': 7000,
        'luxury': 15000
    }
    return mapping.get((cat or "").lower(), 3500)


# small profiles backing file (safe multi-thread write)
_PROFILES_PATH = os.path.join(BASE_DIR, "profiles.json")
_profiles_lock = threading.Lock()


def _read_profiles():
    p = Path(_PROFILES_PATH)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


def _write_profiles(d):
    with _profiles_lock:
        with open(_PROFILES_PATH, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)


# ---------------------------------------------------
# Routes / APIs
# ---------------------------------------------------

# show login page first
@app.route("/")
def root():
    return app.send_static_file("login.html")


@app.route("/api/destinations")
def api_destinations():
    q = (request.args.get("q") or "").strip().lower()
    query = Destination.query.order_by(Destination.rating.desc())
    results = []
    for d in query:
        if q and q not in (d.name + " " + (d.location or "") + " " + (d.description or "")).lower():
            continue
        price = d.price or fallback_price_for_category(d.category)
        extra = extra_info_for(d.name)
        results.append({
            "id": d.id,
            "name": d.name,
            "location": d.location,
            "description": d.description,
            "image_url": d.image_url,
            "price": price,
            "category": d.category,
            "rating": float(d.rating or 0),
            "best_time_to_visit": extra.get("best_time_to_visit"),
            "highlights": extra.get("highlights"),
            "activities": extra.get("activities"),
        })
    return jsonify(results)


@app.route("/api/destination/<int:dest_id>")
def api_destination(dest_id):
    d = Destination.query.get_or_404(dest_id)
    price = d.price or fallback_price_for_category(d.category)
    extra = extra_info_for(d.name)
    return jsonify({
        "id": d.id,
        "name": d.name,
        "location": d.location,
        "description": d.description,
        "image_url": d.image_url,
        "price": price,
        "category": d.category,
        "rating": float(d.rating or 0),
        "best_time_to_visit": extra.get("best_time_to_visit"),
        "highlights": extra.get("highlights"),
        "activities": extra.get("activities"),
    })


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not name or not email or not password:
        return jsonify({"error": "name,email,password required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email exists"}), 400
    u = User(name=name, email=email, password=generate_password_hash(password))
    db.session.add(u)
    db.session.commit()
    return jsonify({
        "message": "registered",
        "token": u.id,
        "user": {"id": u.id, "name": u.name, "email": u.email}
    })


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    u = User.query.filter_by(email=email).first()
    if not u or not check_password_hash(u.password, password):
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({
        "message": "ok",
        "token": u.id,
        "user": {"id": u.id, "name": u.name, "email": u.email}
    })


@app.route("/api/profile", methods=["GET", "POST"])
def api_profile():
    uid = request.headers.get("X-User-Id")
    if request.method == "GET":
        if not uid:
            return jsonify({"error": "missing X-User-Id header"}), 401
        profiles = _read_profiles()
        prof = profiles.get(str(uid), {})
        return jsonify({"profile": prof})

    data = request.get_json(silent=True) or {}
    profile = {
        "name": (data.get("name") or "").strip(),
        "email": (data.get("email") or "").strip().lower(),
        "phone": (data.get("phone") or "").strip(),
        "preferences": data.get("preferences") or []
    }
    if uid:
        profiles = _read_profiles()
        profiles[str(uid)] = profile
        try:
            _write_profiles(profiles)
        except Exception as e:
            return jsonify({"error": "failed to save profile", "details": str(e)}), 500
        return jsonify({"message": "saved", "profile": profile})
    else:
        return jsonify({"message": "not-signed-in", "profile": profile})


@app.route("/api/book", methods=["POST"])
def api_book():
    data = request.get_json() or {}
    uid = request.headers.get("X-User-Id")
    user = User.query.get(int(uid)) if uid else None

    dest_id = data.get("destination_id")
    full_name = data.get("full_name")
    email = data.get("email")
    guests = int(data.get("guests", 1))
    check_in = data.get("check_in")
    check_out = data.get("check_out")
    phone = data.get("phone")
    accommodation_type = data.get("accommodation_type")
    special_requests = data.get("special_requests")

    if not (dest_id and full_name and email and check_in and check_out and phone and accommodation_type):
        return jsonify({"error": "missing fields"}), 400

    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d").date()
        co = datetime.strptime(check_out, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"error": "invalid date"}), 400

    if co <= ci:
        return jsonify({"error": "checkout must be after checkin"}), 400

    d = Destination.query.get_or_404(dest_id)
    nights = (co - ci).days
    price_per_night = d.price or fallback_price_for_category(d.category)
    total = nights * (price_per_night or 0) * max(guests, 1)

    b = Booking(
        destination_id=d.id,
        full_name=full_name,
        email=email,
        user_id=user.id if user else None,
        guests=guests,
        check_in=ci,
        check_out=co,
        total_price=total,
        status="confirmed",
        phone=phone,
        accommodation_type=accommodation_type,
        special_requests=special_requests
    )
    db.session.add(b)
    db.session.commit()
    return jsonify({"message": "booked", "booking_id": b.id, "total": total})


@app.route("/api/my-bookings")
def api_my_bookings():
    user = require_user_header()
    bs = Booking.query.filter_by(user_id=user.id).order_by(Booking.check_in.desc()).all()
    out = []
    for b in bs:
        out.append({
            "id": b.id,
            "destination": {
                "id": b.destination.id,
                "name": b.destination.name,
                "location": b.destination.location,
                "image_url": b.destination.image_url,
                "price": b.destination.price or fallback_price_for_category(b.destination.category)
            },
            "full_name": b.full_name,
            "email": b.email,
            "phone": b.phone,
            "guests": b.guests,
            "check_in": b.check_in.isoformat(),
            "check_out": b.check_out.isoformat(),
            "status": b.status,
            "total_price": b.total_price,
            "accommodation_type": b.accommodation_type,
            "special_requests": b.special_requests
        })
    return jsonify(out)


@app.route("/api/cancel/<int:booking_id>", methods=["POST"])
def api_cancel(booking_id):
    user = require_user_header()
    b = Booking.query.get_or_404(booking_id)
    if b.user_id != user.id:
        return jsonify({"error": "not allowed"}), 403
    if b.status == "cancelled":
        return jsonify({"message": "already cancelled"})
    b.status = "cancelled"
    db.session.commit()
    return jsonify({"message": "cancelled"})


@app.route("/api/invoice/<int:booking_id>")
def api_invoice(booking_id):
    user = require_user_header()
    b = Booking.query.get_or_404(booking_id)
    if b.user_id != user.id:
        return jsonify({"error": "not allowed"}), 403

    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    # --- GoWithUs branding header ---
    pdf.setFont("Helvetica-Bold", 20)
    pdf.setFillColorRGB(0.9, 0.2, 0.4)  # pink theme
    pdf.drawString(50, h - 60, "GoWithUs")

    pdf.setFont("Helvetica", 12)
    pdf.setFillColorRGB(0, 0, 0)
    pdf.drawString(50, h - 80, f"Booking Invoice #{b.id}")

    pdf.setFont("Helvetica-Oblique", 10)
    pdf.setFillColorRGB(0.5, 0.5, 0.5)
    pdf.drawString(50, h - 95, "Explore. Experience. Enjoy.")

    pdf.setFont("Helvetica", 12)
    pdf.setFillColorRGB(0, 0, 0)

    # --- Invoice body ---
    y = h - 130
    lines = [
        f"Guest: {b.full_name}",
        f"Email: {b.email}",
        f"Phone: {b.phone or '-'}",
        f"Destination: {b.destination.name}",
        f"Check-in: {b.check_in.strftime('%d %b %Y')}  Check-out: {b.check_out.strftime('%d %b %Y')}",
        f"Guests: {b.guests}",
        f"Accommodation: {b.accommodation_type or '-'}",
        f"Status: {b.status}",
        f"Special requests: {b.special_requests or '-'}",
        f"Total: ₹ {b.total_price:,}"
    ]
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 18

    pdf.showPage()
    pdf.save()
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"invoice_{b.id}.pdf",
        mimetype="application/pdf"
    )


@app.route("/api/recommendations")
def api_recommendations():
    uid = request.headers.get("X-User-Id")
    prefs = []
    if uid:
        profiles = _read_profiles()
        prof = profiles.get(str(uid), {})
        prefs = prof.get("preferences") or []

    dests = Destination.query.order_by(Destination.rating.desc()).all()
    out = []
    if prefs:
        pref_l = [p.lower() for p in prefs]
        for d in dests:
            if (d.category or "").lower() in pref_l:
                out.append({
                    "id": d.id,
                    "name": d.name,
                    "image_url": d.image_url,
                    "price": d.price or fallback_price_for_category(d.category),
                    "category": d.category,
                    "rating": float(d.rating or 0)
                })
        seen = {x['id'] for x in out}
        for d in dests:
            if d.id in seen:
                continue
            out.append({
                "id": d.id,
                "name": d.name,
                "image_url": d.image_url,
                "price": d.price or fallback_price_for_category(d.category),
                "category": d.category,
                "rating": float(d.rating or 0)
            })
            if len(out) >= 12:
                break
    else:
        for d in dests[:12]:
            out.append({
                "id": d.id,
                "name": d.name,
                "image_url": d.image_url,
                "price": d.price or fallback_price_for_category(d.category),
                "category": d.category,
                "rating": float(d.rating or 0)
            })
    return jsonify(out)


# ---------- TEMP ADMIN ROUTE TO DELETE UDAIPUR & MANALI ----------
@app.route("/admin/delete_udaipur_manali")
def admin_delete_udaipur_manali():
    names = ["Udaipur", "Manali"]
    deleted = []
    for name in names:
        dest = Destination.query.filter_by(name=name).first()
        if dest:
            Booking.query.filter_by(destination_id=dest.id).delete()
            db.session.delete(dest)
            deleted.append(name)
    if deleted:
        db.session.commit()
    return jsonify({"deleted": deleted or []})
# ---------------------------------------------------------------


@app.route("/images/<path:filename>")
def images(filename):
    folder = os.path.join(BASE_DIR, "static", "images")
    return send_from_directory(folder, filename)


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    token = request.get_json(silent=True) or {}
    if token.get("token") != "RESET-OK":
        return jsonify({"error": "unauthorized"}), 403
    db.drop_all()
    db.create_all()
    json_path = os.path.join(BASE_DIR, "destinations.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            d = Destination(
                name=it.get("name"),
                location=it.get("location"),
                description=it.get("description"),
                image_url=it.get("image_url"),
                price=int(it.get("price") or 0),
                category=it.get("category"),
                rating=float(it.get("rating") or 4.5)
            )
            db.session.add(d)
        db.session.commit()
    return jsonify({"message": "reset done"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)