import json

from flask import Blueprint, jsonify, request

from db_utils import db

bp = Blueprint("customer_products", __name__)


@bp.route("/api/products")
def api_products():
    q = request.args.get("q", "")
    cat = request.args.get("category", "")
    gnd = request.args.get("gender", "")
    mx = request.args.get("max_price", 99999, type=float)
    mn = request.args.get("min_price", 0, type=float)
    bs = request.args.get("best_seller", "")
    dc = request.args.get("discounted", "")
    srt = request.args.get("sort", "")
    fs = request.args.get("festival", "")
    ml = request.args.get("most_liked", "")
    lim = request.args.get("limit", 100, type=int)

    sql = "SELECT * FROM products WHERE active=1"
    p = []
    if q:
        sql += " AND name LIKE ?"
        p.append(f"%{q}%")
    if cat:
        sql += " AND category=?"
        p.append(cat)
    if gnd:
        sql += " AND gender_tag=?"
        p.append(gnd)
    if mn:
        sql += " AND price>=?"
        p.append(mn)
    if mx < 99999:
        sql += " AND price<=?"
        p.append(mx)
    if bs == "1":
        sql += " AND is_best_seller=1"
    if dc == "1":
        sql += " AND discount>0"
    if fs == "1":
        sql += " AND is_festival_special=1"
    if ml == "1":
        sql += " AND is_most_liked=1"
    sql += {
        "price_asc": " ORDER BY price ASC",
        "price_desc": " ORDER BY price DESC",
        "likes": " ORDER BY likes DESC",
        "best_selling": " ORDER BY is_best_seller DESC,likes DESC",
        "newest": " ORDER BY created_at DESC",
    }.get(srt, " ORDER BY likes DESC")
    sql += f" LIMIT {lim}"
    c = db()
    rows = [dict(r) for r in c.execute(sql, p).fetchall()]
    c.close()
    for r in rows:
        r["dp"] = (
            round(r["price"] * (1 - r["discount"] / 100), 2)
            if r["discount"]
            else r["price"]
        )
        try:
            r["images"] = json.loads(r["images"]) if r["images"] else [r["image_url"]]
        except Exception:
            r["images"] = [r["image_url"]]
    return jsonify(rows)


@bp.route("/api/products/<int:pid>")
def api_product(pid):
    c = db()
    p = c.execute(
        "SELECT * FROM products WHERE id=? AND active=1", (pid,)
    ).fetchone()
    if not p:
        c.close()
        return jsonify({"error": "Not found"}), 404
    pd = dict(p)
    pd["dp"] = (
        round(pd["price"] * (1 - pd["discount"] / 100), 2)
        if pd["discount"]
        else pd["price"]
    )
    try:
        pd["images"] = json.loads(pd["images"]) if pd["images"] else [pd["image_url"]]
    except Exception:
        pd["images"] = [pd["image_url"]]
    raw_reviews = c.execute(
        "SELECT * FROM reviews WHERE product_id=? ORDER BY created_at DESC",
        (pid,),
    ).fetchall()
    parsed_reviews = []
    for r in raw_reviews:
        rv = dict(r)
        try:
            rv["images"] = json.loads(rv["images"]) if rv.get("images") else []
        except Exception:
            rv["images"] = []
        parsed_reviews.append(rv)
    pd["reviews"] = parsed_reviews
    rel = [
        dict(r)
        for r in c.execute(
            "SELECT * FROM products WHERE category=? AND id!=? AND active=1 LIMIT 4",
            (pd["category"], pid),
        ).fetchall()
    ]
    for r in rel:
        r["dp"] = (
            round(r["price"] * (1 - r["discount"] / 100), 2)
            if r["discount"]
            else r["price"]
        )
    pd["related"] = rel
    c.close()
    return jsonify(pd)


@bp.route("/api/products/<int:pid>/like", methods=["POST"])
def api_like(pid):
    c = db()
    c.execute("UPDATE products SET likes=likes+1 WHERE id=?", (pid,))
    c.commit()
    lk = c.execute("SELECT likes FROM products WHERE id=?", (pid,)).fetchone()["likes"]
    c.close()
    return jsonify({"likes": lk})


@bp.route("/api/categories")
def api_cats():
    import json
    c = db()
    # Prefer categories stored by admin in site_settings
    row = c.execute(
        "SELECT value FROM site_settings WHERE key='product_categories'"
    ).fetchone()
    if row:
        try:
            cats = json.loads(row["value"])
            c.close()
            return jsonify(cats)
        except Exception:
            pass
    # Fallback: derive from active products
    cats = [
        r[0]
        for r in c.execute(
            "SELECT DISTINCT category FROM products WHERE active=1"
        ).fetchall()
    ]
    c.close()
    return jsonify(cats)