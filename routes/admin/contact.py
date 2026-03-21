from flask import Blueprint, jsonify, request

from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_contact", __name__)


@bp.route("/api/admin/contact-messages", methods=["GET"])
@require_admin
def get_contact_messages():
    c = db()
    msgs = [
        dict(m)
        for m in c.execute(
            "SELECT * FROM contact_messages ORDER BY created_at DESC"
        ).fetchall()
    ]
    c.close()
    return jsonify(msgs)


@bp.route("/api/admin/contact-messages/<int:mid>/read", methods=["POST"])
@require_admin
def mark_read(mid):
    c = db()
    c.execute("UPDATE contact_messages SET is_read=1 WHERE id=?", (mid,))
    c.commit()
    c.close()
    return jsonify({"success": True})


@bp.route("/api/admin/contact-messages/<int:mid>", methods=["DELETE"])
@require_admin
def delete_message(mid):
    c = db()
    c.execute("DELETE FROM contact_messages WHERE id=?", (mid,))
    c.commit()
    c.close()
    return jsonify({"success": True})