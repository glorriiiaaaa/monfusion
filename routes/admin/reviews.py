from flask import Blueprint, jsonify

from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_reviews", __name__)


@bp.route("/api/admin/reviews", methods=["GET"])
@require_admin
def admin_get_reviews():
    c = db()
    rows = c.execute(
        """
        SELECT r.id, r.product_id, r.user_id, r.user_name, r.rating,
               r.comment, r.created_at, p.name as product_name, p.image_url
        FROM reviews r
        JOIN products p ON r.product_id = p.id
        ORDER BY r.created_at DESC
        """
    ).fetchall()
    c.close()
    return jsonify([dict(r) for r in rows])


@bp.route("/api/admin/reviews/<int:rid>", methods=["DELETE"])
@require_admin
def admin_delete_review(rid):
    c = db()
    review = c.execute("SELECT product_id FROM reviews WHERE id=?", (rid,)).fetchone()
    if not review:
        c.close()
        return jsonify({"error": "Review not found"}), 404
    pid = review["product_id"]
    c.execute("DELETE FROM reviews WHERE id=?", (rid,))
    # Recalculate product rating after deletion
    avg = c.execute(
        "SELECT AVG(rating) FROM reviews WHERE product_id=?", (pid,)
    ).fetchone()[0]
    new_rating = round(avg, 1) if avg else 4.0
    c.execute("UPDATE products SET rating=? WHERE id=?", (new_rating, pid))
    c.commit()
    c.close()
    return jsonify({"success": True})