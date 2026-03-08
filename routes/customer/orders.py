from flask import Blueprint, jsonify, request, session

from auth_utils import require_user
from db_utils import db, gen_oid

bp = Blueprint("customer_orders", __name__)


@bp.route("/api/orders", methods=["POST"])
def api_orders_post():
    d = request.json
    uid = session.get("user_id")
    nm = d.get("customer_name", "").strip()
    ph = d.get("phone", "").strip()
    if len(nm) < 3:
        return jsonify({"error": "Name must be at least 3 characters"}), 400
    if not ph.isdigit() or len(ph) != 10:
        return jsonify({"error": "Phone must be 10 digits"}), 400
    order_id = gen_oid()
    c = db()
    while c.execute("SELECT id FROM orders WHERE order_id=?", (order_id,)).fetchone():
        order_id = gen_oid()
    c.execute(
        "INSERT INTO orders(user_id,order_id,total_price,address,customer_name,phone,email,payment_method,coupon_code,status) "
        "VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            uid,
            order_id,
            d.get("total_price"),
            d.get("address"),
            nm,
            ph,
            d.get("email"),
            d.get("payment_method"),
            d.get("coupon_code"),
            "pending",
        ),
    )
    for item in d.get("items", []):
        c.execute(
            "INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )
    if uid:
        c.execute("DELETE FROM cart WHERE user_id=?", (uid,))
    c.commit()
    c.close()
    return jsonify({"success": True, "order_id": order_id})


@bp.route("/api/orders/user")
@require_user
def api_orders_user():
    uid = session["user_id"]
    c = db()
    ords = [
        dict(o)
        for o in c.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (uid,)
        ).fetchall()
    ]
    for o in ords:
        items = c.execute(
            "SELECT oi.*,p.name,p.image_url FROM order_items oi "
            "JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?",
            (o["order_id"],),
        ).fetchall()
        o["items"] = [dict(i) for i in items]
    c.close()
    return jsonify(ords)
