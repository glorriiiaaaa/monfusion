from datetime import date

from flask import Blueprint, jsonify, request

from db_utils import db

bp = Blueprint("customer_coupon", __name__)


@bp.route("/api/coupon/validate", methods=["POST"])
def api_coupon():
    from flask import session
    code = request.json.get("code", "").strip().upper()
    c = db()
    cp = c.execute(
        "SELECT * FROM coupons WHERE code=? AND active=1", (code,)
    ).fetchone()
    if not cp:
        c.close()
        return jsonify({"error": "Invalid coupon code"}), 400
    if cp["expiry"] and cp["expiry"] < date.today().isoformat():
        c.close()
        return jsonify({"error": "Coupon has expired"}), 400
    # Check global usage limit (max_uses=0 means unlimited)
    max_uses = cp["max_uses"] if "max_uses" in cp.keys() else 0
    used_count = cp["used_count"] if "used_count" in cp.keys() else 0
    if max_uses > 0 and used_count >= max_uses:
        c.close()
        return jsonify({"error": "This coupon has reached its usage limit"}), 400
    # Check per-user usage limit (max 1 use per user)
    uid = session.get("user_id")
    if uid:
        user_uses = c.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id=? AND coupon_code=?", (uid, code)
        ).fetchone()[0]
        if user_uses >= 1:
            c.close()
            return jsonify({"error": "You have already used this coupon"}), 400
    c.close()
    return jsonify(
        {
            "valid": True,
            "code": cp["code"],
            "type": cp["discount_type"],
            "value": cp["discount_value"],
            "free_delivery": bool(cp["free_delivery"]),
        }
    )