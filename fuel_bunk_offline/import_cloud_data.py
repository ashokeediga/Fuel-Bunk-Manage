"""
Optional Sync / Importer:
Imports existing historical data (Shifts, Staff, Rates, Purchases)
from Cloudflare into the local offline SQLite database.
Can be run once or anytime the user wants to sync offline.
"""

import urllib.request
import json
import os
import sys

from database import init_db, save_shift, save_staff, set_setting, save_stock_purchase

def import_all():
    init_db()
    url = "https://fuel-bunk-api.hp-nlkpump.workers.dev"
    print("Connecting to cloud endpoint to fetch existing data...")

    # 1. Fetch Staff
    try:
        req = urllib.request.Request(url, data=json.dumps({"action": "getStaff"}).encode("utf-8"),
                                     headers={"Content-Type": "text/plain", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            staff_list = data.get("staff", [])
            for s in staff_list:
                save_staff({
                    "staff_id": s.get("Staff_ID"),
                    "staff_name": s.get("Staff_Name"),
                    "role": s.get("Role", "Employee"),
                    "mobile": s.get("Mobile", ""),
                    "pin": s.get("PIN", "1234"),
                    "status": s.get("Status", "Active")
                })
            print(f"Successfully imported {len(staff_list)} staff members.")
    except Exception as e:
        print("Staff import note/skip:", e)

    # 2. Fetch Shifts
    try:
        req = urllib.request.Request(url, data=json.dumps({"action": "getShifts"}).encode("utf-8"),
                                     headers={"Content-Type": "text/plain", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            shifts = data.get("shifts", [])
            imported_count = 0
            for s in shifts:
                save_shift({
                    "shift_id": s.get("Shift_ID"),
                    "date": s.get("Date"),
                    "shift": s.get("Shift", "S1"),
                    "pump_no": s.get("Pump_No", 1),
                    "staff_id": s.get("Staff_ID"),
                    "staff_name": s.get("Staff_Name"),
                    "petrol_litres": s.get("Petrol_Litres"),
                    "petrol_amount": s.get("Petrol_Amount"),
                    "diesel_litres": s.get("Diesel_Litres"),
                    "diesel_amount": s.get("Diesel_Amount"),
                    "cng_kg": s.get("CNG_KG"),
                    "cng_amount": s.get("CNG_Amount"),
                    "total_sales": s.get("Total_Sales"),
                    "online_amount": s.get("Online_Amount"),
                    "otp_amount": s.get("OTP_Amount"),
                    "hp_pay_amount": s.get("HP_Pay_Amount"),
                    "cash_total": s.get("Cash_Total"),
                    "expenditure": s.get("Expenditure"),
                    "expenditure_details": s.get("Expenditure_Details", []),
                    "testing_amount": s.get("Testing_Amount"),
                    "nozzle_readings": s.get("Nozzle_Readings", [])
                })
                imported_count += 1
            print(f"Successfully imported {imported_count} shifts into local offline SQLite database!")
    except Exception as e:
        print("Shifts import note/skip:", e)

    # 3. Fetch Stock Purchases
    try:
        req = urllib.request.Request(url, data=json.dumps({"action": "getStockPurchases"}).encode("utf-8"),
                                     headers={"Content-Type": "text/plain", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            purchases = data.get("purchases", [])
            for p in purchases:
                save_stock_purchase({
                    "purchase_id": p.get("Purchase_ID"),
                    "purchase_date": p.get("Purchase_Date") or p.get("Date"),
                    "fuel_type": p.get("Fuel_Type"),
                    "quantity_kg": p.get("Quantity_KG"),
                    "rate": p.get("Rate"),
                    "total_amount": p.get("Total_Amount"),
                    "supplier": p.get("Supplier"),
                    "invoice_no": p.get("Invoice_No"),
                    "payment_type": p.get("Payment_Type"),
                    "remarks": p.get("Remarks")
                })
            print(f"Successfully imported {len(purchases)} stock purchases.")
    except Exception as e:
        print("Stock purchases import note/skip:", e)

if __name__ == "__main__":
    import_all()
