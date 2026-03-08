from datetime import date

from flask import Blueprint, jsonify, request

from db_utils import db

bp = Blueprint("customer_coupon", __name__)


@bp.route("/api/coupon/validate", methods=["POST"])
def api_coupon():
    code = request.json.get("code", "").strip().upper()
    c = db()
    cp = c.execute(
        "SELECT * FROM coupons WHERE code=? AND active=1", (code,)
    ).fetchone()
    c.close()
    if not cp:
        return jsonify({"error": "Invalid coupon code"}), 400
    if cp["expiry"] and cp["expiry"] < date.today().isoformat():
        return jsonify({"error": "Coupon has expired"}), 400
    return jsonify(
        {
            "valid": True,
            "code": cp["code"],
            "type": cp["discount_type"],
            "value": cp["discount_value"],
            "free_delivery": bool(cp["free_delivery"]),
        }
    )
