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
from flask import Flask, jsonify, request, session, send_from_directory
import sqlite3, hashlib, json, random, os
from datetime import datetime, date, timedelta
from functools import wraps

app = Flask(__name__, static_folder='.')
app.secret_key = "mf_v2_ultra_secret_2024"
app.jinja_env.comment_start_string = '{##'
app.jinja_env.comment_end_string   = '##}'
DB = "mf_v2.db"

# ─── ADMIN CREDENTIALS (hardcoded) ─────────────────────────────────────────
ADMIN_USER = "ParabStore"
ADMIN_PASS = "Parab@29"

# ─── DB ────────────────────────────────────────────────────────────────────
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
        rating INTEGER, comment TEXT,
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
    """)
    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        _seed_products(c)
    if not c.execute("SELECT COUNT(*) FROM coupons").fetchone()[0]:
        _seed_coupons(c)
    if not c.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        _seed_users(c)
    if not c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]:
        _seed_orders(c)
    c.commit(); c.close()

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
    # Demo customer account
    c.execute("INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)",
              ("Demo Customer","demo@monsfusion.com",hp("Demo@1234"),"9876543210"))
    # Extra demo users for analytics
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
    # Generate 30 realistic demo orders over last 6 months
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
            # approximate price from seed index
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

def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()
def gen_oid():
    n = random.randint(1,999999)
    return f"MF-{n:06d}"

# ─── AUTH DECORATORS ────────────────────────────────────────────────────────
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated

def require_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({'error': 'Please login'}), 401
        return f(*args, **kwargs)
    return decorated

# ─── STATIC FILES ────────────────────────────────────────────────────────────
@app.route('/')
def customer(): return send_from_directory('.', 'customer.html')

@app.route('/admin')
def admin_redirect():
    if not session.get('admin_logged_in'):
        return send_from_directory('.', 'admin.html')
    return send_from_directory('.', 'admin.html')

@app.route('/admin.html')
def admin_page(): return send_from_directory('.', 'admin.html')

# ─── ADMIN AUTH ──────────────────────────────────────────────────────────────
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    d = request.json
    if d.get('username') == ADMIN_USER and d.get('password') == ADMIN_PASS:
        session['admin_logged_in'] = True
        session['admin_name'] = ADMIN_USER
        return jsonify({'success': True, 'admin': ADMIN_USER})
    return jsonify({'error': 'Invalid admin credentials'}), 401

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_name', None)
    return jsonify({'success': True})

@app.route('/api/admin/session')
def admin_session():
    return jsonify({'logged_in': bool(session.get('admin_logged_in')), 'admin': session.get('admin_name','')})

# ─── CUSTOMER AUTH ────────────────────────────────────────────────────────────
@app.route('/api/session')
def api_session():
    uid = session.get('user_id')
    return jsonify({'logged_in': bool(uid), 'user_id': uid, 'user_name': session.get('user_name','')})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    d = request.json
    nm = d.get('name','').strip(); em = d.get('email','').strip().lower()
    pw = d.get('password',''); ph = d.get('phone','').strip()
    if len(nm)<3: return jsonify({'error':'Name must be at least 3 characters'}),400
    if '@' not in em or '.' not in em: return jsonify({'error':'Invalid email'}),400
    if len(pw)<8: return jsonify({'error':'Password must be at least 8 characters'}),400
    if ph and (not ph.isdigit() or len(ph)!=10): return jsonify({'error':'Phone must be 10 digits'}),400
    c = db()
    try:
        c.execute("INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)",(nm,em,hp(pw),ph))
        c.commit(); u=c.execute("SELECT * FROM users WHERE email=?",(em,)).fetchone()
        session['user_id']=u['id']; session['user_name']=u['name']
        return jsonify({'success':True,'user':{'id':u['id'],'name':u['name'],'email':u['email']}})
    except: return jsonify({'error':'Email already registered'}),400
    finally: c.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json; em=d.get('email','').strip().lower(); pw=d.get('password','')
    if not em: return jsonify({'error':'Email required'}),400
    if not pw: return jsonify({'error':'Password required'}),400
    c = db(); u=c.execute("SELECT * FROM users WHERE email=? AND password=?",(em,hp(pw))).fetchone(); c.close()
    if not u: return jsonify({'error':'Invalid email or password'}),401
    session['user_id']=u['id']; session['user_name']=u['name']
    return jsonify({'success':True,'user':{'id':u['id'],'name':u['name'],'email':u['email'],'phone':u['phone']}})

@app.route('/api/logout', methods=['POST'])
def api_logout(): session.pop('user_id',None); session.pop('user_name',None); return jsonify({'success':True})

@app.route('/api/profile', methods=['GET'])
@require_user
def api_profile():
    c=db(); u=c.execute("SELECT id,name,email,phone,created_at FROM users WHERE id=?",(session['user_id'],)).fetchone(); c.close()
    return jsonify(dict(u)) if u else (jsonify({'error':'Not found'}),404)

@app.route('/api/profile', methods=['PUT'])
@require_user
def api_profile_update():
    d=request.json; nm=d.get('name','').strip(); ph=d.get('phone','').strip()
    if len(nm)<3: return jsonify({'error':'Name min 3 chars'}),400
    c=db(); c.execute("UPDATE users SET name=?,phone=? WHERE id=?",(nm,ph,session['user_id'])); c.commit(); c.close()
    session['user_name']=nm; return jsonify({'success':True})

# ─── PRODUCT APIs (Customer) ──────────────────────────────────────────────────
@app.route('/api/products')
def api_products():
    q=request.args.get('q',''); cat=request.args.get('category','')
    gnd=request.args.get('gender',''); mx=request.args.get('max_price',99999,type=float)
    mn=request.args.get('min_price',0,type=float); bs=request.args.get('best_seller','')
    dc=request.args.get('discounted',''); srt=request.args.get('sort','')
    fs=request.args.get('festival',''); ml=request.args.get('most_liked','')
    lim=request.args.get('limit',100,type=int)

    sql="SELECT * FROM products WHERE active=1"; p=[]
    if q: sql+=" AND name LIKE ?"; p.append(f"%{q}%")
    if cat: sql+=" AND category=?"; p.append(cat)
    if gnd: sql+=" AND gender_tag=?"; p.append(gnd)
    if mn: sql+=" AND price>=?"; p.append(mn)
    if mx<99999: sql+=" AND price<=?"; p.append(mx)
    if bs=='1': sql+=" AND is_best_seller=1"
    if dc=='1': sql+=" AND discount>0"
    if fs=='1': sql+=" AND is_festival_special=1"
    if ml=='1': sql+=" AND is_most_liked=1"
    sql+={"price_asc":" ORDER BY price ASC","price_desc":" ORDER BY price DESC",
          "likes":" ORDER BY likes DESC","best_selling":" ORDER BY is_best_seller DESC,likes DESC",
          "newest":" ORDER BY created_at DESC"}.get(srt," ORDER BY likes DESC")
    sql+=f" LIMIT {lim}"
    c=db(); rows=[dict(r) for r in c.execute(sql,p).fetchall()]; c.close()
    for r in rows:
        r['dp']=round(r['price']*(1-r['discount']/100),2) if r['discount'] else r['price']
        try: r['images']=json.loads(r['images']) if r['images'] else [r['image_url']]
        except: r['images']=[r['image_url']]
    return jsonify(rows)

@app.route('/api/products/<int:pid>')
def api_product(pid):
    c=db(); p=c.execute("SELECT * FROM products WHERE id=? AND active=1",(pid,)).fetchone()
    if not p: c.close(); return jsonify({'error':'Not found'}),404
    pd=dict(p); pd['dp']=round(pd['price']*(1-pd['discount']/100),2) if pd['discount'] else pd['price']
    try: pd['images']=json.loads(pd['images']) if pd['images'] else [pd['image_url']]
    except: pd['images']=[pd['image_url']]
    pd['reviews']=[dict(r) for r in c.execute("SELECT * FROM reviews WHERE product_id=? ORDER BY created_at DESC",(pid,)).fetchall()]
    rel=[dict(r) for r in c.execute("SELECT * FROM products WHERE category=? AND id!=? AND active=1 LIMIT 4",(pd['category'],pid)).fetchall()]
    for r in rel: r['dp']=round(r['price']*(1-r['discount']/100),2) if r['discount'] else r['price']
    pd['related']=rel; c.close(); return jsonify(pd)

@app.route('/api/products/<int:pid>/like', methods=['POST'])
def api_like(pid):
    c=db(); c.execute("UPDATE products SET likes=likes+1 WHERE id=?",(pid,)); c.commit()
    lk=c.execute("SELECT likes FROM products WHERE id=?",(pid,)).fetchone()['likes']; c.close()
    return jsonify({'likes':lk})

@app.route('/api/categories')
def api_cats():
    c=db(); cats=[r[0] for r in c.execute("SELECT DISTINCT category FROM products WHERE active=1").fetchall()]; c.close()
    return jsonify(cats)

# ─── CART APIs ─────────────────────────────────────────────────────────────
@app.route('/api/cart')
def api_cart():
    uid=session.get('user_id')
    if not uid: return jsonify([])
    c=db()
    items=c.execute("SELECT c.id,c.quantity,p.id as product_id,p.name,p.price,p.discount,p.image_url FROM cart c JOIN products p ON c.product_id=p.id WHERE c.user_id=?",(uid,)).fetchall()
    c.close(); result=[]
    for i in items:
        r=dict(i); r['dp']=round(r['price']*(1-r['discount']/100),2) if r['discount'] else r['price']
        result.append(r)
    return jsonify(result)

@app.route('/api/cart/count')
def api_cart_count():
    uid=session.get('user_id')
    if not uid: return jsonify({'count':0})
    c=db(); n=c.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?",(uid,)).fetchone()[0] or 0; c.close()
    return jsonify({'count':n})

@app.route('/api/cart/add', methods=['POST'])
@require_user
def api_cart_add():
    d=request.json; pid=d.get('product_id'); qty=d.get('quantity',1); uid=session['user_id']
    c=db(); ex=c.execute("SELECT * FROM cart WHERE user_id=? AND product_id=?",(uid,pid)).fetchone()
    if ex: c.execute("UPDATE cart SET quantity=quantity+? WHERE id=?",(qty,ex['id']))
    else: c.execute("INSERT INTO cart(user_id,product_id,quantity) VALUES(?,?,?)",(uid,pid,qty))
    c.commit(); n=c.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?",(uid,)).fetchone()[0] or 0
    c.close(); return jsonify({'success':True,'cart_count':n})

@app.route('/api/cart/remove', methods=['POST'])
@require_user
def api_cart_remove():
    cid=request.json.get('cart_id'); c=db()
    c.execute("DELETE FROM cart WHERE id=? AND user_id=?",(cid,session['user_id'])); c.commit(); c.close()
    return jsonify({'success':True})

@app.route('/api/cart/update', methods=['POST'])
@require_user
def api_cart_update():
    d=request.json; cid=d.get('cart_id'); qty=d.get('quantity',1); c=db()
    if qty<1: c.execute("DELETE FROM cart WHERE id=? AND user_id=?",(cid,session['user_id']))
    else: c.execute("UPDATE cart SET quantity=? WHERE id=? AND user_id=?",(qty,cid,session['user_id']))
    c.commit(); c.close(); return jsonify({'success':True})

# ─── WISHLIST APIs ─────────────────────────────────────────────────────────
@app.route('/api/wishlist')
def api_wish():
    uid=session.get('user_id')
    if not uid: return jsonify([])
    c=db()
    items=c.execute("SELECT w.id,p.id as product_id,p.name,p.price,p.discount,p.image_url,p.rating FROM wishlist w JOIN products p ON w.product_id=p.id WHERE w.user_id=?",(uid,)).fetchall()
    c.close(); result=[]
    for i in items:
        r=dict(i); r['dp']=round(r['price']*(1-r['discount']/100),2) if r['discount'] else r['price']
        result.append(r)
    return jsonify(result)

@app.route('/api/wishlist/toggle', methods=['POST'])
@require_user
def api_wish_toggle():
    pid=request.json.get('product_id'); uid=session['user_id']; c=db()
    ex=c.execute("SELECT * FROM wishlist WHERE user_id=? AND product_id=?",(uid,pid)).fetchone()
    if ex: c.execute("DELETE FROM wishlist WHERE id=?",(ex['id'],)); c.commit(); c.close(); return jsonify({'added':False})
    c.execute("INSERT INTO wishlist(user_id,product_id) VALUES(?,?)",(uid,pid)); c.commit(); c.close()
    return jsonify({'added':True})

@app.route('/api/wishlist/check/<int:pid>')
def api_wish_check(pid):
    uid=session.get('user_id')
    if not uid: return jsonify({'in_wishlist':False})
    c=db(); ex=c.execute("SELECT id FROM wishlist WHERE user_id=? AND product_id=?",(uid,pid)).fetchone(); c.close()
    return jsonify({'in_wishlist':bool(ex)})

@app.route('/api/wishlist/remove', methods=['POST'])
@require_user
def api_wish_remove():
    wid=request.json.get('wishlist_id'); c=db()
    c.execute("DELETE FROM wishlist WHERE id=? AND user_id=?",(wid,session['user_id'])); c.commit(); c.close()
    return jsonify({'success':True})

# ─── COUPON API ────────────────────────────────────────────────────────────
@app.route('/api/coupon/validate', methods=['POST'])
def api_coupon():
    code=request.json.get('code','').strip().upper()
    c=db(); cp=c.execute("SELECT * FROM coupons WHERE code=? AND active=1",(code,)).fetchone(); c.close()
    if not cp: return jsonify({'error':'Invalid coupon code'}),400
    if cp['expiry'] and cp['expiry'] < date.today().isoformat(): return jsonify({'error':'Coupon has expired'}),400
    return jsonify({'valid':True,'code':cp['code'],'type':cp['discount_type'],'value':cp['discount_value'],'free_delivery':bool(cp['free_delivery'])})

# ─── ORDER APIs ────────────────────────────────────────────────────────────
@app.route('/api/orders', methods=['POST'])
def api_orders_post():
    d=request.json; uid=session.get('user_id')
    nm=d.get('customer_name','').strip(); ph=d.get('phone','').strip()
    if len(nm)<3: return jsonify({'error':'Name must be at least 3 characters'}),400
    if not ph.isdigit() or len(ph)!=10: return jsonify({'error':'Phone must be 10 digits'}),400
    order_id=gen_oid(); c=db()
    while c.execute("SELECT id FROM orders WHERE order_id=?",(order_id,)).fetchone(): order_id=gen_oid()
    c.execute("INSERT INTO orders(user_id,order_id,total_price,address,customer_name,phone,email,payment_method,coupon_code,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
              (uid,order_id,d.get('total_price'),d.get('address'),nm,ph,d.get('email'),d.get('payment_method'),d.get('coupon_code'),'pending'))
    for item in d.get('items',[]):
        c.execute("INSERT INTO order_items(order_id,product_id,quantity,price) VALUES(?,?,?,?)",(order_id,item['product_id'],item['quantity'],item['price']))
    if uid: c.execute("DELETE FROM cart WHERE user_id=?",(uid,))
    c.commit(); c.close()
    return jsonify({'success':True,'order_id':order_id})

@app.route('/api/orders/user')
@require_user
def api_orders_user():
    uid=session['user_id']; c=db()
    ords=[dict(o) for o in c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC",(uid,)).fetchall()]
    for o in ords:
        items=c.execute("SELECT oi.*,p.name,p.image_url FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?",(o['order_id'],)).fetchall()
        o['items']=[dict(i) for i in items]
    c.close(); return jsonify(ords)

# ─── REVIEW APIs ────────────────────────────────────────────────────────────
@app.route('/api/reviews', methods=['POST'])
@require_user
def api_review():
    d=request.json; pid=d.get('product_id'); rt=d.get('rating',5); cm=d.get('comment','').strip()
    if not cm: return jsonify({'error':'Comment required'}),400
    if not 1<=rt<=5: return jsonify({'error':'Rating must be 1-5'}),400
    uid=session['user_id']; c=db()
    un=c.execute("SELECT name FROM users WHERE id=?",(uid,)).fetchone()
    un=un['name'] if un else 'Anonymous'
    c.execute("INSERT INTO reviews(product_id,user_id,user_name,rating,comment) VALUES(?,?,?,?,?)",(pid,uid,un,rt,cm))
    avg=c.execute("SELECT AVG(rating) FROM reviews WHERE product_id=?",(pid,)).fetchone()[0]
    c.execute("UPDATE products SET rating=? WHERE id=?",(round(avg,1),pid))
    c.commit(); c.close(); return jsonify({'success':True})

# ═══════════════════════════════════════════════════════════════════════════
#  ADMIN APIs
# ═══════════════════════════════════════════════════════════════════════════

# ─── ADMIN PRODUCTS ─────────────────────────────────────────────────────────
@app.route('/api/admin/products', methods=['GET'])
@require_admin
def admin_get_products():
    c=db()
    rows=[dict(r) for r in c.execute("SELECT * FROM products ORDER BY id DESC").fetchall()]
    c.close()
    for r in rows:
        try: r['images']=json.loads(r['images']) if r['images'] else [r['image_url']]
        except: r['images']=[r['image_url']]
    return jsonify(rows)

@app.route('/api/admin/products', methods=['POST'])
@require_admin
def admin_add_product():
    d=request.json
    name=d.get('name','').strip()
    if not name: return jsonify({'error':'Name required'}),400
    c=db()
    imgs=d.get('images',[])
    img_url=imgs[0] if imgs else d.get('image_url','https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=500')
    cur = c.execute("""INSERT INTO products(name,price,discount,description,category,subcategory,gender_tag,
                 is_best_seller,is_festival_special,is_most_liked,image_url,images,active)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)""",
              (name, d.get('price',0), d.get('discount',0), d.get('description',''),
               d.get('category',''), d.get('subcategory',''), d.get('gender_tag',''),
               1 if d.get('is_best_seller') else 0,
               1 if d.get('is_festival_special') else 0,
               1 if d.get('is_most_liked') else 0,
               img_url, json.dumps(imgs) if imgs else json.dumps([img_url])))
    c.commit(); pid=cur.lastrowid; c.close()
    return jsonify({'success':True,'id':pid})

@app.route('/api/admin/products/<int:pid>', methods=['PUT'])
@require_admin
def admin_update_product(pid):
    d=request.json; c=db()
    imgs=d.get('images',[])
    img_url=imgs[0] if imgs else d.get('image_url','')
    c.execute("""UPDATE products SET name=?,price=?,discount=?,description=?,category=?,subcategory=?,
                 gender_tag=?,is_best_seller=?,is_festival_special=?,is_most_liked=?,
                 image_url=?,images=?,active=? WHERE id=?""",
              (d.get('name'), d.get('price',0), d.get('discount',0), d.get('description',''),
               d.get('category',''), d.get('subcategory',''), d.get('gender_tag',''),
               1 if d.get('is_best_seller') else 0,
               1 if d.get('is_festival_special') else 0,
               1 if d.get('is_most_liked') else 0,
               img_url, json.dumps(imgs) if imgs else json.dumps([img_url]),
               1 if d.get('active',True) else 0, pid))
    c.commit(); c.close(); return jsonify({'success':True})

@app.route('/api/admin/products/<int:pid>', methods=['DELETE'])
@require_admin
def admin_delete_product(pid):
    c=db(); c.execute("UPDATE products SET active=0 WHERE id=?",(pid,)); c.commit(); c.close()
    return jsonify({'success':True})

# ─── ADMIN COUPONS ──────────────────────────────────────────────────────────
@app.route('/api/admin/coupons', methods=['GET'])
@require_admin
def admin_get_coupons():
    c=db(); rows=[dict(r) for r in c.execute("SELECT * FROM coupons ORDER BY id DESC").fetchall()]; c.close()
    return jsonify(rows)

@app.route('/api/admin/coupons', methods=['POST'])
@require_admin
def admin_add_coupon():
    d=request.json; code=d.get('code','').strip().upper()
    if not code: return jsonify({'error':'Coupon code required'}),400
    c=db()
    try:
        cur = c.execute("INSERT INTO coupons(code,discount_type,discount_value,free_delivery,expiry,active) VALUES(?,?,?,?,?,1)",
                  (code, d.get('discount_type','percent'), d.get('discount_value',0),
                   1 if d.get('free_delivery') else 0, d.get('expiry','')))
        c.commit(); cid=cur.lastrowid; c.close()
        return jsonify({'success':True,'id':cid})
    except Exception as e:
        c.close(); return jsonify({'error':'Coupon code already exists'}),400

@app.route('/api/admin/coupons/<int:cid>', methods=['PUT'])
@require_admin
def admin_update_coupon(cid):
    d=request.json; c=db()
    c.execute("UPDATE coupons SET discount_type=?,discount_value=?,free_delivery=?,expiry=?,active=? WHERE id=?",
              (d.get('discount_type','percent'), d.get('discount_value',0),
               1 if d.get('free_delivery') else 0, d.get('expiry',''),
               1 if d.get('active',True) else 0, cid))
    c.commit(); c.close(); return jsonify({'success':True})

@app.route('/api/admin/coupons/<int:cid>', methods=['DELETE'])
@require_admin
def admin_delete_coupon(cid):
    c=db(); c.execute("DELETE FROM coupons WHERE id=?",(cid,)); c.commit(); c.close()
    return jsonify({'success':True})

# ─── ADMIN ORDERS ───────────────────────────────────────────────────────────
@app.route('/api/admin/orders', methods=['GET'])
@require_admin
def admin_get_orders():
    status=request.args.get('status','')
    c=db()
    sql="SELECT * FROM orders"
    params=[]
    if status: sql+=" WHERE status=?"; params.append(status)
    sql+=" ORDER BY created_at DESC"
    ords=[dict(o) for o in c.execute(sql,params).fetchall()]
    for o in ords:
        items=c.execute("SELECT oi.*,p.name,p.image_url FROM order_items oi JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?",(o['order_id'],)).fetchall()
        o['items']=[dict(i) for i in items]
    c.close(); return jsonify(ords)

@app.route('/api/admin/orders/<string:oid>/status', methods=['PUT'])
@require_admin
def admin_update_order_status(oid):
    status=request.json.get('status','')
    if status not in ['pending','shipped','delivered','cancelled']:
        return jsonify({'error':'Invalid status'}),400
    c=db(); c.execute("UPDATE orders SET status=? WHERE order_id=?",(status,oid)); c.commit(); c.close()
    return jsonify({'success':True})

# ─── ADMIN ANALYTICS ────────────────────────────────────────────────────────
@app.route('/api/admin/analytics')
@require_admin
def admin_analytics():
    c=db()

    # Totals
    total_orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_revenue = c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE status!='cancelled'").fetchone()[0]
    total_customers = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_products = c.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]

    # Revenue by month (last 6 months)
    monthly = []
    for i in range(5,-1,-1):
        d_start = (datetime.now().replace(day=1) - timedelta(days=30*i))
        month_str = d_start.strftime("%Y-%m")
        month_name = d_start.strftime("%b %Y")
        rev = c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE created_at LIKE ? AND status!='cancelled'",(month_str+'%',)).fetchone()[0]
        cnt = c.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",(month_str+'%',)).fetchone()[0]
        monthly.append({'month':month_name,'revenue':round(rev,2),'orders':cnt})

    # Best selling products (by order items)
    best_products = c.execute("""
        SELECT p.name, p.category, p.image_url, SUM(oi.quantity) as total_sold, SUM(oi.quantity*oi.price) as revenue
        FROM order_items oi JOIN products p ON oi.product_id=p.id
        GROUP BY oi.product_id ORDER BY total_sold DESC LIMIT 5
    """).fetchall()

    # Category sales
    cat_sales = c.execute("""
        SELECT p.category, COUNT(oi.id) as orders, SUM(oi.quantity*oi.price) as revenue
        FROM order_items oi JOIN products p ON oi.product_id=p.id
        GROUP BY p.category ORDER BY revenue DESC
    """).fetchall()

    # Order status distribution
    status_dist = c.execute("SELECT status, COUNT(*) as count FROM orders GROUP BY status").fetchall()

    # Recent orders
    recent = c.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 8").fetchall()

    # Avg order value
    avg_order = c.execute("SELECT COALESCE(AVG(total_price),0) FROM orders WHERE status!='cancelled'").fetchone()[0]

    # Total profit (rough 40% margin)
    total_profit = total_revenue * 0.4

    c.close()
    return jsonify({
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'total_customers': total_customers,
        'total_products': total_products,
        'total_profit': round(total_profit, 2),
        'avg_order_value': round(avg_order, 2),
        'monthly': monthly,
        'best_products': [dict(r) for r in best_products],
        'category_sales': [dict(r) for r in cat_sales],
        'status_distribution': [dict(r) for r in status_dist],
        'recent_orders': [dict(r) for r in recent],
    })

@app.route('/api/admin/customers', methods=['GET'])
@require_admin
def admin_customers():
    c=db()
    users=c.execute("SELECT id,name,email,phone,created_at FROM users ORDER BY created_at DESC").fetchall()
    result=[]
    for u in users:
        ud=dict(u)
        ud['order_count']=c.execute("SELECT COUNT(*) FROM orders WHERE user_id=?",(u['id'],)).fetchone()[0]
        ud['total_spent']=c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders WHERE user_id=? AND status!='cancelled'",(u['id'],)).fetchone()[0]
        result.append(ud)
    c.close(); return jsonify(result)

if __name__ == '__main__':
    init_db()
    print("\n"+"="*62)
    print("  🎁  MONS FUSION — Full Stack App Ready!")
    print("="*62)
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
    print("="*62+"\n")
    app.run(debug=True, port=5000)
