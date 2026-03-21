from routes.admin.auth import bp as auth_bp
from routes.admin.products import bp as products_bp
from routes.admin.coupons import bp as coupons_bp
from routes.admin.orders import bp as orders_bp
from routes.admin.analytics import bp as analytics_bp
from routes.admin.contact import bp as contact_bp
from routes.admin.categories import bp as categories_bp
from routes.admin.settings import bp as settings_bp

admin_blueprints = [
    auth_bp,
    products_bp,
    coupons_bp,
    orders_bp,
    analytics_bp,
    contact_bp,
    categories_bp,
    settings_bp,
]

__all__ = ["admin_blueprints"]