"""
Fuel Bunk Manager - Offline SQLite Database Engine
100% Offline, Zero external dependencies, Thread-safe SQLite management.
"""

import os
import sqlite3
import json
import shutil
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_DIR, "fuel_bunk.db")
BACKUP_DIR = os.path.join(DB_DIR, "backups")

def get_connection():
    """Returns a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_FILE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates all required tables if they don't already exist."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 2. Staff Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                staff_id TEXT PRIMARY KEY,
                staff_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Employee',
                mobile TEXT DEFAULT '',
                pin TEXT NOT NULL DEFAULT '1234',
                status TEXT NOT NULL DEFAULT 'Active',
                created_at TEXT NOT NULL
            )
        """)

        # 3. Pumps Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pumps (
                pump_no INTEGER PRIMARY KEY,
                pump_name TEXT NOT NULL,
                fuel_types TEXT NOT NULL
            )
        """)

        # 4. Shifts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                shift_id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                shift TEXT NOT NULL DEFAULT 'S1',
                pump_no INTEGER NOT NULL,
                staff_id TEXT NOT NULL,
                staff_name TEXT NOT NULL,
                petrol_litres REAL DEFAULT 0,
                petrol_amount REAL DEFAULT 0,
                diesel_litres REAL DEFAULT 0,
                diesel_amount REAL DEFAULT 0,
                cng_kg REAL DEFAULT 0,
                cng_amount REAL DEFAULT 0,
                total_sales REAL DEFAULT 0,
                online_amount REAL DEFAULT 0,
                otp_amount REAL DEFAULT 0,
                hp_pay_amount REAL DEFAULT 0,
                cash_total REAL DEFAULT 0,
                change_amount REAL DEFAULT 0,
                expenditure REAL DEFAULT 0,
                expenditure_type TEXT DEFAULT 'General',
                expenditure_remarks TEXT DEFAULT '',
                testing_amount REAL DEFAULT 0,
                total_collected REAL DEFAULT 0,
                difference REAL DEFAULT 0,
                status TEXT DEFAULT 'Saved',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (pump_no) REFERENCES pumps (pump_no)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_date_pump ON shifts(date, pump_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shifts_staff ON shifts(staff_id)")

        # 5. Nozzle Readings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nozzle_readings (
                reading_id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                date TEXT NOT NULL,
                pump_no INTEGER NOT NULL,
                nozzle_no INTEGER NOT NULL,
                fuel_type TEXT NOT NULL,
                opening_reading REAL NOT NULL,
                closing_reading REAL NOT NULL,
                mid_reading REAL DEFAULT 0,
                litres REAL DEFAULT 0,
                rate REAL DEFAULT 0,
                rate1 REAL DEFAULT 0,
                rate2 REAL DEFAULT 0,
                slot1_litres REAL DEFAULT 0,
                slot1_amount REAL DEFAULT 0,
                slot2_litres REAL DEFAULT 0,
                slot2_amount REAL DEFAULT 0,
                amount REAL DEFAULT 0,
                FOREIGN KEY (shift_id) REFERENCES shifts (shift_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nozzle_shift ON nozzle_readings(shift_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nozzle_date_pump ON nozzle_readings(date, pump_no)")

        # 6. Expenditures Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenditures (
                expense_id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                date TEXT NOT NULL,
                pump_no INTEGER NOT NULL,
                expense_type TEXT NOT NULL,
                amount REAL NOT NULL,
                remarks TEXT DEFAULT '',
                FOREIGN KEY (shift_id) REFERENCES shifts (shift_id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_shift ON expenditures(shift_id)")

        # 7. Stock Purchases Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_purchases (
                purchase_id TEXT PRIMARY KEY,
                purchase_date TEXT NOT NULL,
                fuel_type TEXT NOT NULL,
                quantity_kg REAL NOT NULL,
                rate REAL NOT NULL,
                total_amount REAL NOT NULL,
                supplier TEXT DEFAULT '',
                invoice_no TEXT DEFAULT '',
                payment_type TEXT DEFAULT 'Bank Transfer',
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        # 8. DSR (Daily Stock & Dip Register)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dsr_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                fuel_type TEXT NOT NULL,
                opening_stock REAL NOT NULL,
                purchase_qty REAL DEFAULT 0,
                total_stock REAL DEFAULT 0,
                sales_qty REAL DEFAULT 0,
                expected_closing REAL DEFAULT 0,
                closing_dip REAL DEFAULT 0,
                actual_closing REAL DEFAULT 0,
                variation REAL DEFAULT 0,
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dsr_date ON dsr_entries(date)")

        # 9. OTP Settlements
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_settlements (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                pump_no INTEGER NOT NULL,
                staff_id TEXT NOT NULL,
                otp_amount REAL NOT NULL,
                settled_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'Pending',
                remarks TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()

    # Seed initial system configuration if empty
    seed_default_data()

def seed_default_data():
    """Populates basic pumps, staff, rates, and settings if not present."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Pumps
        cursor.execute("SELECT COUNT(*) as cnt FROM pumps")
        if cursor.fetchone()["cnt"] == 0:
            cursor.executemany("""
                INSERT INTO pumps (pump_no, pump_name, fuel_types) VALUES (?, ?, ?)
            """, [
                (1, "Pump 1 (Petrol & Diesel)", "MS,HSD"),
                (2, "Pump 2 (Petrol & Diesel)", "MS,HSD"),
                (3, "Pump 3 (CNG)", "CNG")
            ])

        # Settings
        default_settings = {
            "bunk_name": "NLK Filling Station - HPCL",
            "pRate": "116.96",
            "dRate": "105.01",
            "cRate": "114.00",
            "tank_cap_petrol": "20000",
            "tank_cap_diesel": "20000",
            "tank_cap_cng": "5000"
        }
        for k, v in default_settings.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                           (k, v, datetime.now().isoformat()))

        # Staff
        cursor.execute("SELECT COUNT(*) as cnt FROM staff")
        if cursor.fetchone()["cnt"] == 0:
            cursor.executemany("""
                INSERT INTO staff (staff_id, staff_name, role, mobile, pin, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("OWN001", "Super Admin / Owner", "Owner", "9988776655", "1111", "Active", datetime.now().isoformat()),
                ("MGR001", "Manager", "Manager", "9876543210", "1234", "Active", datetime.now().isoformat()),
                ("EMP001", "Shankar (Staff)", "Employee", "9123456780", "1234", "Active", datetime.now().isoformat()),
                ("EMP002", "Pavani (Staff)", "Employee", "9123456781", "1234", "Active", datetime.now().isoformat()),
                ("EMP003", "Ramesh (Staff)", "Employee", "9123456782", "1234", "Active", datetime.now().isoformat())
            ])

        conn.commit()

# --- Settings ---
def get_settings():
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}

def set_setting(key, value):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (key, str(value), datetime.now().isoformat()))
        conn.commit()

# --- Staff ---
def get_staff_list(active_only=False):
    with get_connection() as conn:
        sql = "SELECT * FROM staff" + (" WHERE status='Active'" if active_only else "") + " ORDER BY staff_id"
        return [dict(r) for r in conn.execute(sql).fetchall()]

def authenticate_staff(staff_id, pin):
    staff_id = str(staff_id).strip().upper()
    pin = str(pin).strip()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM staff WHERE staff_id=? AND pin=? AND status='Active'", (staff_id, pin)).fetchone()
        if row:
            return dict(row)
        # Fallback master PINs for owner/manager recovery
        if staff_id in ('OWN001', 'ADMIN') and pin in ('1111', '1234', '9999'):
            return {"staff_id": "OWN001", "staff_name": "Super Admin / Owner", "role": "Owner", "status": "Active"}
        if staff_id == 'MGR001' and pin in ('1234', '2222'):
            return {"staff_id": "MGR001", "staff_name": "Manager", "role": "Manager", "status": "Active"}
    return None

def save_staff(data):
    staff_id = str(data.get("staff_id", "")).strip().upper()
    name = str(data.get("staff_name", "")).strip()
    role = str(data.get("role", "Employee")).strip()
    mobile = str(data.get("mobile", "")).strip()
    pin = str(data.get("pin", "1234")).strip()
    status = str(data.get("status", "Active")).strip()
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO staff (staff_id, staff_name, role, mobile, pin, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(staff_id) DO UPDATE SET
                staff_name=excluded.staff_name, role=excluded.role, mobile=excluded.mobile,
                pin=excluded.pin, status=excluded.status
        """, (staff_id, name, role, mobile, pin, status, now))
        conn.commit()
    return True

# --- Last Closing (Auto-Prefill) ---
def get_last_closing(pump_no, target_date=None):
    """
    Returns closing readings of the previous shift for the specified pump
    to automatically prefill as opening readings for today!
    """
    pump_no = int(pump_no)
    closing_obj = {
        "Petrol_1": {"closing": 0.0},
        "Petrol_2": {"closing": 0.0},
        "Diesel_1": {"closing": 0.0},
        "Diesel_2": {"closing": 0.0},
        "CNG_1": {"closing": 0.0},
        "CNG_2": {"closing": 0.0}
    }
    
    with get_connection() as conn:
        sql = "SELECT shift_id, date FROM shifts WHERE pump_no=?"
        params = [pump_no]
        if target_date:
            sql += " AND date <= ?"
            params.append(str(target_date)[:10])
        sql += " ORDER BY date DESC, created_at DESC LIMIT 1"
        
        last_shift = conn.execute(sql, params).fetchone()
        if not last_shift:
            # If no shifts on or before target_date, try any latest shift
            last_shift = conn.execute("SELECT shift_id, date FROM shifts WHERE pump_no=? ORDER BY date DESC, created_at DESC LIMIT 1", [pump_no]).fetchone()
            
        if not last_shift:
            return {"found": False, "closing": closing_obj, "shift_id": None, "date": None}

        shift_id = last_shift["shift_id"]
        shift_date = last_shift["date"]

        readings = conn.execute("SELECT * FROM nozzle_readings WHERE shift_id=?", [shift_id]).fetchall()
        for r in readings:
            f = str(r["fuel_type"] or "").lower()
            n = int(r["nozzle_no"] or 1)
            val = float(r["closing_reading"] or 0)
            if "petrol" in f or f == "ms":
                if n == 1: closing_obj["Petrol_1"]["closing"] = val
                if n == 2: closing_obj["Petrol_2"]["closing"] = val
            elif "diesel" in f or f == "hsd":
                if n == 1: closing_obj["Diesel_1"]["closing"] = val
                if n == 2: closing_obj["Diesel_2"]["closing"] = val
            elif "cng" in f:
                if n == 1: closing_obj["CNG_1"]["closing"] = val
                if n == 2: closing_obj["CNG_2"]["closing"] = val

        return {
            "found": True,
            "shift_id": shift_id,
            "date": shift_date,
            "closing": closing_obj
        }

# --- Shifts CRUD ---
def save_shift(data):
    """
    Saves a complete shift record atomically with Nozzle Readings and Expenditures.
    """
    shift_id = str(data.get("shift_id") or data.get("Shift_ID") or f"SH-{datetime.now().strftime('%Y%m%d%H%M%S')}").strip()
    date_val = str(data.get("date") or data.get("Date") or datetime.now().strftime('%Y-%m-%d')).strip()[:10]
    shift_val = str(data.get("shift") or data.get("Shift") or 'S1').strip()
    pump_no = int(data.get("pump_no") or data.get("Pump_No") or 1)
    staff_id = str(data.get("staff_id") or data.get("Staff_ID") or 'EMP001').strip().upper()
    staff_name = str(data.get("staff_name") or data.get("Staff_Name") or staff_id).strip()
    now_str = datetime.now().isoformat()

    num = lambda v: float(v) if v is not None and str(v).strip() != '' else 0.0

    p_lit = num(data.get("petrol_litres") or data.get("Petrol_Litres"))
    p_amt = num(data.get("petrol_amount") or data.get("Petrol_Amount"))
    d_lit = num(data.get("diesel_litres") or data.get("Diesel_Litres"))
    d_amt = num(data.get("diesel_amount") or data.get("Diesel_Amount"))
    c_kg  = num(data.get("cng_kg") or data.get("CNG_KG"))
    c_amt = num(data.get("cng_amount") or data.get("CNG_Amount"))
    sales = num(data.get("total_sales") or data.get("Total_Sales")) or (p_amt + d_amt + c_amt)

    online = num(data.get("online_amount") or data.get("Online_Amount"))
    otp    = num(data.get("otp_amount") or data.get("OTP_Amount"))
    hp_pay = num(data.get("hp_pay_amount") or data.get("HP_Pay_Amount"))
    cash   = num(data.get("cash_total") or data.get("Cash_Total"))
    test_amt = num(data.get("testing_amount") or data.get("Testing_Amount"))

    exp_details = data.get("expenditure_details") or data.get("Expenditure_Details") or []
    exp_total = sum(num(x.get("amount") or x.get("Amount")) for x in exp_details) if exp_details else num(data.get("expenditure") or data.get("Expenditure"))

    col = cash + online + otp + hp_pay
    diff = col + exp_total + test_amt - sales

    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Insert/Replace Shift
        cursor.execute("""
            INSERT OR REPLACE INTO shifts (
                shift_id, date, shift, pump_no, staff_id, staff_name,
                petrol_litres, petrol_amount, diesel_litres, diesel_amount,
                cng_kg, cng_amount, total_sales,
                online_amount, otp_amount, hp_pay_amount, cash_total,
                expenditure, expenditure_type, expenditure_remarks, testing_amount,
                total_collected, difference, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            shift_id, date_val, shift_val, pump_no, staff_id, staff_name,
            p_lit, p_amt, d_lit, d_amt, c_kg, c_amt, sales,
            online, otp, hp_pay, cash, exp_total,
            exp_details[0].get("Expense_Type", "General") if exp_details else "General",
            "", test_amt, col, diff, "Saved", now_str, now_str
        ))

        # 2. Insert Nozzle Readings
        cursor.execute("DELETE FROM nozzle_readings WHERE shift_id=?", (shift_id,))
        readings = data.get("nozzle_readings") or data.get("Nozzle_Readings") or []
        for idx, nr in enumerate(readings):
            rid = str(nr.get("reading_id") or f"RD-{shift_id}-{idx+1}")
            cursor.execute("""
                INSERT OR REPLACE INTO nozzle_readings (
                    reading_id, shift_id, date, pump_no, nozzle_no, fuel_type,
                    opening_reading, closing_reading, mid_reading, litres, rate, rate1, rate2,
                    slot1_litres, slot1_amount, slot2_litres, slot2_amount, amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rid, shift_id, date_val, pump_no,
                int(nr.get("nozzle_no") or nr.get("Nozzle_No") or 1),
                str(nr.get("fuel_type") or nr.get("Fuel_Type") or "Petrol"),
                num(nr.get("opening_reading") or nr.get("Opening_Reading")),
                num(nr.get("closing_reading") or nr.get("Closing_Reading")),
                num(nr.get("mid_reading") or nr.get("Mid_Reading")),
                num(nr.get("litres") or nr.get("Litres")),
                num(nr.get("rate") or nr.get("Rate")),
                num(nr.get("rate1") or nr.get("Rate1")),
                num(nr.get("rate2") or nr.get("Rate2")),
                num(nr.get("slot1_litres") or nr.get("Slot1_Litres")),
                num(nr.get("slot1_amount") or nr.get("Slot1_Amount")),
                num(nr.get("slot2_litres") or nr.get("Slot2_Litres")),
                num(nr.get("slot2_amount") or nr.get("Slot2_Amount")),
                num(nr.get("amount") or nr.get("Amount"))
            ))

        # 3. Insert Expenditures
        cursor.execute("DELETE FROM expenditures WHERE shift_id=?", (shift_id,))
        for idx, exp in enumerate(exp_details):
            amt = num(exp.get("amount") or exp.get("Amount"))
            if amt > 0:
                eid = str(exp.get("expense_id") or f"EXP-{shift_id}-{idx+1}")
                cursor.execute("""
                    INSERT INTO expenditures (expense_id, shift_id, date, pump_no, expense_type, amount, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    eid, shift_id, date_val, pump_no,
                    str(exp.get("expense_type") or exp.get("Expense_Type") or "General"),
                    amt,
                    str(exp.get("remarks") or exp.get("Remarks") or "")
                ))

        # 4. OTP Settlement entry if OTP > 0
        if otp > 0:
            cursor.execute("""
                INSERT OR IGNORE INTO otp_settlements (id, date, pump_no, staff_id, otp_amount, settled_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, 0, 'Pending', ?)
            """, (f"OTP-{shift_id}", date_val, pump_no, staff_id, otp, now_str))

        conn.commit()

    return {"ok": True, "shift_id": shift_id, "message": "Shift saved successfully"}

def get_shifts(date_from=None, date_to=None, pump_no=None, staff_id=None, limit=500):
    """Retrieves shifts with filter criteria."""
    with get_connection() as conn:
        sql = "SELECT * FROM shifts WHERE 1=1"
        params = []
        if date_from:
            sql += " AND date >= ?"
            params.append(str(date_from)[:10])
        if date_to:
            sql += " AND date <= ?"
            params.append(str(date_to)[:10])
        if pump_no:
            sql += " AND pump_no = ?"
            params.append(int(pump_no))
        if staff_id:
            sql += " AND staff_id = ?"
            params.append(str(staff_id).strip().upper())
        sql += " ORDER BY date DESC, created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        result = []
        for r in rows:
            s = dict(r)
            # Attach nozzle readings
            nr = conn.execute("SELECT * FROM nozzle_readings WHERE shift_id=? ORDER BY nozzle_no", (s["shift_id"],)).fetchall()
            s["nozzle_readings"] = [dict(x) for x in nr]
            # Attach expenditures
            exp = conn.execute("SELECT * FROM expenditures WHERE shift_id=?", (s["shift_id"],)).fetchall()
            s["expenditures"] = [dict(x) for x in exp]
            result.append(s)
        return result

def get_shift_by_id(shift_id):
    """Retrieves a single shift record with all sub-details."""
    with get_connection() as conn:
        r = conn.execute("SELECT * FROM shifts WHERE shift_id=?", (shift_id,)).fetchone()
        if not r:
            return None
        s = dict(r)
        nr = conn.execute("SELECT * FROM nozzle_readings WHERE shift_id=? ORDER BY nozzle_no", (shift_id,)).fetchall()
        s["nozzle_readings"] = [dict(x) for x in nr]
        exp = conn.execute("SELECT * FROM expenditures WHERE shift_id=?", (shift_id,)).fetchall()
        s["expenditures"] = [dict(x) for x in exp]
        return s

def delete_shift(shift_id):
    """Deletes a shift and its cascade dependencies."""
    with get_connection() as conn:
        conn.execute("DELETE FROM shifts WHERE shift_id=?", (shift_id,))
        conn.commit()
    return True

# --- Calendar Analysis (Double Entries & Mismatch Detection) ---
def get_calendar_analysis(year, month):
    """
    Analyzes shifts for the given month:
    - Counts entries per day
    - Identifies Double entries (if a single pump has > 1 shift on the same date)
    - Detects Mismatches (if previous shift's closing does not match current shift's opening)
    """
    prefix = f"{year:04d}-{month:02d}"
    with get_connection() as conn:
        # Load all shifts for the target month + a few prior days to check opening boundary
        shifts = conn.execute("""
            SELECT * FROM shifts 
            WHERE date LIKE ? 
            ORDER BY pump_no, date ASC, created_at ASC
        """, (f"{prefix}%",)).fetchall()

        by_date = {}
        # Pre-populate dates
        import calendar
        _, num_days = calendar.monthrange(year, month)
        for d in range(1, num_days + 1):
            d_str = f"{year:04d}-{month:02d}-{d:02d}"
            by_date[d_str] = {
                "date": d_str,
                "count": 0,
                "pumps": {},
                "double_pumps": [],
                "has_mismatch": False,
                "mismatches": [],
                "total_sales": 0.0,
                "shifts": []
            }

        # Pump sequence tracking for mismatch calculation
        pump_prev_closing = {} # pump_no -> { 'petrol_1': close, 'petrol_2': close, ... }

        # Check all shifts in chronological order
        all_sorted = conn.execute("""
            SELECT * FROM shifts ORDER BY date ASC, created_at ASC
        """).fetchall()

        for s in all_sorted:
            d_str = s["date"][:10]
            p_no = int(s["pump_no"])
            shift_id = s["shift_id"]
            
            readings = conn.execute("SELECT * FROM nozzle_readings WHERE shift_id=?", (shift_id,)).fetchall()
            
            # Check mismatch against previous shift of this same pump
            curr_openings = {}
            curr_closings = {}
            for nr in readings:
                key = f"{nr['fuel_type']}_{nr['nozzle_no']}".lower()
                curr_openings[key] = float(nr["opening_reading"] or 0)
                curr_closings[key] = float(nr["closing_reading"] or 0)

            # If there was a previous shift recorded for this pump, check if its closing == current opening
            mismatch_reasons = []
            if p_no in pump_prev_closing:
                prev = pump_prev_closing[p_no]
                for k, prev_close in prev.items():
                    curr_open = curr_openings.get(k, 0.0)
                    if prev_close > 0 and curr_open > 0 and abs(prev_close - curr_open) > 0.05:
                        mismatch_reasons.append(f"P{p_no} {k.upper()} Open ({curr_open:.2f}) != Prev Close ({prev_close:.2f})")

            # Update prev closing for this pump
            pump_prev_closing[p_no] = curr_closings

            # If this shift is in our current target month, record it
            if d_str in by_date:
                entry = by_date[d_str]
                entry["count"] += 1
                entry["total_sales"] += float(s["total_sales"] or 0)
                entry["pumps"][p_no] = entry["pumps"].get(p_no, 0) + 1
                if entry["pumps"][p_no] > 1 and f"P{p_no}" not in entry["double_pumps"]:
                    entry["double_pumps"].append(f"P{p_no}")
                if mismatch_reasons:
                    entry["has_mismatch"] = True
                    entry["mismatches"].extend(mismatch_reasons)
                entry["shifts"].append({"shift_id": shift_id, "pump_no": p_no, "sales": s["total_sales"]})

        return by_date

# --- Stock Purchases ---
def save_stock_purchase(data):
    pid = str(data.get("purchase_id") or f"PUR-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    pdate = str(data.get("purchase_date") or datetime.now().strftime('%Y-%m-%d'))[:10]
    fuel = str(data.get("fuel_type") or "Petrol")
    qty = float(data.get("quantity_kg") or 0)
    rate = float(data.get("rate") or 0)
    tot = float(data.get("total_amount") or (qty * rate))
    supplier = str(data.get("supplier") or "HPCL Terminal")
    inv = str(data.get("invoice_no") or "")
    pay = str(data.get("payment_type") or "Bank Transfer")
    rem = str(data.get("remarks") or "")
    now = datetime.now().isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO stock_purchases (
                purchase_id, purchase_date, fuel_type, quantity_kg, rate, total_amount,
                supplier, invoice_no, payment_type, remarks, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pid, pdate, fuel, qty, rate, tot, supplier, inv, pay, rem, now))
        conn.commit()
    return {"ok": True, "purchase_id": pid}

def get_stock_purchases():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM stock_purchases ORDER BY purchase_date DESC, created_at DESC").fetchall()
        return [dict(r) for r in rows]

# --- Database Backup & Restore ---
def backup_database():
    """Creates a timestamped copy of the fuel_bunk.db in the backups folder."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"fuel_bunk_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    with get_connection() as conn:
        # Checkpoint WAL if any
        conn.execute("VACUUM")
    shutil.copy2(DB_FILE, backup_path)
    return {"ok": True, "filename": backup_filename, "path": backup_path}

def list_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    files.sort(reverse=True)
    return files

def restore_database(backup_filename):
    """Restores database from a selected backup file."""
    src = os.path.join(BACKUP_DIR, backup_filename)
    if not os.path.isfile(src):
        return {"ok": False, "error": "Backup file not found"}
    
    # Take a safety backup first
    backup_database()
    shutil.copy2(src, DB_FILE)
    return {"ok": True, "message": "Database restored successfully"}

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_FILE)
    settings = get_settings()
    print("Settings:", settings)
    staff = get_staff_list()
    print(f"Loaded {len(staff)} staff members.")
