from flask import Blueprint, session, send_from_directory

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def customer():
    return send_from_directory(".", "customer.html")


@pages_bp.route("/admin")
def admin_redirect():
    if not session.get("admin_logged_in"):
        return send_from_directory(".", "admin.html")
    return send_from_directory(".", "admin.html")


@pages_bp.route("/admin.html")
def admin_page():
    return send_from_directory(".", "admin.html")


@pages_bp.route("/api/site-content")
def public_site_content():
    import json
    from db_utils import db
    from flask import jsonify
    c = db()
    row = c.execute(
        "SELECT value FROM site_settings WHERE key='site_content'"
    ).fetchone()
    c.close()
    defaults = {
        "hero_badge":     "🌸 India's Most Loved Gift Store",
        "hero_title":     "Gifts that speak from the heart",
        "hero_subtitle":  "Discover magical customised gifts — polaroids, albums, frames & more — lovingly crafted for your most special moments.",
        "hero_image":     "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=700",
        "about_title":    "Turning Moments into Memories",
        "about_para1":    "At Mons Fusion, we believe the best gifts come from the heart. Founded in 2022, we started as a small home-based gifting studio with one simple goal: help people express love through beautifully crafted, personalised gifts.",
        "about_para2":    "From custom polaroids that bring memories to life, to carefully curated hampers for every occasion — every product we create is made with love, attention to detail, and the joy of making someone's day special.",
        "about_image":    "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600",
        "contact_whatsapp":  "+91 98765 43210",
        "contact_email":     "hello@monsfusion.com",
        "contact_instagram": "@monsfusion",
        "contact_hours":     "Mon–Sat: 10am – 8pm IST",
    }
    if row:
        try:
            saved = json.loads(row["value"])
            return jsonify({**defaults, **saved})
        except Exception:
            pass
    return jsonify(defaults)


@pages_bp.route("/api/festival")
def public_festival():
    """Public endpoint — returns festival data if active, else empty."""
    import json
    from db_utils import db
    from flask import jsonify
    c = db()
    row = c.execute(
        "SELECT value FROM site_settings WHERE key='festival_settings'"
    ).fetchone()
    if not row:
        c.close()
        return jsonify({"active": False, "products": [], "all_fest_products": []})
    try:
        saved = json.loads(row["value"])
        if not saved.get("active"):
            c.close()
            return jsonify({"active": False, "products": [], "all_fest_products": []})

        product_ids = saved.get("product_ids", [])

        # Special offer products — admin-selected, shown highlighted at top
        special_products = []
        if product_ids:
            placeholders = ",".join("?" * len(product_ids))
            special_products = [
                dict(p) for p in c.execute(
                    f"SELECT id,name,price,discount,rating,image_url,category,likes,"
                    f"is_best_seller,is_most_liked,is_festival_special "
                    f"FROM products WHERE id IN ({placeholders}) AND active=1",
                    product_ids
                ).fetchall()
            ]

        # All festival products — is_festival_special=1, EXCLUDING already-featured ones
        excluded = ",".join("?" * len(product_ids)) if product_ids else "0"
        params = product_ids + [8] if product_ids else [8]
        all_fest_products = [
            dict(p) for p in c.execute(
                f"SELECT id,name,price,discount,rating,image_url,category,likes,"
                f"is_best_seller,is_most_liked,is_festival_special "
                f"FROM products WHERE is_festival_special=1 AND active=1 "
                + (f"AND id NOT IN ({excluded}) " if product_ids else "")
                + "ORDER BY likes DESC LIMIT ?",
                params
            ).fetchall()
        ]

        c.close()
        return jsonify({
            "active":           True,
            "name":             saved.get("name", "Festival Special Gifts"),
            "emoji":            saved.get("emoji", "✨🎆✨"),
            "offer_text":       saved.get("offer_text", ""),
            "sub_text":         saved.get("sub_text", ""),
            "banner_image":     saved.get("banner_image", ""),
            "products":         special_products,
            "all_fest_products": all_fest_products,
        })
    except Exception:
        c.close()
        return jsonify({"active": False, "products": [], "all_fest_products": []})