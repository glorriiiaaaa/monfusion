from flask import Blueprint, jsonify, request
import re

from db_utils import db

bp = Blueprint("pages_contact", __name__)


@bp.route("/api/contact", methods=["POST"])
def api_contact():
    d = request.json or {}
    name    = d.get("name", "").strip()
    email   = d.get("email", "").strip()
    subject = d.get("subject", "General Inquiry").strip()
    message = d.get("message", "").strip()
    phone   = d.get("phone", "").strip()

    if len(name) < 3:
        return jsonify({"error": "Name must be at least 3 characters"}), 400
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,10}$', email):
        return jsonify({"error": "Invalid email address"}), 400
    if not message:
        return jsonify({"error": "Message is required"}), 400
    if phone and (not re.match(r'^[6-9][0-9]{9}$', phone)):
        return jsonify({"error": "Phone must be 10 digits and start with 6-9"}), 400

    c = db()
    c.execute(
        "INSERT INTO contact_messages(name, email, subject, message, phone) VALUES(?,?,?,?,?)",
        (name, email, subject, message, phone or None),
    )
    c.commit()
    c.close()
    return jsonify({"success": True})