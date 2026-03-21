import re
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
    if not re.fullmatch(r"[A-Za-z]+(?:[ '][A-Za-z]+)*", nm):
        return jsonify({"error": "Name can only contain letters and spaces"}), 400
    import re as _re
    if not _re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,10}$', em):
        return jsonify({"error": "Invalid email address"}), 400
    if len(pw) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if ph and (not ph.isdigit() or len(ph) != 10):
        return jsonify({"error": "Phone must be 10 digits"}), 400
    if ph and not re.match(r"^[6-9][0-9]{9}$", ph):
        return jsonify({"error": "Phone must be 10 digits and start with 6-9"}), 400
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
        "SELECT id,name,email,phone,created_at,"
        "address_house,address_area,address_city,address_state,address_pin,address_category "
        "FROM users WHERE id=?",
        (session["user_id"],),
    ).fetchone()
    c.close()
    return jsonify(dict(u)) if u else (jsonify({"error": "Not found"}), 404)


@bp.route("/api/profile", methods=["PUT"])
@require_user
def api_profile_update():
    d = request.json
    nm    = d.get("name", "").strip()
    ph    = d.get("phone", "").strip()
    house = d.get("address_house", "").strip()
    area  = d.get("address_area", "").strip()
    city  = d.get("address_city", "").strip()
    state = d.get("address_state", "").strip()
    pin   = d.get("address_pin", "").strip()
    category = d.get("address_category", "").strip()
    if len(nm) < 3:
        return jsonify({"error": "Name min 3 chars"}), 400
    c = db()
    c.execute(
        "UPDATE users SET name=?,phone=?,address_house=?,address_area=?,"
        "address_city=?,address_state=?,address_pin=?,address_category=? WHERE id=?",
        (nm, ph, house, area, city, state, pin, category, session["user_id"]),
    )
    c.commit()
    c.close()
    session["user_name"] = nm
    return jsonify({"success": True})


# ── FORGOT PASSWORD ──────────────────────────────────────

import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# Configure these in production via environment variables
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = ""          # e.g. yourapp@gmail.com
SMTP_PASSWORD = ""          # App password (not your Gmail password)
FROM_EMAIL    = "noreply@monsfusion.com"
SITE_URL      = "http://localhost:5000"


def _send_reset_email(to_email, token, user_name):
    """Send the reset link via SMTP. Prints link to console if SMTP not configured."""
    reset_link = f"{SITE_URL}/#reset-password?token={token}"
    body = f"""Hi {user_name},

We received a request to reset your MonsFusion password.

Click the link below to reset it (valid for 1 hour):
{reset_link}

If you didn't request this, you can safely ignore this email.

— Team MonsFusion
"""
    if not SMTP_USER:
        # Dev mode: print to console instead of sending
        print(f"\n{'='*60}")
        print(f"  PASSWORD RESET LINK (dev mode — SMTP not configured)")
        print(f"  To: {to_email}")
        print(f"  Link: {reset_link}")
        print(f"{'='*60}\n")
        return

    msg = MIMEText(body)
    msg["Subject"] = "Reset your MonsFusion password"
    msg["From"]    = FROM_EMAIL
    msg["To"]      = to_email
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
        s.sendmail(FROM_EMAIL, to_email, msg.as_string())


@bp.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    d    = request.json or {}
    em   = d.get("email", "").strip().lower()
    if not em:
        return jsonify({"error": "Email is required"}), 400

    c = db()
    user = c.execute("SELECT * FROM users WHERE email=?", (em,)).fetchone()

    # Always return success to avoid email enumeration
    if not user:
        c.close()
        return jsonify({"success": True})

    # Invalidate any existing tokens for this user
    c.execute("UPDATE password_reset_tokens SET used=1 WHERE user_id=?", (user["id"],))

    token      = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO password_reset_tokens(user_id, token, expires_at) VALUES(?,?,?)",
        (user["id"], token, expires_at),
    )
    c.commit()
    c.close()

    try:
        _send_reset_email(em, token, user["name"])
    except Exception as e:
        print(f"Email send error: {e}")

    return jsonify({"success": True})


@bp.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    d     = request.json or {}
    token = d.get("token", "").strip()
    pw    = d.get("password", "")

    if not token:
        return jsonify({"error": "Invalid reset link"}), 400
    if len(pw) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    c   = db()
    row = c.execute(
        "SELECT * FROM password_reset_tokens WHERE token=? AND used=0",
        (token,),
    ).fetchone()

    if not row:
        c.close()
        return jsonify({"error": "Invalid or already used reset link"}), 400

    # Check expiry
    expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() > expires_at:
        c.close()
        return jsonify({"error": "This reset link has expired. Please request a new one."}), 400

    # Update password and mark token used
    c.execute("UPDATE users SET password=? WHERE id=?", (hp(pw), row["user_id"]))
    c.execute("UPDATE password_reset_tokens SET used=1 WHERE id=?", (row["id"],))
    c.commit()
    c.close()
    return jsonify({"success": True})