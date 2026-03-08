"""
╔══════════════════════════════════════════════════════════════════╗
║   MONS FUSION — Full Stack App (Customer + Admin)                ║
║   Run: python app.py → http://localhost:5000                     ║
║   Customer:  http://localhost:5000/                              ║
║   Admin:     http://localhost:5000/admin                         ║
╠══════════════════════════════════════════════════════════════════╣
║   DEMO CREDENTIALS                                               ║
║   Customer: demo@monsfusion.com / Demo@1234                      ║
║   Admin:    ParabStore / Parab@29                                ║
╚══════════════════════════════════════════════════════════════════╝
"""

from flask import Flask

from db_utils import init_db




















from routes import pages_bp, customer_blueprints, admin_blueprints

app = Flask(__name__, static_folder=".")
app.secret_key = "mf_v2_ultra_secret_2024"
app.jinja_env.comment_start_string = "{##"
app.jinja_env.comment_end_string = "##}"

app.register_blueprint(pages_bp)
for bp in customer_blueprints:
    app.register_blueprint(bp)
for bp in admin_blueprints:
    app.register_blueprint(bp)


if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 62)
    print("  🎁  MONS FUSION — Full Stack App Ready!")
    print("=" * 62)
    print("  🌐  Customer:  http://localhost:5000/")
    print("  🔐  Admin:     http://localhost:5000/admin")
    print("  📦  DB:        mf_v2.db (auto-created)")
    print()
    print("  👤  DEMO LOGIN (Customer):")
    print("      Email:    demo@monsfusion.com")
    print("      Password: Demo@1234")
    print()
    print("  🔑  ADMIN LOGIN:")
    print("      Username: ParabStore")
    print("      Password: Parab@29")
    print("=" * 62 + "\n")
    app.run(debug=True, port=5000)
