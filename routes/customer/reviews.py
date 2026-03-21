import json

from flask import Blueprint, jsonify, request, session

from auth_utils import require_user
from db_utils import db

bp = Blueprint("customer_reviews", __name__)


@bp.route("/api/reviews", methods=["POST"])
@require_user
def api_review():
    d = request.json
    pid = d.get("product_id")
    rt = d.get("rating", 5)
    cm = d.get("comment", "").strip()
    images = d.get("images", [])  # list of base64 strings (optional)

    if not cm:
        return jsonify({"error": "Comment required"}), 400
    if not 1 <= rt <= 5:
        return jsonify({"error": "Rating must be 1-5"}), 400
    if not isinstance(images, list):
        images = []
    # Cap at 5 images, each base64 string max ~5MB
    images = images[:5]

    uid = session["user_id"]
    c = db()
    un = c.execute("SELECT name FROM users WHERE id=?", (uid,)).fetchone()
    un = un["name"] if un else "Anonymous"
    images_json = json.dumps(images) if images else None
    c.execute(
        "INSERT INTO reviews(product_id,user_id,user_name,rating,comment,images) VALUES(?,?,?,?,?,?)",
        (pid, uid, un, rt, cm, images_json),
    )
    avg = c.execute(
        "SELECT AVG(rating) FROM reviews WHERE product_id=?", (pid,)
    ).fetchone()[0]
    c.execute("UPDATE products SET rating=? WHERE id=?", (round(avg, 1), pid))
    c.commit()
    c.close()
    return jsonify({"success": True})