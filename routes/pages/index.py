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
