# 🚍 Campus Shuttle Management System v3.0
### Real Bus Management System — Student Booking + Driver Manifest + Admin Control

---

## ✅ HOW TO RUN — Complete Step-by-Step

### Prerequisites
- Python 3.9 or higher
- VS Code installed
- Internet connection (for Google Fonts / Chart.js CDN)

---

### Step 1 — Extract & Open

1. Extract `shuttle-v3.zip`
2. Open **VS Code** → `File → Open Folder` → select `shuttle-v3`

---

### Step 2 — Open Terminal

Press **Ctrl + ` ** (backtick) in VS Code

---

### Step 3 — Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Step 4 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5 — Run

```bash
python app.py
```

Output:
```
✅ DB ready — Campus Shuttle v3.0
🚍 Campus Shuttle Management System v3.0
   → http://localhost:5000
```

---

### Step 6 — Open Browser

```
http://localhost:5000
```

---

## 🔐 Login Credentials

| Role    | Username  | Password    | Portal |
|---------|-----------|-------------|--------|
| **Admin**   | `admin`     | `admin123`    | `/admin` |
| **Driver 1**| `driver1`   | `driver123`   | `/driver` |
| **Driver 2**| `driver2`   | `driver456`   | `/driver` |
| **Driver 3**| `driver3`   | `driver789`   | `/driver` |
| Student | `student1`  | `student123`  | `/student` |
| Student | `alice`     | `alice123`    | `/student` |
| Student | `bob`       | `bob123`      | `/student` |
| Student | `charlie`   | `charlie123`  | `/student` |

---

## 🎯 Complete User Journey

### Student Flow (5 Steps)
1. Login → **Book Shuttle** tab
2. **Step 1** — Select Boarding Point (click a stop card)
3. **Step 2** — Select Destination (another stop)
4. **Step 3** — See Fare + Distance + Est. Time → Pick a shuttle (see driver info + available seats)
5. **Step 4** — Review all details → Confirm
6. **Step 5** — Get unique **Boarding Pass** (ID like `BRD-A1B2C3`, seat number)
7. Use **Track Booking** to monitor live status

### Driver Flow
1. Login as `driver1` → See your assigned shuttle info
2. **Passenger Manifest** — See all booked passengers grouped by boarding stop
3. When passenger boards → Click **✓ Board** (status: Booked → On Board)
4. When passenger exits → Click **🏁 Terminate** (status: On Board → Completed)
5. **Quick Scan** — Enter Boarding ID to quickly find & mark a passenger
6. **Trip Log** — Full history of all actions

### Admin Flow
1. Login as `admin`
2. **Overview** — Live stats + recent bookings
3. **Shuttle Fleet** — Each shuttle has its own panel showing:
   - Driver name, phone, vehicle info
   - All passengers with status (waiting/on board/done)
   - Seat-by-seat manifest
4. **All Bookings** — Full searchable table with boarded/terminated timestamps
5. **Analytics** — Revenue chart + booking status distribution

---

## 🗂️ Project Structure

```
shuttle-v3/
├── app.py              # Flask backend — all routes
├── db.py               # SQLite database — all tables, helpers
├── requirements.txt    # Flask, Flask-SocketIO, Eventlet
├── templates/
│   ├── login.html      # Unified login (student/driver/admin tabs)
│   ├── student.html    # 5-step booking flow + boarding pass
│   ├── driver.html     # Passenger manifest + board/terminate
│   └── admin.html      # Fleet panels + all bookings + analytics
└── data/
    └── shuttle.db      # Auto-created SQLite database
```

---

## 🧩 Key Features

| Feature | Details |
|---------|---------|
| **Boarding Point → Destination** | 5-step guided booking flow |
| **Fare + Distance + Time** | Shown before booking |
| **Shuttle Selection** | See driver name, vehicle, available seats |
| **Unique Boarding ID** | Format: `BRD-XXXXXX` (seat number assigned) |
| **Boarding Pass** | Shows all trip details + seat no |
| **Driver Manifest** | Grouped by boarding stop, real-time |
| **Board / Terminate** | Driver clicks to change passenger status |
| **Admin Shuttle Panels** | One card per shuttle with full info |
| **Real-time Sync** | WebSocket updates across all portals |
| **Role-Based Auth** | Student / Driver / Admin separate portals |
| **Search + Filter** | Bookings searchable by name, ID, route |
| **Revenue Analytics** | Charts per shuttle and status breakdown |

---

## 💡 Demo Tips

1. Open **3 browser tabs**: student / driver / admin simultaneously
2. Book as student → Watch it appear **live** in driver manifest and admin panel
3. Driver ticks **Board** → Student's tracking page updates to "On Board"
4. Driver clicks **Terminate** → Shows "Passenger Terminated" in admin
5. Admin → Shuttle Fleet panel → See full picture of every shuttle
