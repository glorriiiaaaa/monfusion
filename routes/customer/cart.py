from flask import Blueprint, jsonify, request, session

from auth_utils import require_user
from db_utils import db

bp = Blueprint("customer_cart", __name__)


@bp.route("/api/cart")
def api_cart():
    uid = session.get("user_id")
    if not uid:
        return jsonify([])
    c = db()
    items = c.execute(
        "SELECT c.id,c.quantity,p.id as product_id,p.name,p.price,p.discount,p.image_url "
        "FROM cart c JOIN products p ON c.product_id=p.id WHERE c.user_id=?",
        (uid,),
    ).fetchall()
    c.close()
    result = []
    for i in items:
        r = dict(i)
        r["dp"] = (
            round(r["price"] * (1 - r["discount"] / 100), 2)
            if r["discount"]
            else r["price"]
        )
        result.append(r)
    return jsonify(result)


@bp.route("/api/cart/count")
def api_cart_count():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"count": 0})
    c = db()
    n = (
        c.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?", (uid,)).fetchone()[0]
        or 0
    )
    c.close()
    return jsonify({"count": n})


@bp.route("/api/cart/add", methods=["POST"])
@require_user
def api_cart_add():
    d = request.json
    pid = d.get("product_id")
    qty = d.get("quantity", 1)
    uid = session["user_id"]
    c = db()
    ex = c.execute(
        "SELECT * FROM cart WHERE user_id=? AND product_id=?", (uid, pid)
    ).fetchone()
    if ex:
        c.execute("UPDATE cart SET quantity=quantity+? WHERE id=?", (qty, ex["id"]))
    else:
        c.execute(
            "INSERT INTO cart(user_id,product_id,quantity) VALUES(?,?,?)",
            (uid, pid, qty),
        )
    c.commit()
    n = (
        c.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?", (uid,)).fetchone()[0]
        or 0
    )
    c.close()
    return jsonify({"success": True, "cart_count": n})


@bp.route("/api/cart/remove", methods=["POST"])
@require_user
def api_cart_remove():
    cid = request.json.get("cart_id")
    c = db()
    c.execute(
        "DELETE FROM cart WHERE id=? AND user_id=?", (cid, session["user_id"])
    )
    c.commit()
    c.close()
    return jsonify({"success": True})


@bp.route("/api/cart/update", methods=["POST"])
@require_user
def api_cart_update():
    d = request.json
    cid = d.get("cart_id")
    qty = d.get("quantity", 1)
    c = db()
    if qty < 1:
        c.execute(
            "DELETE FROM cart WHERE id=? AND user_id=?", (cid, session["user_id"])
        )
    else:
        c.execute(
            "UPDATE cart SET quantity=? WHERE id=? AND user_id=?",
            (qty, cid, session["user_id"]),
        )
    c.commit()
    c.close()
    return jsonify({"success": True})
