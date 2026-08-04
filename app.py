"""
Campus Shuttle Management System v3.0
Flask + SocketIO — Student booking flow, Driver manifest, Admin portal
"""
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import hashlib, time, threading, json, os
from db import (init_db, conn, hp, get_route_info, get_shuttle_availability,
                create_booking, get_my_bookings, get_shuttle_manifest,
                mark_boarded, mark_terminated, cancel_booking,
                get_all_shuttles, get_all_bookings_admin, update_shuttle_status,
                get_stops_list, get_driver_shuttle, get_stats, gen_boarding_id)

app = Flask(__name__)
app.secret_key = os.environ.get("CSMS_SECRET_KEY", "dev-only-change-me")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ── Auth helpers ──────────────────────────────────────────────────────────────
def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrap(*a, **kw):
        if 'uid' not in session: return redirect('/')
        return f(*a, **kw)
    return wrap

def role_required(*roles):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrap(*a, **kw):
            if session.get('role') not in roles:
                return jsonify({'error': 'Forbidden'}), 403
            return f(*a, **kw)
        return wrap
    return decorator

# ════════════════════════════════════════
#  PAGES
# ════════════════════════════════════════
@app.route('/')
def index():
    if 'uid' in session:
        role = session['role']
        if role == 'admin':   return redirect('/admin')
        if role == 'driver':  return redirect('/driver')
        return redirect('/student')
    return render_template('login.html')

@app.route('/student')
@login_required
def student_page():
    if session['role'] != 'student': return redirect('/')
    return render_template('student.html', username=session['uname'], full_name=session.get('full_name',''))

@app.route('/admin')
@login_required
def admin_page():
    if session['role'] != 'admin': return redirect('/')
    return render_template('admin.html', username=session['uname'])

@app.route('/driver')
@login_required
def driver_page():
    if session['role'] != 'driver': return redirect('/')
    sh = get_driver_shuttle(session['uid'])
    if sh is None:
        sh = {'id': None, 'name': 'No shuttle assigned', 'status': 'off_duty',
              'current_stop': '', 'capacity': 0, 'license_plate': '', 'model': ''}
    return render_template('driver.html', username=session['uname'],
                           full_name=session.get('full_name',''), shuttle=sh)

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

# ════════════════════════════════════════
#  AUTH API
# ════════════════════════════════════════
@app.route('/api/login', methods=['POST'])
def api_login():
    d  = request.json
    db = conn()
    u  = db.execute("SELECT * FROM users WHERE username=? AND password=?",
                    (d['username'], hp(d['password']))).fetchone()
    db.close()
    if u:
        session.update({'uid': u['id'], 'uname': u['username'],
                        'role': u['role'], 'full_name': u['full_name']})
        return jsonify({'ok': True, 'role': u['role'], 'username': u['username']})
    return jsonify({'ok': False, 'message': 'Invalid credentials'}), 401

# ════════════════════════════════════════
#  BOOKING FLOW (STUDENT)
# ════════════════════════════════════════
@app.route('/api/stops')
def api_stops():
    stops = get_stops_list()
    COORDS = {
        "Gate A":{"x":80,"y":280,"color":"#00e5ff"},
        "Library":{"x":230,"y":140,"color":"#ff6b35"},
        "Hostel Block":{"x":420,"y":80,"color":"#a855f7"},
        "Cafeteria":{"x":540,"y":190,"color":"#22c55e"},
        "Tech Block":{"x":640,"y":330,"color":"#f59e0b"},
        "Sports Ground":{"x":460,"y":390,"color":"#ec4899"},
        "Admin Block":{"x":280,"y":340,"color":"#06b6d4"},
        "Medical":{"x":130,"y":410,"color":"#ef4444"},
        "Labs Complex":{"x":590,"y":90,"color":"#84cc16"},
    }
    return jsonify([{"id":s,"color":COORDS.get(s,{}).get("color","#fff"),
                     "x":COORDS.get(s,{}).get("x",300),
                     "y":COORDS.get(s,{}).get("y",200)} for s in stops])

@app.route('/api/route_info')
def api_route_info():
    f = request.args.get('from')
    t = request.args.get('to')
    if not f or not t: return jsonify({'error':'Missing params'}),400
    rt = get_route_info(f, t)
    if not rt: return jsonify({'error':'Route not found'}),404
    # Get available shuttles
    shuttles = []
    for sh in get_all_shuttles():
        if sh['status'] == 'off_duty': continue
        av = get_shuttle_availability(sh['id'])
        if av and av['available'] > 0:
            shuttles.append({
                'id': sh['id'], 'name': sh['name'],
                'driver': sh['driver_name'], 'driver_phone': sh['driver_phone'],
                'license': sh['license_plate'], 'model': sh['model'],
                'capacity': sh['capacity'], 'available': av['available'],
                'booked': av['booked'], 'current_stop': sh['current_stop'],
                'status': sh['status']
            })
    return jsonify({**rt, 'shuttles': shuttles})

@app.route('/api/book', methods=['POST'])
def api_book():
    if 'uid' not in session: return jsonify({'error':'Not logged in'}),401
    if session['role'] != 'student': return jsonify({'error':'Students only'}),403
    d = request.json
    bk = create_booking(session['uid'], session.get('full_name') or session['uname'],
                        d['shuttle_id'], d['from_stop'], d['to_stop'])
    if not bk: return jsonify({'error':'Booking failed — shuttle full or route unavailable'}),400
    # Broadcast update to admin and driver
    socketio.emit('booking_update', {'shuttle_id': d['shuttle_id']})
    return jsonify({'ok': True, 'booking': bk})

@app.route('/api/my_bookings')
def api_my_bookings():
    if 'uid' not in session: return jsonify([])
    return jsonify(get_my_bookings(session['uid']))

@app.route('/api/cancel_booking', methods=['POST'])
def api_cancel():
    if 'uid' not in session: return jsonify({'error':'Not logged in'}),401
    bid = request.json.get('boarding_id')
    cancel_booking(bid, session['uid'])
    socketio.emit('booking_update', {})
    return jsonify({'ok': True})

# ════════════════════════════════════════
#  DRIVER API
# ════════════════════════════════════════
@app.route('/api/driver/manifest')
def api_manifest():
    if session.get('role') not in ('driver','admin'):
        return jsonify({'error':'Forbidden'}),403
    sh_id = request.args.get('shuttle_id')
    if not sh_id:
        driver_shuttle = get_driver_shuttle(session['uid'])
        sh_id = driver_shuttle['id'] if driver_shuttle else None
    if not sh_id:
        return jsonify([])
    return jsonify(get_shuttle_manifest(sh_id))

@app.route('/api/driver/board', methods=['POST'])
def api_board():
    if session.get('role') != 'driver': return jsonify({'error':'Forbidden'}),403
    bid = request.json.get('boarding_id')
    mark_boarded(bid, session['uid'])
    socketio.emit('manifest_update', {'action':'boarded','boarding_id':bid})
    socketio.emit('booking_status', {'boarding_id':bid,'status':'on_board'})
    return jsonify({'ok':True})

@app.route('/api/driver/terminate', methods=['POST'])
def api_terminate():
    if session.get('role') != 'driver': return jsonify({'error':'Forbidden'}),403
    bid = request.json.get('boarding_id')
    mark_terminated(bid, session['uid'])
    socketio.emit('manifest_update', {'action':'terminated','boarding_id':bid})
    socketio.emit('booking_status', {'boarding_id':bid,'status':'completed'})
    return jsonify({'ok':True})

@app.route('/api/driver/shuttle_status', methods=['POST'])
def api_shuttle_status():
    if session.get('role') not in ('driver','admin'): return jsonify({'error':'Forbidden'}),403
    d = request.json
    update_shuttle_status(d['shuttle_id'], d['status'], d.get('current_stop',''))
    socketio.emit('shuttle_update', get_all_shuttles())
    return jsonify({'ok':True})

# ════════════════════════════════════════
#  ADMIN API
# ════════════════════════════════════════
@app.route('/api/admin/shuttles')
def api_admin_shuttles():
    if session.get('role') != 'admin': return jsonify({'error':'Forbidden'}),403
    shuttles = get_all_shuttles()
    result = []
    for sh in shuttles:
        av = get_shuttle_availability(sh['id'])
        manifest = get_shuttle_manifest(sh['id'])
        result.append({**sh, 'available': av['available'] if av else 0,
                       'booked': av['booked'] if av else 0,
                       'manifest': manifest})
    return jsonify(result)

@app.route('/api/admin/bookings')
def api_admin_bookings():
    if session.get('role') != 'admin': return jsonify({'error':'Forbidden'}),403
    return jsonify(get_all_bookings_admin(200))

@app.route('/api/admin/stats')
def api_admin_stats():
    if session.get('role') != 'admin': return jsonify({'error':'Forbidden'}),403
    return jsonify(get_stats())

@app.route('/api/admin/shuttle_status', methods=['POST'])
def api_admin_shuttle_status():
    if session.get('role') != 'admin': return jsonify({'error':'Forbidden'}),403
    d = request.json
    update_shuttle_status(d['shuttle_id'], d['status'], d.get('current_stop',''))
    socketio.emit('shuttle_update', get_all_shuttles())
    return jsonify({'ok':True})

# ════════════════════════════════════════
#  LIVE BOOKING STATUS (student polls)
# ════════════════════════════════════════
@app.route('/api/booking_status/<boarding_id>')
def api_booking_status(boarding_id):
    db  = conn()
    row = db.execute("SELECT b.*,s.current_stop,s.status as shuttle_status,s.driver_name FROM bookings b JOIN shuttles s ON b.shuttle_id=s.id WHERE b.boarding_id=?", (boarding_id,)).fetchone()
    db.close()
    return jsonify(dict(row)) if row else jsonify({'error':'Not found'}), 404
import traceback

@app.errorhandler(500)
def internal_error(e):
    return f"<pre>{traceback.format_exc()}</pre>", 500
    
if __name__ == '__main__':
    init_db()
    print("🚍 Campus Shuttle Management System v3.0")
    print("   → http://localhost:5000")
    print("   Logins: admin/admin123 | driver1/driver123 | student1/student123")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)