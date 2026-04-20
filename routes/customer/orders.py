from flask import Blueprint, jsonify, request, session
import os
import requests as http_requests

from auth_utils import require_user
from db_utils import db, gen_oid

bp = Blueprint("customer_orders", __name__)

DELIVERY_FEE = 80
FREE_DELIVERY_THRESHOLD = 999
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
FROM_EMAIL    = "noreply@brevo.com"
SITE_NAME     = "MonsFusion"


def _send_order_confirmation(to_email, customer_name, order_id, items, subtotal, delivery_fee, total, payment_method):
    """Send order confirmation email via Brevo. Prints to console if API key not set."""
    if not BREVO_API_KEY:
        print(f"\n{'='*60}")
        print(f"  ORDER CONFIRMATION (dev mode — Brevo not configured)")
        print(f"  To: {to_email}  |  Order: {order_id}  |  Total: ₹{total}")
        print(f"{'='*60}\n")
        return

    items_html = "".join(
        f"<tr><td style='padding:8px 0;border-bottom:1px solid #eee'>{i['name']}</td>"
        f"<td style='padding:8px;text-align:center'>{i['quantity']}</td>"
        f"<td style='padding:8px;text-align:right'>₹{round(i['price']*i['quantity'])}</td></tr>"
        for i in items
    )
    delivery_text = "🎉 FREE" if delivery_fee == 0 else f"₹{delivery_fee}"

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333">
      <div style="background:linear-gradient(135deg,#ff4f8b,#e3a7c4);padding:30px;text-align:center;border-radius:12px 12px 0 0">
        <h1 style="color:white;margin:0;font-size:1.6rem">🎁 Order Confirmed!</h1>
        <p style="color:rgba(255,255,255,.9);margin:8px 0 0">Thank you for shopping with {SITE_NAME}</p>
      </div>
      <div style="background:#f9f9f9;padding:24px;border-radius:0 0 12px 12px">
        <p>Hi <strong>{customer_name}</strong>,</p>
        <p>Your order has been placed successfully. We'll start preparing it right away!</p>
        <div style="background:white;border-radius:8px;padding:16px;margin:16px 0;border:1px solid #eee">
          <p style="margin:0 0 12px;font-weight:700;color:#ff4f8b">Order ID: {order_id}</p>
          <table width="100%" cellpadding="0" cellspacing="0">
            <thead><tr style="background:#f5f5f5">
              <th style="padding:8px;text-align:left;font-size:.85rem">Item</th>
              <th style="padding:8px;text-align:center;font-size:.85rem">Qty</th>
              <th style="padding:8px;text-align:right;font-size:.85rem">Amount</th>
            </tr></thead>
            <tbody>{items_html}</tbody>
          </table>
          <div style="margin-top:12px;padding-top:12px;border-top:2px solid #eee">
            <div style="display:flex;justify-content:space-between;color:#666;margin:4px 0"><span>Subtotal</span><span>₹{round(subtotal)}</span></div>
            <div style="display:flex;justify-content:space-between;color:#666;margin:4px 0"><span>Delivery</span><span>{delivery_text}</span></div>
            <div style="display:flex;justify-content:space-between;font-weight:700;font-size:1.1rem;margin-top:8px"><span>Total Paid</span><span style="color:#ff4f8b">₹{total}</span></div>
          </div>
        </div>
        <p style="color:#666;font-size:.85rem">💳 Payment method: <strong>{payment_method}</strong></p>
        <p style="color:#666;font-size:.85rem">📦 Expected delivery: <strong>3–5 business days</strong></p>
        <p style="color:#999;font-size:.8rem;margin-top:24px">— Team {SITE_NAME}</p>
      </div>
    </body></html>
    """
    try:
        response = http_requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": BREVO_API_KEY, "content-type": "application/json"},
            json={
                "sender": {"name": SITE_NAME, "email": FROM_EMAIL},
                "to": [{"email": to_email, "name": customer_name}],
                "subject": f"✅ Order Confirmed — {order_id}",
                "htmlContent": html,
            },
            timeout=10,
        )
        response.raise_for_status()
        print(f"✅ Order confirmation sent to {to_email}")
    except Exception as e:
        print(f"❌ Order confirmation email failed: {e}")




def compute_delivery_fee(subtotal: float) -> int:
    """Return delivery fee based on subtotal. FREE if subtotal > ₹999."""
    return 0 if subtotal > FREE_DELIVERY_THRESHOLD else DELIVERY_FEE


@bp.route("/api/cart/delivery")
def api_cart_delivery():
    """Return delivery fee and final total for current cart."""
    uid = session.get("user_id")
    if not uid:
        return jsonify({"delivery_fee": DELIVERY_FEE, "subtotal": 0, "total": DELIVERY_FEE})
    c = db()
    items = c.execute(
        "SELECT p.price, p.discount, c.quantity "
        "FROM cart c JOIN products p ON c.product_id=p.id WHERE c.user_id=?",
        (uid,),
    ).fetchall()
    c.close()
    subtotal = sum(
        round(i["price"] * (1 - (i["discount"] or 0) / 100), 2) * i["quantity"]
        for i in items
    )
    subtotal = round(subtotal, 2)
    delivery_fee = compute_delivery_fee(subtotal)
    return jsonify({
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": round(subtotal + delivery_fee, 2),
        "free_delivery": delivery_fee == 0,
    })


@bp.route("/api/orders", methods=["POST"])
def api_orders_post():
    d = request.json
    uid = session.get("user_id")
    nm = d.get("customer_name", "").strip()
    ph = d.get("phone", "").strip()
    if len(nm) < 3:
        return jsonify({"error": "Name must be at least 3 characters"}), 400
    if not ph.isdigit() or len(ph) != 10:
        return jsonify({"error": "Phone must be 10 digits"}), 400

    # ── Compute delivery fee on the backend (never trust frontend) ──
    items = d.get("items", [])
    subtotal = round(sum(item["price"] * item["quantity"] for item in items), 2)
    delivery_fee = compute_delivery_fee(subtotal)
    final_total = round(subtotal + delivery_fee, 2)

    order_id = gen_oid()
    c = db()
    while c.execute("SELECT id FROM orders WHERE order_id=?", (order_id,)).fetchone():
        order_id = gen_oid()
    c.execute(
        "INSERT INTO orders(user_id,order_id,total_price,delivery_fee,address,customer_name,phone,email,payment_method,coupon_code,status) "
        "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            uid,
            order_id,
            final_total,
            delivery_fee,
            d.get("address"),
            nm,
            ph,
            d.get("email"),
            d.get("payment_method"),
            d.get("coupon_code"),
            "pending",
        ),
    )
    for item in items:
        c.execute(
            "INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )
    if uid:
        c.execute("DELETE FROM cart WHERE user_id=?", (uid,))
    c.commit()
    c.close()
    # Send order confirmation email (non-blocking)
    customer_email = d.get("email")
    customer_name  = nm
    if customer_email:
        try:
            _send_order_confirmation(
                to_email=customer_email,
                customer_name=customer_name,
                order_id=order_id,
                items=items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=final_total,
                payment_method=d.get("payment_method", ""),
            )
        except Exception as e:
            print(f"Order email error: {e}")

    return jsonify({
        "success": True,
        "order_id": order_id,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": final_total,
    })


@bp.route("/api/orders/user")
@require_user
def api_orders_user():
    uid = session["user_id"]
    c = db()
    ords = [
        dict(o)
        for o in c.execute(
            "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (uid,)
        ).fetchall()
    ]
    for o in ords:
        items = c.execute(
            "SELECT oi.*,p.name,p.image_url FROM order_items oi "
            "JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?",
            (o["order_id"],),
        ).fetchall()
        o["items"] = [dict(i) for i in items]
    c.close()
    return jsonify(ords)