from routes.customer.auth import bp as auth_bp
from routes.customer.products import bp as products_bp
from routes.customer.cart import bp as cart_bp
from routes.customer.wishlist import bp as wishlist_bp
from routes.customer.coupon import bp as coupon_bp
from routes.customer.orders import bp as orders_bp
from routes.customer.reviews import bp as reviews_bp

customer_blueprints = [
    auth_bp,
    products_bp,
    cart_bp,
    wishlist_bp,
    coupon_bp,
    orders_bp,
    reviews_bp,
]

__all__ = ["customer_blueprints"]
