import json
from flask import Blueprint, jsonify, request
from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_categories", __name__)

CATEGORIES_KEY = "product_categories"


def _get_categories(c):
    row = c.execute(
        "SELECT value FROM site_settings WHERE key=?", (CATEGORIES_KEY,)
    ).fetchone()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            pass
    # Fallback: derive from existing products
    cats = [
        r[0]
        for r in c.execute(
            "SELECT DISTINCT category FROM products WHERE active=1 AND category!='' ORDER BY category"
        ).fetchall()
    ]
    # Persist them so they exist for future edits
    c.execute(
        "INSERT OR REPLACE INTO site_settings(key,value) VALUES(?,?)",
        (CATEGORIES_KEY, json.dumps(cats)),
    )
    c.commit()
    return cats


@bp.route("/api/admin/categories", methods=["GET"])
@require_admin
def get_categories():
    c = db()
    cats = _get_categories(c)
    c.close()
    return jsonify(cats)


@bp.route("/api/admin/categories", methods=["POST"])
@require_admin
def add_category():
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Category name is required"}), 400
    c = db()
    cats = _get_categories(c)
    if name in cats:
        c.close()
        return jsonify({"error": "Category already exists"}), 400
    cats.append(name)
    cats.sort()
    c.execute(
        "INSERT OR REPLACE INTO site_settings(key,value) VALUES(?,?)",
        (CATEGORIES_KEY, json.dumps(cats)),
    )
    c.commit()
    c.close()
    return jsonify({"success": True, "categories": cats})


@bp.route("/api/admin/categories/<string:name>", methods=["DELETE"])
@require_admin
def delete_category(name):
    c = db()
    cats = _get_categories(c)
    if name not in cats:
        c.close()
        return jsonify({"error": "Category not found"}), 404
    cats = [cat for cat in cats if cat != name]
    c.execute(
        "INSERT OR REPLACE INTO site_settings(key,value) VALUES(?,?)",
        (CATEGORIES_KEY, json.dumps(cats)),
    )
    c.commit()
    c.close()
    return jsonify({"success": True, "categories": cats})