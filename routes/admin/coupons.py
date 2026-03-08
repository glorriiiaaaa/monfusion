from flask import Blueprint, jsonify, request

from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_coupons", __name__)


@bp.route("/api/admin/coupons", methods=["GET"])
@require_admin
def admin_get_coupons():
    c = db()
    rows = [dict(r) for r in c.execute("SELECT * FROM coupons ORDER BY id DESC").fetchall()]
    c.close()
    return jsonify(rows)


@bp.route("/api/admin/coupons", methods=["POST"])
@require_admin
def admin_add_coupon():
    d = request.json
    code = d.get("code", "").strip().upper()
    if not code:
        return jsonify({"error": "Coupon code required"}), 400
    c = db()
    try:
        cur = c.execute(
            "INSERT INTO coupons(code,discount_type,discount_value,free_delivery,expiry,active) VALUES(?,?,?,?,?,1)",
            (
                code,
                d.get("discount_type", "percent"),
                d.get("discount_value", 0),
                1 if d.get("free_delivery") else 0,
                d.get("expiry", ""),
            ),
        )
        c.commit()
        cid = cur.lastrowid
        c.close()
        return jsonify({"success": True, "id": cid})
    except Exception:
        c.close()
        return jsonify({"error": "Coupon code already exists"}), 400


@bp.route("/api/admin/coupons/<int:cid>", methods=["PUT"])
@require_admin
def admin_update_coupon(cid):
    d = request.json
    c = db()
    c.execute(
        "UPDATE coupons SET discount_type=?,discount_value=?,free_delivery=?,expiry=?,active=? WHERE id=?",
        (
            d.get("discount_type", "percent"),
            d.get("discount_value", 0),
            1 if d.get("free_delivery") else 0,
            d.get("expiry", ""),
            1 if d.get("active", True) else 0,
            cid,
        ),
    )
    c.commit()
    c.close()
    return jsonify({"success": True})


@bp.route("/api/admin/coupons/<int:cid>", methods=["DELETE"])
@require_admin
def admin_delete_coupon(cid):
    c = db()
    c.execute("DELETE FROM coupons WHERE id=?", (cid,))
    c.commit()
    c.close()
    return jsonify({"success": True})
