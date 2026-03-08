from flask import Blueprint, jsonify, request, session

from auth_utils import ADMIN_PASS, ADMIN_USER

bp = Blueprint("admin_auth", __name__)


@bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    d = request.json
    if d.get("username") == ADMIN_USER and d.get("password") == ADMIN_PASS:
        session["admin_logged_in"] = True
        session["admin_name"] = ADMIN_USER
        return jsonify({"success": True, "admin": ADMIN_USER})
    return jsonify({"error": "Invalid admin credentials"}), 401


@bp.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_name", None)
    return jsonify({"success": True})


@bp.route("/api/admin/session")
def admin_session():
    return jsonify(
        {
            "logged_in": bool(session.get("admin_logged_in")),
            "admin": session.get("admin_name", ""),
        }
    )
