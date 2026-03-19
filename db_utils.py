import sqlite3
import hashlib
import json
import random
from datetime import datetime, timedelta

DB = "mf_v2.db"


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, phone TEXT,
        created_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, price REAL NOT NULL,
        discount INTEGER DEFAULT 0, rating REAL DEFAULT 4.0,
        description TEXT, category TEXT, subcategory TEXT,
        gender_tag TEXT, likes INTEGER DEFAULT 0,
        is_best_seller INTEGER DEFAULT 0,
        is_festival_special INTEGER DEFAULT 0,
        is_most_liked INTEGER DEFAULT 0,
        image_url TEXT, images TEXT, active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, order_id TEXT UNIQUE,
        total_price REAL, status TEXT DEFAULT 'pending',
        address TEXT, customer_name TEXT, phone TEXT,
        email TEXT, payment_method TEXT, coupon_code TEXT,
        created_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS order_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT, product_id INTEGER,
        quantity INTEGER, price REAL
    );
    CREATE TABLE IF NOT EXISTS reviews(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER, user_id INTEGER, user_name TEXT,
        rating INTEGER, comment TEXT, images TEXT,
        created_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS wishlist(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS cart(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product_id INTEGER, quantity INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS coupons(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE, discount_type TEXT,
        discount_value REAL, free_delivery INTEGER DEFAULT 0,
        expiry TEXT, active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS site_settings(
        key TEXT PRIMARY KEY, value TEXT,
        updated_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS contact_messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT NOT NULL,
        subject TEXT, message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT(datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS password_reset_tokens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TEXT NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TEXT DEFAULT(datetime('now'))
    );
    """)
    # Migrate existing reviews table — add images column if missing
    try:
        c.execute("ALTER TABLE reviews ADD COLUMN images TEXT")
        c.commit()
    except Exception:
        pass  # Column already exists

    # Migrate contact_messages table — add phone column if missing
    try:
        c.execute("ALTER TABLE contact_messages ADD COLUMN phone TEXT")
        c.commit()
    except Exception:
        pass  # Column already exists

    # Migrate users table — add address columns if missing
    for col in ['address_house TEXT', 'address_area TEXT', 'address_city TEXT',
                'address_state TEXT', 'address_pin TEXT', 'address_category TEXT']:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col}")
            c.commit()
        except Exception:
            pass  # Column already exists

    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        _seed_products(c)
    if not c.execute("SELECT COUNT(*) FROM coupons").fetchone()[0]:
        _seed_coupons(c)
    if not c.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        _seed_users(c)
    if not c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]:
        _seed_orders(c)
    c.commit()
    c.close()


def _seed_products(c):
    P = [
      ("Vintage Polaroid Set of 10",299,20,4.8,"Beautiful set of 10 custom polaroid prints with vintage borders. Perfect for gifting memories.","Polaroids","polaroid-set","her",245,1,1,0,"https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500",'["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500","https://images.unsplash.com/photo-1544568100-847a948585b9?w=500"]'),
      ("Custom Polaroid Strip",199,10,4.6,"3 polaroid strips with your favourite memories.","Polaroids","strip","friends",189,1,0,0,"https://images.unsplash.com/photo-1544568100-847a948585b9?w=500",'["https://images.unsplash.com/photo-1544568100-847a948585b9?w=500"]'),
      ("Aesthetic Polaroid Wall",449,15,4.9,"20 custom polaroids + string lights.","Polaroids","wall","her",312,1,1,1,"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",'["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500"]'),
      ("Premium Memory Album",599,25,4.7,"Hardbound premium album with 50 pages.","Albums","photo-album","parents",178,1,1,0,"https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500",'["https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500"]'),
      ("Couple Anniversary Album",799,20,4.9,"Romantic custom album for couples.","Albums","couple","her",267,1,1,1,"https://images.unsplash.com/photo-1519741497674-611481863552?w=500",'["https://images.unsplash.com/photo-1519741497674-611481863552?w=500"]'),
      ("Baby First Year Album",899,10,5.0,"Capture your baby's first year beautifully.","Albums","baby","parents",134,0,0,0,"https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=500",'["https://images.unsplash.com/photo-1555252333-9f8e92e65df9?w=500"]'),
      ("Custom Life Magazine",349,15,4.5,"Create your own magazine with personal photos.","Magazines","A4","friends",198,1,0,0,"https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500",'["https://images.unsplash.com/photo-1532012197267-da84d127e765?w=500"]'),
      ("Birthday Tribute Magazine",399,20,4.7,"Magazine-style birthday tribute.","Magazines","A5","friends",156,0,1,0,"https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500",'["https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500"]'),
      ("Photo Acrylic Keychain",149,0,4.4,"Custom acrylic keychain with your photo.","Keychains","acrylic","friends",423,1,0,1,"https://images.unsplash.com/photo-1601924582970-9238bcb495d9?w=500",'["https://images.unsplash.com/photo-1601924582970-9238bcb495d9?w=500"]'),
      ("Couple Wooden Keychain Pair",199,10,4.6,"Pair of wooden keychains with engraving.","Keychains","wooden","him",312,1,0,0,"https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=500",'["https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=500"]'),
      ("Heart Shape Keychain",129,0,4.3,"Cute heart-shaped photo keychain.","Keychains","heart","her",289,0,0,0,"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",'["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500"]'),
      ("Collage Photo Frame",499,20,4.8,"Collage frame for 6 photos with custom text.","Frames","collage","parents",234,1,1,0,"https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=500",'["https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=500"]'),
      ("LED Glow Photo Frame",699,15,4.9,"Photo frame with warm LED lighting.","Frames","led","her",178,1,1,1,"https://images.unsplash.com/photo-1579762715118-a6f1d4b934f1?w=500",'["https://images.unsplash.com/photo-1579762715118-a6f1d4b934f1?w=500"]'),
      ("Rustic Wooden Frame",349,0,4.5,"Handcrafted wooden frame.","Frames","wooden","parents",145,0,0,0,"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",'["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500"]'),
      ("Custom Photo Magnets Set",99,0,4.2,"Set of 3 custom photo fridge magnets.","Fridge Magnets","photo","friends",567,1,0,1,"https://images.unsplash.com/photo-1583394293214-0b3da7fd7c3f?w=500",'["https://images.unsplash.com/photo-1583394293214-0b3da7fd7c3f?w=500"]'),
      ("Quote Magnets Pack",149,10,4.4,"Set of 5 motivational quote magnets.","Fridge Magnets","quote","her",234,0,0,0,"https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=500",'["https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=500"]'),
      ("Birthday Hamper Deluxe",1299,20,4.9,"Complete birthday hamper package.","Hampers","birthday","her",189,1,1,1,"https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500",'["https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500"]'),
      ("Couple Anniversary Hamper",1599,25,4.8,"Romantic anniversary hamper.","Hampers","anniversary","him",167,1,1,0,"https://images.unsplash.com/photo-1607344645866-009c320b63e0?w=500",'["https://images.unsplash.com/photo-1607344645866-009c320b63e0?w=500"]'),
      ("Friendship Day Hamper",999,15,4.7,"Friendship hamper with polaroids & sweets.","Hampers","friendship","friends",203,0,1,0,"https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500",'["https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500"]'),
      ("LED Photo String Lights",599,10,4.8,"20 photo clips with warm LED lights.","Room Décor","lights","her",456,1,0,1,"https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500",'["https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500"]'),
      ("Custom Name LED Board",799,20,4.7,"Personalised LED name board.","Room Décor","led-board","him",234,1,1,0,"https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=500",'["https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=500"]'),
      ("Photo Collage Wall Art",899,15,4.9,"Large-format photo collage wall art.","Room Décor","wall-art","parents",178,1,1,1,"https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=500",'["https://images.unsplash.com/photo-1513519245088-0e12902e35ca?w=500"]'),
      ("Mini Square Photo Prints",99,0,4.1,"Set of 5 mini square photo prints.","Polaroids","mini","friends",678,0,0,0,"https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500",'["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=500"]'),
      ("Custom Photo Bookmarks",149,0,4.3,"Set of 3 custom photo bookmarks.","Keychains","bookmark","friends",345,0,0,0,"https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500",'["https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=500"]'),
      ("Wooden Photo Calendar",499,0,4.5,"12-month custom wooden calendar.","Room Décor","calendar","parents",134,0,0,0,"https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500",'["https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=500"]'),
    ]
    for p in P:
        c.execute("INSERT INTO products(name,price,discount,rating,description,category,subcategory,gender_tag,likes,is_best_seller,is_festival_special,is_most_liked,image_url,images) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", p)


def _seed_coupons(c):
    coupons = [
        ("WELCOME10","percent",10,0,"2027-12-31"),
        ("FREESHIP","flat",0,1,"2027-12-31"),
        ("SAVE50","flat",50,0,"2027-12-31"),
        ("FEST20","percent",20,0,"2027-12-31"),
    ]
    for cp in coupons:
        c.execute("INSERT INTO coupons(code,discount_type,discount_value,free_delivery,expiry) VALUES(?,?,?,?,?)", cp)


def _seed_users(c):
    c.execute("INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)",
              ("Demo Customer","demo@monsfusion.com",hp("Demo@1234"),"9876543210"))
    extras = [
        ("Priya Sharma","priya@example.com",hp("pass123"),"9811111111"),
        ("Rahul Mehta","rahul@example.com",hp("pass123"),"9822222222"),
        ("Anjali Patel","anjali@example.com",hp("pass123"),"9833333333"),
        ("Vikram Singh","vikram@example.com",hp("pass123"),"9844444444"),
        ("Sneha Joshi","sneha@example.com",hp("pass123"),"9855555555"),
    ]
    for u in extras:
        c.execute("INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)", u)


def _seed_orders(c):
    statuses = ['pending','shipped','delivered','delivered','delivered']
    methods  = ['UPI','Credit Card','Debit Card','Net Banking','UPI']
    items_pool = list(range(1,26))
    import random as rnd
    rnd.seed(42)
    for i in range(30):
        uid = rnd.randint(1,6)
        oid = f"MF-{100000+i:06d}"
        days_ago = rnd.randint(1,180)
        order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        pids = rnd.sample(items_pool, rnd.randint(1,3))
        total = 0
        item_list = []
        for pid in pids:
            qty = rnd.randint(1,2)
            prices = [239,179,382,449,639,809,297,319,149,179,129,399,594,349,99,134,1039,1199,849,539,639,764,99,149,499]
            price = prices[pid-1] if pid <= len(prices) else 199
            total += price * qty
            item_list.append((oid, pid, qty, price))
        total = round(total + 80)
        addr_cities = ["Mumbai","Delhi","Bangalore","Chennai","Pune","Hyderabad"]
        addr = f"Flat {rnd.randint(1,50)}, Sample Street, {rnd.choice(addr_cities)} - {rnd.randint(400001,411015)}"
        names = ["Demo Customer","Priya Sharma","Rahul Mehta","Anjali Patel","Vikram Singh","Sneha Joshi"]
        phones = ["9876543210","9811111111","9822222222","9833333333","9844444444","9855555555"]
        emails = ["demo@monsfusion.com","priya@example.com","rahul@example.com","anjali@example.com","vikram@example.com","sneha@example.com"]
        c.execute("INSERT INTO orders(user_id,order_id,total_price,status,address,customer_name,phone,email,payment_method,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (uid, oid, total, rnd.choice(statuses), addr, names[uid-1], phones[uid-1], emails[uid-1], rnd.choice(methods), order_date))
        for it in item_list:
            c.execute("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)", it)


def hp(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def gen_oid():
    n = random.randint(1,999999)
    return f"MF-{n:06d}"