import json
import os
import uuid

from flask import Blueprint, jsonify, request, current_app

from auth_utils import require_admin
from db_utils import db

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', 'products')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

bp = Blueprint("admin_products", __name__)


@bp.route("/api/admin/products", methods=["GET"])
@require_admin
def admin_get_products():
    c = db()
    rows = [dict(r) for r in c.execute("SELECT * FROM products ORDER BY id DESC").fetchall()]
    c.close()
    for r in rows:
        try:
            r["images"] = json.loads(r["images"]) if r["images"] else [r["image_url"]]
        except Exception:
            r["images"] = [r["image_url"]]
    return jsonify(rows)


@bp.route("/api/admin/products", methods=["POST"])
@require_admin
def admin_add_product():
    d = request.json
    name = d.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    c = db()
    imgs = d.get("images", [])
    img_url = (
        imgs[0]
        if imgs
        else d.get(
            "image_url", "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500"
        )
    )
    cur = c.execute(
        """INSERT INTO products(name,price,discount,description,category,subcategory,gender_tag,
                 is_best_seller,is_festival_special,is_most_liked,image_url,images,active)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)""",
        (
            name,
            d.get("price", 0),
            d.get("discount", 0),
            d.get("description", ""),
            d.get("category", ""),
            d.get("subcategory", ""),
            d.get("gender_tag", ""),
            1 if d.get("is_best_seller") else 0,
            1 if d.get("is_festival_special") else 0,
            1 if d.get("is_most_liked") else 0,
            img_url,
            json.dumps(imgs) if imgs else json.dumps([img_url]),
        ),
    )
    c.commit()
    pid = cur.lastrowid
    c.close()
    return jsonify({"success": True, "id": pid})


@bp.route("/api/admin/products/<int:pid>", methods=["PUT"])
@require_admin
def admin_update_product(pid):
    d = request.json
    c = db()
    imgs = d.get("images", [])
    img_url = imgs[0] if imgs else d.get("image_url", "")
    c.execute(
        """UPDATE products SET name=?,price=?,discount=?,description=?,category=?,subcategory=?,
                 gender_tag=?,is_best_seller=?,is_festival_special=?,is_most_liked=?,
                 image_url=?,images=?,active=? WHERE id=?""",
        (
            d.get("name"),
            d.get("price", 0),
            d.get("discount", 0),
            d.get("description", ""),
            d.get("category", ""),
            d.get("subcategory", ""),
            d.get("gender_tag", ""),
            1 if d.get("is_best_seller") else 0,
            1 if d.get("is_festival_special") else 0,
            1 if d.get("is_most_liked") else 0,
            img_url,
            json.dumps(imgs) if imgs else json.dumps([img_url]),
            1 if d.get("active", True) else 0,
            pid,
        ),
    )
    c.commit()
    c.close()
    return jsonify({"success": True})


@bp.route("/api/admin/products/<int:pid>", methods=["DELETE"])
@require_admin
def admin_delete_product(pid):
    c = db()
    c.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
    c.commit()
    c.close()
    return jsonify({"success": True})


@bp.route("/api/admin/upload-image", methods=["POST"])
@require_admin
def admin_upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use PNG, JPG, GIF or WebP"}), 400

    # Limit file size to 5MB
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({"error": "File too large. Maximum size is 5MB"}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    url = f"/static/uploads/products/{filename}"
    return jsonify({"success": True, "url": url})