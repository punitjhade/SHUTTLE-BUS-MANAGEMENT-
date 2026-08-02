"""
Database — SQLite for Campus Shuttle Management System v3
Tables:
  users         — students, admins, drivers
  shuttles      — shuttle fleet with driver info
  routes        — stop→stop with fare/distance
  bookings      — passenger bookings with boarding_id
  boarding_log  — driver ticks passenger on-board / terminated
"""
import sqlite3, hashlib, os, random, string
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), 'data', 'shuttle.db')

def hp(pw): return hashlib.sha256(pw.encode()).hexdigest()

def conn():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    db = conn()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        username  TEXT UNIQUE NOT NULL,
        password  TEXT NOT NULL,
        role      TEXT DEFAULT 'student',   -- student | admin | driver
        full_name TEXT DEFAULT '',
        email     TEXT DEFAULT '',
        phone     TEXT DEFAULT '',
        created   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS shuttles (
        id           TEXT PRIMARY KEY,        -- SH-001 etc
        name         TEXT NOT NULL,
        driver_id    INTEGER,
        driver_name  TEXT DEFAULT '',
        driver_phone TEXT DEFAULT '',
        capacity     INTEGER DEFAULT 20,
        route_from   TEXT DEFAULT '',
        route_to     TEXT DEFAULT '',
        status       TEXT DEFAULT 'idle',    -- idle|running|at_stop|off_duty
        current_stop TEXT DEFAULT '',
        license_plate TEXT DEFAULT '',
        model        TEXT DEFAULT '',
        created      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(driver_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS stop_routes (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        from_stop TEXT NOT NULL,
        to_stop   TEXT NOT NULL,
        distance  REAL NOT NULL,
        fare      REAL NOT NULL,
        duration  INTEGER NOT NULL          -- minutes
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        boarding_id   TEXT UNIQUE NOT NULL,
        student_id    INTEGER NOT NULL,
        student_name  TEXT NOT NULL,
        shuttle_id    TEXT NOT NULL,
        from_stop     TEXT NOT NULL,
        to_stop       TEXT NOT NULL,
        distance      REAL,
        fare          REAL,
        seat_no       INTEGER,
        status        TEXT DEFAULT 'booked', -- booked|on_board|completed|cancelled
        booked_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        boarded_at    TIMESTAMP,
        terminated_at TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(shuttle_id) REFERENCES shuttles(id)
    );

    CREATE TABLE IF NOT EXISTS boarding_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id  INTEGER,
        boarding_id TEXT,
        action      TEXT,                   -- boarded | terminated
        driver_id   INTEGER,
        timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Seed users
    seed_users = [
        ('admin',    hp('admin123'),    'admin',   'Admin User',      '', ''),
        ('driver1',  hp('driver123'),   'driver',  'Ravi Kumar',      '9876543210', ''),
        ('driver2',  hp('driver456'),   'driver',  'Suresh Babu',     '9123456789', ''),
        ('driver3',  hp('driver789'),   'driver',  'Anbu Selvan',     '9988776655', ''),
        ('student1', hp('student123'),  'student', 'Alice Johnson',   '', 'alice@campus.edu'),
        ('student2', hp('pass123'),     'student', 'Bob Williams',    '', 'bob@campus.edu'),
        ('alice',    hp('alice123'),    'student', 'Alice Sharma',    '', 'alice2@campus.edu'),
        ('bob',      hp('bob123'),      'student', 'Bob Patel',       '', 'bob2@campus.edu'),
        ('charlie',  hp('charlie123'),  'student', 'Charlie Cruz',    '', 'charlie@campus.edu'),
        ('diana',    hp('diana123'),    'student', 'Diana Prince',    '', 'diana@campus.edu'),
    ]
    for u in seed_users:
        try: db.execute("INSERT INTO users (username,password,role,full_name,phone,email) VALUES (?,?,?,?,?,?)", u)
        except: pass

    # Seed shuttles
    seed_shuttles = [
        ('SH-001', 'Campus Express 1', 2, 'Ravi Kumar',   '9876543210', 20, 'TN-01-AB-1234', 'Ashok Leyland'),
        ('SH-002', 'Campus Express 2', 3, 'Suresh Babu',  '9123456789', 18, 'TN-02-CD-5678', 'TATA Motors'),
        ('SH-003', 'Campus Shuttle 3', 4, 'Anbu Selvan',  '9988776655', 22, 'TN-03-EF-9012', 'Volvo'),
    ]
    for s in seed_shuttles:
        try:
            db.execute("""INSERT INTO shuttles (id,name,driver_id,driver_name,driver_phone,capacity,license_plate,model,status,current_stop)
                VALUES (?,?,?,?,?,?,?,?,'idle','Gate A')""", s)
        except: pass

    # Seed stop routes (all combinations)
    stops = ["Gate A","Library","Hostel Block","Cafeteria","Tech Block","Sports Ground","Admin Block","Medical","Labs Complex"]
    fare_per_km = 5.0
    distances = {
        ("Gate A","Library"):2.0,("Gate A","Admin Block"):1.8,("Gate A","Medical"):1.5,
        ("Gate A","Hostel Block"):3.8,("Gate A","Cafeteria"):4.5,("Gate A","Tech Block"):5.8,
        ("Gate A","Sports Ground"):5.2,("Gate A","Labs Complex"):5.6,
        ("Library","Hostel Block"):2.2,("Library","Admin Block"):1.6,("Library","Cafeteria"):3.0,
        ("Library","Tech Block"):4.2,("Library","Sports Ground"):3.8,("Library","Labs Complex"):3.0,
        ("Library","Medical"):2.4,
        ("Hostel Block","Labs Complex"):1.8,("Hostel Block","Cafeteria"):2.5,
        ("Hostel Block","Tech Block"):3.2,("Hostel Block","Medical"):4.5,
        ("Cafeteria","Tech Block"):1.4,("Cafeteria","Labs Complex"):1.2,
        ("Cafeteria","Sports Ground"):2.2,("Cafeteria","Medical"):3.5,
        ("Tech Block","Sports Ground"):1.6,("Tech Block","Labs Complex"):2.0,
        ("Tech Block","Medical"):4.0,
        ("Sports Ground","Admin Block"):2.8,("Sports Ground","Medical"):3.2,
        ("Admin Block","Medical"):2.1,("Labs Complex","Medical"):4.2,
    }
    for (a,b),d in distances.items():
        fare = round(d * fare_per_km, 2)
        dur  = int(d * 3)
        try: db.execute("INSERT INTO stop_routes (from_stop,to_stop,distance,fare,duration) VALUES (?,?,?,?,?)",(a,b,d,fare,dur))
        except: pass
        try: db.execute("INSERT INTO stop_routes (from_stop,to_stop,distance,fare,duration) VALUES (?,?,?,?,?)",(b,a,d,fare,dur))
        except: pass

    db.commit()
    db.close()
    print("✅ DB ready — Campus Shuttle v3.0")

def gen_boarding_id():
    chars = string.ascii_uppercase + string.digits
    code  = ''.join(random.choices(chars, k=6))
    return f"BRD-{code}"

# ── Booking helpers ───────────────────────────────────────────────────────────
def get_route_info(from_stop, to_stop):
    db  = conn()
    row = db.execute("SELECT * FROM stop_routes WHERE from_stop=? AND to_stop=?", (from_stop,to_stop)).fetchone()
    db.close()
    return dict(row) if row else None

def get_shuttle_availability(shuttle_id):
    db = conn()
    sh = db.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
    if not sh:
        db.close(); return None
    booked = db.execute("SELECT COUNT(*) as c FROM bookings WHERE shuttle_id=? AND status IN ('booked','on_board')", (shuttle_id,)).fetchone()['c']
    db.close()
    return {"shuttle": dict(sh), "booked": booked, "available": sh['capacity'] - booked}

def create_booking(student_id, student_name, shuttle_id, from_stop, to_stop):
    rt = get_route_info(from_stop, to_stop)
    if not rt: return None
    av = get_shuttle_availability(shuttle_id)
    if not av or av['available'] <= 0: return None

    bid = gen_boarding_id()
    # Next available seat
    db  = conn()
    taken = [r['seat_no'] for r in db.execute("SELECT seat_no FROM bookings WHERE shuttle_id=? AND status IN ('booked','on_board')",(shuttle_id,)).fetchall()]
    seat  = next((i for i in range(1, av['shuttle']['capacity']+1) if i not in taken), 1)
    db.execute("""INSERT INTO bookings (boarding_id,student_id,student_name,shuttle_id,from_stop,to_stop,distance,fare,seat_no)
                  VALUES (?,?,?,?,?,?,?,?,?)""",
               (bid, student_id, student_name, shuttle_id, from_stop, to_stop, rt['distance'], rt['fare'], seat))
    db.commit()
    # Return full booking
    row = db.execute("SELECT b.*,s.name as shuttle_name,s.driver_name,s.driver_phone,s.license_plate,s.model FROM bookings b JOIN shuttles s ON b.shuttle_id=s.id WHERE b.boarding_id=?",(bid,)).fetchone()
    db.close()
    return dict(row)

def get_my_bookings(student_id):
    db   = conn()
    rows = db.execute("""SELECT b.*,s.name as shuttle_name,s.driver_name,s.driver_phone,s.license_plate,s.current_stop,s.status as shuttle_status
                         FROM bookings b JOIN shuttles s ON b.shuttle_id=s.id
                         WHERE b.student_id=? ORDER BY b.booked_at DESC LIMIT 20""",(student_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_shuttle_manifest(shuttle_id):
    db   = conn()
    rows = db.execute("SELECT * FROM bookings WHERE shuttle_id=? AND status IN ('booked','on_board') ORDER BY seat_no",(shuttle_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]

def mark_boarded(booking_id, driver_id):
    db = conn()
    db.execute("UPDATE bookings SET status='on_board',boarded_at=CURRENT_TIMESTAMP WHERE boarding_id=?",(booking_id,))
    db.execute("INSERT INTO boarding_log (booking_id,boarding_id,action,driver_id) VALUES (?,?,'boarded',?)",
               (None, booking_id, driver_id))
    db.commit(); db.close()

def mark_terminated(booking_id, driver_id):
    db = conn()
    db.execute("UPDATE bookings SET status='completed',terminated_at=CURRENT_TIMESTAMP WHERE boarding_id=?",(booking_id,))
    db.execute("INSERT INTO boarding_log (booking_id,boarding_id,action,driver_id) VALUES (?,?,'terminated',?)",
               (None, booking_id, driver_id))
    db.commit(); db.close()

def cancel_booking(booking_id, student_id):
    db = conn()
    db.execute("UPDATE bookings SET status='cancelled' WHERE boarding_id=? AND student_id=? AND status='booked'",
               (booking_id, student_id))
    db.commit(); db.close()

def get_all_shuttles():
    db   = conn()
    rows = db.execute("SELECT * FROM shuttles").fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_all_bookings_admin(limit=100):
    db   = conn()
    rows = db.execute("""SELECT b.*,s.name as shuttle_name,s.driver_name FROM bookings b
                         JOIN shuttles s ON b.shuttle_id=s.id
                         ORDER BY b.booked_at DESC LIMIT ?""",(limit,)).fetchall()
    db.close()
    return [dict(r) for r in rows]

def update_shuttle_status(shuttle_id, status, current_stop=''):
    db = conn()
    if current_stop:
        db.execute("UPDATE shuttles SET status=?,current_stop=? WHERE id=?",(status,current_stop,shuttle_id))
    else:
        db.execute("UPDATE shuttles SET status=? WHERE id=?",(status,shuttle_id))
    db.commit(); db.close()

def get_stops_list():
    db   = conn()
    rows = db.execute("SELECT DISTINCT from_stop FROM stop_routes ORDER BY from_stop").fetchall()
    db.close()
    return [r['from_stop'] for r in rows]

def get_driver_shuttle(driver_id):
    db  = conn()
    row = db.execute("SELECT * FROM shuttles WHERE driver_id=?", (driver_id,)).fetchone()
    db.close()
    return dict(row) if row else None

def get_stats():
    db = conn()
    total_bookings = db.execute("SELECT COUNT(*) as c FROM bookings").fetchone()['c']
    active         = db.execute("SELECT COUNT(*) as c FROM bookings WHERE status='on_board'").fetchone()['c']
    completed      = db.execute("SELECT COUNT(*) as c FROM bookings WHERE status='completed'").fetchone()['c']
    revenue        = db.execute("SELECT SUM(fare) as s FROM bookings WHERE status IN ('booked','on_board','completed')").fetchone()['s'] or 0
    db.close()
    return {"total_bookings":total_bookings,"active":active,"completed":completed,"revenue":round(revenue,2)}
