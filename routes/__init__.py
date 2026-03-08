"""Route blueprints by role: pages, customer, admin."""

from routes.pages import pages_bp
from routes.customer import customer_blueprints
from routes.admin import admin_blueprints

__all__ = ["pages_bp", "customer_blueprints", "admin_blueprints"]
