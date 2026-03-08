from flask import Blueprint, jsonify, request, session

from auth_utils import require_user
from db_utils import db, hp

bp = Blueprint("customer_auth", __name__)


@bp.route("/api/session")
def api_session():
    uid = session.get("user_id")
    return jsonify(
        {
            "logged_in": bool(uid),
            "user_id": uid,
            "user_name": session.get("user_name", ""),
        }
    )


@bp.route("/api/signup", methods=["POST"])
def api_signup():
    d = request.json
    nm = d.get("name", "").strip()
    em = d.get("email", "").strip().lower()
    pw = d.get("password", "")
    ph = d.get("phone", "").strip()
    if len(nm) < 3:
        return jsonify({"error": "Name must be at least 3 characters"}), 400
    if "@" not in em or "." not in em:
        return jsonify({"error": "Invalid email"}), 400
    if len(pw) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if ph and (not ph.isdigit() or len(ph) != 10):
        return jsonify({"error": "Phone must be 10 digits"}), 400
    c = db()
    try:
        c.execute(
            "INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)",
            (nm, em, hp(pw), ph),
        )
        c.commit()
        u = c.execute("SELECT * FROM users WHERE email=?", (em,)).fetchone()
        session["user_id"] = u["id"]
        session["user_name"] = u["name"]
        return jsonify(
            {
                "success": True,
                "user": {"id": u["id"], "name": u["name"], "email": u["email"]},
            }
        )
    except Exception:
        return jsonify({"error": "Email already registered"}), 400
    finally:
        c.close()


@bp.route("/api/login", methods=["POST"])
def api_login():
    d = request.json
    em = d.get("email", "").strip().lower()
    pw = d.get("password", "")
    if not em:
        return jsonify({"error": "Email required"}), 400
    if not pw:
        return jsonify({"error": "Password required"}), 400
    c = db()
    u = c.execute(
        "SELECT * FROM users WHERE email=? AND password=?", (em, hp(pw))
    ).fetchone()
    c.close()
    if not u:
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = u["id"]
    session["user_name"] = u["name"]
    return jsonify(
        {
            "success": True,
            "user": {
                "id": u["id"],
                "name": u["name"],
                "email": u["email"],
                "phone": u["phone"],
            },
        }
    )


@bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return jsonify({"success": True})


@bp.route("/api/profile", methods=["GET"])
@require_user
def api_profile():
    c = db()
    u = c.execute(
        "SELECT id,name,email,phone,created_at FROM users WHERE id=?",
        (session["user_id"],),
    ).fetchone()
    c.close()
    return jsonify(dict(u)) if u else (jsonify({"error": "Not found"}), 404)


@bp.route("/api/profile", methods=["PUT"])
@require_user
def api_profile_update():
    d = request.json
    nm = d.get("name", "").strip()
    ph = d.get("phone", "").strip()
    if len(nm) < 3:
        return jsonify({"error": "Name min 3 chars"}), 400
    c = db()
    c.execute(
        "UPDATE users SET name=?,phone=? WHERE id=?",
        (nm, ph, session["user_id"]),
    )
    c.commit()
    c.close()
    session["user_name"] = nm
    return jsonify({"success": True})
