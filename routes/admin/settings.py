import json
from flask import Blueprint, jsonify, request
from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_settings", __name__)

CONTENT_KEY = "site_content"

DEFAULTS = {
    # Hero
    "hero_badge":     "🌸 India's Most Loved Gift Store",
    "hero_title":     "Gifts that speak from the heart",
    "hero_subtitle":  "Discover magical customised gifts — polaroids, albums, frames & more — lovingly crafted for your most special moments.",
    "hero_image":     "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=700",
    # Announcement bar
    "marquee_text":   "🎁 FREE DELIVERY ABOVE ₹499 &nbsp;|&nbsp; ✨ CUSTOM POLAROIDS FROM ₹199 &nbsp;|&nbsp; 💝 COUPLE GIFTS & BIRTHDAY HAMPERS &nbsp;|&nbsp; 🌟 FEST SPECIALS AVAILABLE &nbsp;|&nbsp; 🎀 GIFTS FOR HER & HIM",
    # Stats (shared across hero, stats bar, about)
    "stat1_val":   "10K+",  "stat1_label": "Happy Customers",
    "stat2_val":   "50+",   "stat2_label": "Unique Products",
    "stat3_val":   "4.9★",  "stat3_label": "Average Rating",
    "stat4_val":   "3–5d",  "stat4_label": "Delivery",
    # Homepage sections
    "section_bestsellers_tag":   "Most Popular",
    "section_bestsellers_title": "Best Selling Products",
    "section_festival_title":    "Festival Special Gifts",
    "section_festival_sub":      "Curated for Every Celebration",
    "section_mostliked_tag":     "Community Favourites",
    "section_mostliked_title":   "Most Liked Products",
    # About page
    "about_story_sub":  "Born from a love of meaningful gifting, Mons Fusion creates personalised gifts that tell your story.",
    "about_title":      "Turning Moments into Memories",
    "about_para1":      "At Mons Fusion, we believe the best gifts come from the heart. Founded in 2022, we started as a small home-based gifting studio with one simple goal: help people express love through beautifully crafted, personalised gifts.",
    "about_para2":      "From custom polaroids that bring memories to life, to carefully curated hampers for every occasion — every product we create is made with love, attention to detail, and the joy of making someone's day special.",
    "about_para3":      "Today we serve 10,000+ happy customers across India, and we're just getting started.",
    "about_image":      "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600",
    # Contact info
    "contact_whatsapp":  "+91 98765 43210",
    "contact_email":     "hello@monsfusion.com",
    "contact_instagram": "@monsfusion",
    "contact_hours":     "Mon–Sat: 10am – 8pm IST",
    # Footer
    "footer_desc":      "Creating magical customised gifts for every special moment. Made with love, delivered with care.",
    "footer_copyright": "© 2024 Mons Fusion. All rights reserved. Made with ❤️ in India.",
}


def _get_content(c):
    row = c.execute(
        "SELECT value FROM site_settings WHERE key=?", (CONTENT_KEY,)
    ).fetchone()
    if row:
        try:
            saved = json.loads(row["value"])
            # Merge with defaults so new keys always exist
            return {**DEFAULTS, **saved}
        except Exception:
            pass
    return dict(DEFAULTS)


@bp.route("/api/admin/site-content", methods=["GET"])
@require_admin
def get_content():
    c = db()
    content = _get_content(c)
    c.close()
    return jsonify(content)


@bp.route("/api/admin/site-content", methods=["PUT"])
@require_admin
def update_content():
    d = request.json or {}
    c = db()
    current = _get_content(c)
    # Only update known keys
    for key in DEFAULTS:
        if key in d:
            current[key] = str(d[key]).strip()
    c.execute(
        "INSERT OR REPLACE INTO site_settings(key,value) VALUES(?,?)",
        (CONTENT_KEY, json.dumps(current)),
    )
    c.commit()
    c.close()
    return jsonify({"success": True, "content": current})

# ── FESTIVAL SECTION ─────────────────────────────────────────
FEST_KEY = "festival_settings"

FEST_DEFAULTS = {
    "name":         "Festival Special Gifts",
    "emoji":        "✨🎆✨",
    "offer_text":   "",
    "sub_text":     "Birthdays · Anniversaries · Diwali · Christmas · Valentine's Day",
    "active":       False,
    "product_ids":  [],
    "banner_image": "",
}


def _get_festival(c):
    row = c.execute(
        "SELECT value FROM site_settings WHERE key=?", (FEST_KEY,)
    ).fetchone()
    if row:
        try:
            saved = json.loads(row["value"])
            result = {**FEST_DEFAULTS, **saved}
            # Fetch full product details for stored IDs
            if result["product_ids"]:
                placeholders = ",".join("?" * len(result["product_ids"]))
                result["products"] = [
                    dict(p) for p in c.execute(
                        f"SELECT id,name,price,discount,image_url,category,is_best_seller,is_most_liked "
                        f"FROM products WHERE id IN ({placeholders}) AND active=1",
                        result["product_ids"]
                    ).fetchall()
                ]
            else:
                result["products"] = []
            return result
        except Exception:
            pass
    return {**FEST_DEFAULTS, "products": []}


@bp.route("/api/admin/festival", methods=["GET"])
@require_admin
def get_festival():
    c = db()
    data = _get_festival(c)
    c.close()
    return jsonify(data)


@bp.route("/api/admin/festival", methods=["PUT"])
@require_admin
def update_festival():
    d = request.json or {}
    c = db()
    current = _get_festival(c)
    # Update only provided keys
    for key in ["name", "emoji", "offer_text", "sub_text", "active", "banner_image"]:
        if key in d:
            current[key] = d[key]
    if "product_ids" in d:
        current["product_ids"] = [int(i) for i in d["product_ids"] if str(i).isdigit() or isinstance(i, int)]
    # Strip products list before saving (we re-fetch on load)
    to_save = {k: v for k, v in current.items() if k != "products"}
    c.execute(
        "INSERT OR REPLACE INTO site_settings(key,value) VALUES(?,?)",
        (FEST_KEY, json.dumps(to_save)),
    )
    c.commit()
    # Return full data with product details
    data = _get_festival(c)
    c.close()
    return jsonify({"success": True, "festival": data})