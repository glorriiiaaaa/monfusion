from flask import Blueprint, jsonify, request

from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_orders", __name__)


@bp.route("/api/admin/orders", methods=["GET"])
@require_admin
def admin_get_orders():
    status = request.args.get("status", "")
    c = db()
    sql = "SELECT * FROM orders"
    params = []
    if status:
        sql += " WHERE status=?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    ords = [dict(o) for o in c.execute(sql, params).fetchall()]
    for o in ords:
        items = c.execute(
            "SELECT oi.*,p.name,p.image_url FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?",
            (o["order_id"],),
        ).fetchall()
        o["items"] = [dict(i) for i in items]
    c.close()
    return jsonify(ords)


@bp.route("/api/admin/orders/<string:oid>/status", methods=["PUT"])
@require_admin
def admin_update_order_status(oid):
    status = request.json.get("status", "")
    if status not in ["pending", "shipped", "delivered", "cancelled"]:
        return jsonify({"error": "Invalid status"}), 400
    c = db()
    c.execute("UPDATE orders SET status=? WHERE order_id=?", (status, oid))
    c.commit()
    c.close()
    return jsonify({"success": True})
