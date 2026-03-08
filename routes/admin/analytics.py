from datetime import datetime, timedelta

from flask import Blueprint, jsonify

from auth_utils import require_admin
from db_utils import db

bp = Blueprint("admin_analytics", __name__)


@bp.route("/api/admin/analytics")
@require_admin
def admin_analytics():
    c = db()

    total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue = c.execute(
        "SELECT COALESCE(SUM(total_price),0) FROM orders WHERE status!='cancelled'"
    ).fetchone()[0]
    total_customers = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_products = c.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]

    monthly = []
    for i in range(5, -1, -1):
        d_start = (datetime.now().replace(day=1) - timedelta(days=30 * i))
        month_str = d_start.strftime("%Y-%m")
        month_name = d_start.strftime("%b %Y")
        rev = c.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM orders WHERE created_at LIKE ? AND status!='cancelled'",
            (month_str + "%",),
        ).fetchone()[0]
        cnt = c.execute(
            "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",
            (month_str + "%",),
        ).fetchone()[0]
        monthly.append({"month": month_name, "revenue": round(rev, 2), "orders": cnt})

    best_products = c.execute(
        """
        SELECT p.name, p.category, p.image_url, SUM(oi.quantity) as total_sold, SUM(oi.quantity*oi.price) as revenue
        FROM order_items oi JOIN products p ON oi.product_id=p.id
        GROUP BY oi.product_id ORDER BY total_sold DESC LIMIT 5
    """
    ).fetchall()

    cat_sales = c.execute(
        """
        SELECT p.category, COUNT(oi.id) as orders, SUM(oi.quantity*oi.price) as revenue
        FROM order_items oi JOIN products p ON oi.product_id=p.id
        GROUP BY p.category ORDER BY revenue DESC
    """
    ).fetchall()

    status_dist = c.execute(
        "SELECT status, COUNT(*) as count FROM orders GROUP BY status"
    ).fetchall()

    recent = c.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 8"
    ).fetchall()

    avg_order = c.execute(
        "SELECT COALESCE(AVG(total_price),0) FROM orders WHERE status!='cancelled'"
    ).fetchone()[0]

    total_profit = total_revenue * 0.4

    c.close()
    return jsonify(
        {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_customers": total_customers,
            "total_products": total_products,
            "total_profit": round(total_profit, 2),
            "avg_order_value": round(avg_order, 2),
            "monthly": monthly,
            "best_products": [dict(r) for r in best_products],
            "category_sales": [dict(r) for r in cat_sales],
            "status_distribution": [dict(r) for r in status_dist],
            "recent_orders": [dict(r) for r in recent],
        }
    )


@bp.route("/api/admin/customers", methods=["GET"])
@require_admin
def admin_customers():
    c = db()
    users = c.execute(
        "SELECT id,name,email,phone,created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    result = []
    for u in users:
        ud = dict(u)
        ud["order_count"] = c.execute(
            "SELECT COUNT(*) FROM orders WHERE user_id=?", (u["id"],)
        ).fetchone()[0]
        ud["total_spent"] = c.execute(
            "SELECT COALESCE(SUM(total_price),0) FROM orders WHERE user_id=? AND status!='cancelled'",
            (u["id"],),
        ).fetchone()[0]
        result.append(ud)
    c.close()
    return jsonify(result)
