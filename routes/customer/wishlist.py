from flask import Blueprint, jsonify, request, session

from auth_utils import require_user
from db_utils import db

bp = Blueprint("customer_wishlist", __name__)


@bp.route("/api/wishlist")
def api_wish():
    uid = session.get("user_id")
    if not uid:
        return jsonify([])
    c = db()
    items = c.execute(
        "SELECT w.id,p.id as product_id,p.name,p.price,p.discount,p.image_url,p.rating "
        "FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.user_id=?",
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


@bp.route("/api/wishlist/toggle", methods=["POST"])
@require_user
def api_wish_toggle():
    pid = request.json.get("product_id")
    uid = session["user_id"]
    c = db()
    ex = c.execute(
        "SELECT * FROM wishlist WHERE user_id=? AND product_id=?", (uid, pid)
    ).fetchone()
    if ex:
        c.execute("DELETE FROM wishlist WHERE id=?", (ex["id"],))
        c.commit()
        c.close()
        return jsonify({"added": False})
    c.execute("INSERT INTO wishlist(user_id,product_id) VALUES(?,?)", (uid, pid))
    c.commit()
    c.close()
    return jsonify({"added": True})


@bp.route("/api/wishlist/check/<int:pid>")
def api_wish_check(pid):
    uid = session.get("user_id")
    if not uid:
        return jsonify({"in_wishlist": False})
    c = db()
    ex = c.execute(
        "SELECT id FROM wishlist WHERE user_id=? AND product_id=?", (uid, pid)
    ).fetchone()
    c.close()
    return jsonify({"in_wishlist": bool(ex)})


@bp.route("/api/wishlist/remove", methods=["POST"])
@require_user
def api_wish_remove():
    wid = request.json.get("wishlist_id")
    c = db()
    c.execute(
        "DELETE FROM wishlist WHERE id=? AND user_id=?",
        (wid, session["user_id"]),
    )
    c.commit()
    c.close()
    return jsonify({"success": True})
