import base64
import binascii
import json

from flask import Blueprint, jsonify, request

from auth_utils import require_admin
from db_utils import db

# ── Allowed MIME types for base64 images ─────────────────────
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
MAX_IMAGE_BYTES    = 5 * 1024 * 1024   # 5 MB per image
MAX_IMAGES         = 10                # max images per product

bp = Blueprint("admin_products", __name__)


def _validate_base64_image(data_url: str) -> bool:
    """
    Validate a base64 data URL.
    Expected format: data:<mime>;base64,<data>
    Returns True if valid mime type, valid base64, and within size limit.
    """
    if not isinstance(data_url, str):
        return False
    if not data_url.startswith("data:"):
        return False
    try:
        # Split header from base64 payload
        header, encoded = data_url.split(",", 1)
        # header = "data:image/jpeg;base64"
        mime = header.split(":")[1].split(";")[0]
        if mime not in ALLOWED_MIME_TYPES:
            return False
        # Validate it is actual base64 and check decoded size
        decoded = base64.b64decode(encoded, validate=True)
        if len(decoded) > MAX_IMAGE_BYTES:
            return False
    except (ValueError, binascii.Error, IndexError):
        return False
    return True


def _sanitize_images(images: list) -> list:
    """
    Filter image list: keep only valid base64 data URLs, cap at MAX_IMAGES.
    """
    if not isinstance(images, list):
        return []
    valid = [img for img in images if _validate_base64_image(img)]
    return valid[:MAX_IMAGES]


# ─────────────────────────────────────────────────────────────
# GET  /api/admin/products
# ─────────────────────────────────────────────────────────────
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


# ─────────────────────────────────────────────────────────────
# POST  /api/admin/products
# Body: JSON  { name, price, discount, description, category,
#               subcategory, gender_tag, is_best_seller,
#               is_festival_special, is_most_liked,
#               images: ["data:image/jpeg;base64,...", ...] }
# ─────────────────────────────────────────────────────────────
@bp.route("/api/admin/products", methods=["POST"])
@require_admin
def admin_add_product():
    d = request.get_json() or {}

    name = d.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400

    # Validate and sanitise incoming base64 images
    raw_images = d.get("images", [])
    imgs       = _sanitize_images(raw_images)

    if not imgs:
        return jsonify({"error": "At least one valid image is required"}), 400

    # First image is the primary thumbnail
    img_url = imgs[0]

    c = db()
    cur = c.execute(
        """INSERT INTO products(name, price, discount, min_quantity, description, category, subcategory,
                 gender_tag, is_best_seller, is_festival_special, is_most_liked,
                 image_url, images, active)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
        (
            name,
            d.get("price", 0),
            d.get("discount", 0),
            d.get("min_quantity", 1),
            d.get("description", ""),
            d.get("category", ""),
            d.get("subcategory", ""),
            d.get("gender_tag", ""),
            1 if d.get("is_best_seller") else 0,
            1 if d.get("is_festival_special") else 0,
            1 if d.get("is_most_liked") else 0,
            img_url,
            json.dumps(imgs),
        ),
    )
    c.commit()
    pid = cur.lastrowid
    c.close()
    return jsonify({"success": True, "id": pid})


# ─────────────────────────────────────────────────────────────
# PUT  /api/admin/products/<pid>
# ─────────────────────────────────────────────────────────────
@bp.route("/api/admin/products/<int:pid>", methods=["PUT"])
@require_admin
def admin_update_product(pid):
    d = request.get_json() or {}

    raw_images = d.get("images", [])
    imgs       = _sanitize_images(raw_images)

    # If caller passed no valid images, keep existing ones from DB
    if not imgs:
        c = db()
        row = c.execute("SELECT image_url, images FROM products WHERE id=?", (pid,)).fetchone()
        c.close()
        if row:
            try:
                imgs = json.loads(row["images"]) if row["images"] else [row["image_url"]]
            except Exception:
                imgs = [row["image_url"]]

    img_url = imgs[0] if imgs else ""

    c = db()
    c.execute(
        """UPDATE products
           SET name=?, price=?, discount=?, min_quantity=?, description=?, category=?, subcategory=?,
               gender_tag=?, is_best_seller=?, is_festival_special=?, is_most_liked=?,
               image_url=?, images=?, active=?
           WHERE id=?""",
        (
            d.get("name", ""),
            d.get("price", 0),
            d.get("discount", 0),
            d.get("min_quantity", 1),
            d.get("description", ""),
            d.get("category", ""),
            d.get("subcategory", ""),
            d.get("gender_tag", ""),
            1 if d.get("is_best_seller") else 0,
            1 if d.get("is_festival_special") else 0,
            1 if d.get("is_most_liked") else 0,
            img_url,
            json.dumps(imgs),
            1 if d.get("active", True) else 0,
            pid,
        ),
    )
    c.commit()
    c.close()
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────
# DELETE  /api/admin/products/<pid>   (soft delete)
# ─────────────────────────────────────────────────────────────
@bp.route("/api/admin/products/<int:pid>", methods=["DELETE"])
@require_admin
def admin_delete_product(pid):
    c = db()
    c.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
    c.commit()
    c.close()
    return jsonify({"success": True})


# ─────────────────────────────────────────────────────────────
# POST  /api/admin/upload-image
# Body: JSON  { "file": "data:image/jpeg;base64,..." }
# Returns the validated data URL back so the frontend can
# collect multiple images before submitting the product form.
# ─────────────────────────────────────────────────────────────
@bp.route("/api/admin/upload-image", methods=["POST"])
@require_admin
def admin_upload_image():
    d        = request.get_json() or {}
    data_url = d.get("file", "")

    if not data_url:
        return jsonify({"error": "No file provided"}), 400

    if not _validate_base64_image(data_url):
        return jsonify({
            "error": "Invalid image. Use PNG, JPG, GIF or WebP under 5 MB."
        }), 400

    # No filesystem write needed — return the data URL directly.
    # The frontend accumulates these and sends them in the images[] array
    # when creating / updating a product.
    return jsonify({"success": True, "url": data_url})
