"""
Fuel Bunk Manager - Native Windows Desktop Application
100% Offline Python GUI (Tkinter + TTK)
Zero external dependencies, works on any standard Python on Windows.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import (
    init_db, get_settings, set_setting, get_staff_list, save_staff,
    get_last_closing, save_shift, get_shifts, get_shift_by_id, delete_shift,
    get_calendar_analysis, save_stock_purchase, get_stock_purchases,
    backup_database, list_backups, restore_database
)

EXPENSE_CATEGORIES = [
    'Electricity', 'Generator Diesel', 'Tea & Snacks', 'Staff Food', 
    'Daily Wages', 'Machine Repair', 'Printing & Stationery', 'Local Transport', 'Advance', 'General'
]

class FuelBunkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fuel Bunk Manager · Offline Desktop Edition")
        self.geometry("1180x760")
        self.minsize(980, 640)
        
        # Configure Styles
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        self.configure(bg="#0b1329")
        self.style.configure(".", background="#0b1329", foreground="#f1f5f9", font=("Segoe UI", 10))
        self.style.configure("TNotebook", background="#0b1329", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#131f37", foreground="#94a3b8", padding=[14, 8], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])
        self.style.configure("Treeview", background="#131f37", fieldbackground="#131f37", foreground="#ffffff", rowheight=26, bordercolor="#223458")
        self.style.configure("Treeview.Heading", background="#1e293b", foreground="#94a3b8", font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", "#3b82f6")])

        # Header Frame
        hdr_frame = tk.Frame(self, bg="#0f172a", height=50)
        hdr_frame.pack(fill=tk.X, side=tk.TOP)
        
        tk.Label(hdr_frame, text="⛽ Fuel Bunk Manager", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#0f172a").pack(side=tk.LEFT, padx=16, pady=10)
        tk.Label(hdr_frame, text="100% Offline SQLite Edition", font=("Segoe UI", 9, "bold"), fg="#34d399", bg="#0f172a").pack(side=tk.LEFT, padx=6)
        
        btn_quick_bk = tk.Button(hdr_frame, text="💾 1-Click Backup", bg="#1e293b", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=10, pady=4, command=self.quick_backup)
        btn_quick_bk.pack(side=tk.RIGHT, padx=16)

        # Main Notebook Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Tab Frames
        self.tab_entry = ttk.Frame(self.notebook)
        self.tab_shifts = ttk.Frame(self.notebook)
        self.tab_cal = ttk.Frame(self.notebook)
        self.tab_stock = ttk.Frame(self.notebook)
        self.tab_staff = ttk.Frame(self.notebook)
        self.tab_backup = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_entry, text=" ⛽ New Shift Entry ")
        self.notebook.add(self.tab_shifts, text=" 📋 Shift History ")
        self.notebook.add(self.tab_cal, text=" 📅 Shift Calendar ")
        self.notebook.add(self.tab_stock, text=" 🛢️ Fuel Purchases ")
        self.notebook.add(self.tab_staff, text=" 👥 Staff & Rates ")
        self.notebook.add(self.tab_backup, text=" 💾 Backup & Restore ")

        self.init_entry_tab()
        self.init_shifts_tab()
        self.init_cal_tab()
        self.init_stock_tab()
        self.init_staff_tab()
        self.init_backup_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def on_tab_change(self, event):
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 1:
            self.load_shifts()
        elif tab_idx == 2:
            self.load_calendar()
        elif tab_idx == 3:
            self.load_stock_table()
        elif tab_idx == 4:
            self.load_staff_table()
        elif tab_idx == 5:
            self.load_backup_list()

    # ==========================================
    # TAB 1: NEW SHIFT ENTRY
    # ==========================================
    def init_entry_tab(self):
        canvas = tk.Canvas(self.tab_entry, bg="#0b1329", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_entry, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#0b1329")

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Section 1: General Info
        sec1 = tk.LabelFrame(scroll_frame, text=" 1. Shift Information ", bg="#131f37", fg="#60a5fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        sec1.pack(fill=tk.X, padx=10, pady=6)

        row1 = tk.Frame(sec1, bg="#131f37")
        row1.pack(fill=tk.X)

        tk.Label(row1, text="Shift Date:", bg="#131f37", fg="#94a3b8").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.ent_date = tk.Entry(row1, bg="#0c1527", fg="#ffffff", font=("Segoe UI", 10, "bold"), insertbackground="white")
        self.ent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=0, column=1, padx=6, pady=4)
        self.ent_date.bind("<FocusOut>", lambda e: self.load_openings_for_pump())

        tk.Label(row1, text="Select Pump:", bg="#131f37", fg="#94a3b8").grid(row=0, column=2, sticky="w", padx=12, pady=4)
        self.cmb_pump = ttk.Combobox(row1, values=["Pump 1 (Petrol & Diesel)", "Pump 2 (Petrol & Diesel)", "Pump 3 (CNG)"], state="readonly", width=25)
        self.cmb_pump.current(0)
        self.cmb_pump.grid(row=0, column=3, padx=6, pady=4)
        self.cmb_pump.bind("<<ComboboxSelected>>", lambda e: self.load_openings_for_pump())

        tk.Label(row1, text="Duty Staff:", bg="#131f37", fg="#94a3b8").grid(row=0, column=4, sticky="w", padx=12, pady=4)
        self.cmb_staff = ttk.Combobox(row1, state="readonly", width=22)
        self.cmb_staff.grid(row=0, column=5, padx=6, pady=4)
        self.refresh_staff_combobox()

        # Section 2: Nozzle Meter Readings
        self.sec2 = tk.LabelFrame(scroll_frame, text=" 2. Nozzle Meter Readings (Auto Prefilled) ", bg="#131f37", fg="#34d399", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        self.sec2.pack(fill=tk.X, padx=10, pady=6)

        self.noz_inputs = {}
        self.build_nozzle_inputs()

        # Section 3: Collections & Expenses
        sec3 = tk.LabelFrame(scroll_frame, text=" 3. Digital Collections & Multiple Expenditures ", bg="#131f37", fg="#c084fc", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        sec3.pack(fill=tk.X, padx=10, pady=6)

        row_pay = tk.Frame(sec3, bg="#131f37")
        row_pay.pack(fill=tk.X, pady=4)

        tk.Label(row_pay, text="Online / UPI ₹:", bg="#131f37", fg="#94a3b8").grid(row=0, column=0, sticky="w", padx=6)
        self.ent_online = tk.Entry(row_pay, bg="#0c1527", fg="#ffffff", insertbackground="white", width=14)
        self.ent_online.grid(row=0, column=1, padx=6)
        self.ent_online.bind("<KeyRelease>", lambda e: self.calc_tally())

        tk.Label(row_pay, text="HPCL OTP ₹:", bg="#131f37", fg="#94a3b8").grid(row=0, column=2, sticky="w", padx=10)
        self.ent_otp = tk.Entry(row_pay, bg="#0c1527", fg="#ffffff", insertbackground="white", width=14)
        self.ent_otp.grid(row=0, column=3, padx=6)
        self.ent_otp.bind("<KeyRelease>", lambda e: self.calc_tally())

        tk.Label(row_pay, text="HP Pay ₹:", bg="#131f37", fg="#94a3b8").grid(row=0, column=4, sticky="w", padx=10)
        self.ent_hp_pay = tk.Entry(row_pay, bg="#0c1527", fg="#ffffff", insertbackground="white", width=14)
        self.ent_hp_pay.grid(row=0, column=5, padx=6)
        self.ent_hp_pay.bind("<KeyRelease>", lambda e: self.calc_tally())

        tk.Label(row_pay, text="Testing ₹:", bg="#131f37", fg="#94a3b8").grid(row=0, column=6, sticky="w", padx=10)
        self.ent_testing = tk.Entry(row_pay, bg="#0c1527", fg="#ffffff", insertbackground="white", width=14)
        self.ent_testing.grid(row=0, column=7, padx=6)
        self.ent_testing.bind("<KeyRelease>", lambda e: self.calc_tally())

        # Expenses Box
        exp_box = tk.Frame(sec3, bg="#131f37")
        exp_box.pack(fill=tk.X, pady=10)
        
        tk.Label(exp_box, text="Shift Expenditures List:", bg="#131f37", fg="#f1f5f9", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        btn_add_exp = tk.Button(exp_box, text="+ Add Expense Row", bg="#1e293b", fg="#60a5fa", relief="flat", font=("Segoe UI", 8, "bold"), command=self.add_expense_row)
        btn_add_exp.pack(side=tk.RIGHT)

        self.exp_container = tk.Frame(sec3, bg="#131f37")
        self.exp_container.pack(fill=tk.X, pady=4)
        self.expense_rows = []

        # Section 4: Net Cash & Tally
        sec4 = tk.LabelFrame(scroll_frame, text=" 4. Net Cash Total & Live Difference Status ", bg="#131f37", fg="#f59e0b", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        sec4.pack(fill=tk.X, padx=10, pady=6)

        row_cash = tk.Frame(sec4, bg="#131f37")
        row_cash.pack(fill=tk.X, pady=6)

        tk.Label(row_cash, text="💵 Net Cash Total (Collected in Hand) ₹:", bg="#131f37", fg="#ffffff", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=6)
        self.ent_cash = tk.Entry(row_cash, bg="#0c1527", fg="#34d399", font=("Segoe UI", 13, "bold"), insertbackground="white", width=18)
        self.ent_cash.pack(side=tk.LEFT, padx=10)
        self.ent_cash.bind("<KeyRelease>", lambda e: self.calc_tally())

        self.lbl_tally = tk.Label(sec4, text="Total Sales: ₹ 0.00  |  Difference: ₹ 0.00 (Balanced ✅)", bg="#10b981", fg="#ffffff", font=("Segoe UI", 11, "bold"), pady=8)
        self.lbl_tally.pack(fill=tk.X, pady=8)

        # Action Buttons
        btn_bar = tk.Frame(scroll_frame, bg="#0b1329")
        btn_bar.pack(fill=tk.X, padx=10, pady=14)

        btn_save = tk.Button(btn_bar, text="💾 Save Shift Record to Offline Database", bg="#10b981", fg="#ffffff", font=("Segoe UI", 11, "bold"), relief="flat", padx=20, pady=8, command=self.save_shift_action)
        btn_save.pack(side=tk.RIGHT)

        btn_reset = tk.Button(btn_bar, text="Reset Form", bg="#1e293b", fg="#94a3b8", font=("Segoe UI", 10), relief="flat", padx=14, pady=8, command=self.reset_entry_form)
        btn_reset.pack(side=tk.RIGHT, padx=10)

        # Trigger initial opening prefill
        self.load_openings_for_pump()

    def refresh_staff_combobox(self):
        staff_list = get_staff_list(active_only=True)
        items = [f"{s['staff_id']} - {s['staff_name']}" for s in staff_list]
        self.cmb_staff['values'] = items
        if items:
            self.cmb_staff.current(0)

    def build_nozzle_inputs(self):
        for widget in self.sec2.winfo_children():
            widget.destroy()

        p_idx = self.cmb_pump.current()
        is_cng = (p_idx == 2)
        settings = get_settings()

        headers = ["Fuel / Nozzle", "Opening Reading (Auto)", "Closing Reading", "Litres / KG", "Rate ₹", "Amount ₹"]
        for col, h in enumerate(headers):
            tk.Label(self.sec2, text=h, bg="#131f37", fg="#94a3b8", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, padx=8, pady=4, sticky="w")

        self.noz_inputs = {}

        if not is_cng:
            nozzles = [
                ("Petrol_1", "MS Petrol N1", settings.get("pRate", "116.96")),
                ("Petrol_2", "MS Petrol N2", settings.get("pRate", "116.96")),
                ("Diesel_1", "HSD Diesel N1", settings.get("dRate", "105.01")),
                ("Diesel_2", "HSD Diesel N2", settings.get("dRate", "105.01"))
            ]
        else:
            nozzles = [
                ("CNG_1", "CNG Nozzle 1", settings.get("cRate", "114.00")),
                ("CNG_2", "CNG Nozzle 2", settings.get("cRate", "114.00"))
            ]

        for idx, (key, label, default_rate) in enumerate(nozzles, start=1):
            tk.Label(self.sec2, text=label, bg="#131f37", fg="#ffffff", font=("Segoe UI", 9, "bold")).grid(row=idx, column=0, padx=8, pady=4, sticky="w")
            
            ent_open = tk.Entry(self.sec2, bg="#0c1527", fg="#ffffff", insertbackground="white", width=16)
            ent_open.grid(row=idx, column=1, padx=6, pady=4)
            ent_open.bind("<KeyRelease>", lambda e: self.calc_tally())

            ent_close = tk.Entry(self.sec2, bg="#0c1527", fg="#ffffff", insertbackground="white", width=16)
            ent_close.grid(row=idx, column=2, padx=6, pady=4)
            ent_close.bind("<KeyRelease>", lambda e: self.calc_tally())

            lbl_lit = tk.Label(self.sec2, text="0.00", bg="#131f37", fg="#60a5fa", font=("Segoe UI", 10, "bold"), width=12, anchor="w")
            lbl_lit.grid(row=idx, column=3, padx=6, pady=4)

            ent_rate = tk.Entry(self.sec2, bg="#0c1527", fg="#ffffff", insertbackground="white", width=12)
            ent_rate.insert(0, str(default_rate))
            ent_rate.grid(row=idx, column=4, padx=6, pady=4)
            ent_rate.bind("<KeyRelease>", lambda e: self.calc_tally())

            lbl_amt = tk.Label(self.sec2, text="₹ 0.00", bg="#131f37", fg="#34d399", font=("Segoe UI", 10, "bold"), width=14, anchor="w")
            lbl_amt.grid(row=idx, column=5, padx=6, pady=4)

            self.noz_inputs[key] = {
                "open": ent_open,
                "close": ent_close,
                "lit_lbl": lbl_lit,
                "rate": ent_rate,
                "amt_lbl": lbl_amt
            }

    def load_openings_for_pump(self):
        p_no = self.cmb_pump.current() + 1
        d_val = self.ent_date.get().strip() or datetime.now().strftime("%Y-%m-%d")

        self.build_nozzle_inputs()

        res = get_last_closing(p_no, d_val)
        closing = res.get("closing", {})

        for key, fields in self.noz_inputs.items():
            if key in closing and closing[key].get("closing", 0) > 0:
                fields["open"].delete(0, tk.END)
                fields["open"].insert(0, str(closing[key]["closing"]))
        
        self.calc_tally()

    def add_expense_row(self, cat="General", amt="", rem=""):
        row_fr = tk.Frame(self.exp_container, bg="#131f37")
        row_fr.pack(fill=tk.X, pady=2)

        cmb_cat = ttk.Combobox(row_fr, values=EXPENSE_CATEGORIES, state="readonly", width=18)
        cmb_cat.set(cat)
        cmb_cat.pack(side=tk.LEFT, padx=4)

        ent_amt = tk.Entry(row_fr, bg="#0c1527", fg="#ffffff", insertbackground="white", width=14)
        if amt: ent_amt.insert(0, str(amt))
        ent_amt.pack(side=tk.LEFT, padx=6)
        ent_amt.bind("<KeyRelease>", lambda e: self.calc_tally())

        ent_rem = tk.Entry(row_fr, bg="#0c1527", fg="#ffffff", insertbackground="white", width=28)
        if rem: ent_rem.insert(0, str(rem))
        ent_rem.pack(side=tk.LEFT, padx=6)

        btn_del = tk.Button(row_fr, text="✕", bg="#ef4444", fg="#ffffff", font=("Segoe UI", 8, "bold"), relief="flat", command=lambda: self.remove_expense_row(row_fr))
        btn_del.pack(side=tk.LEFT, padx=4)

        self.expense_rows.append({"frame": row_fr, "cat": cmb_cat, "amt": ent_amt, "rem": ent_rem})
        self.calc_tally()

    def remove_expense_row(self, frame):
        for idx, item in enumerate(self.expense_rows):
            if item["frame"] == frame:
                self.expense_rows.pop(idx)
                break
        frame.destroy()
        self.calc_tally()

    def calc_tally(self):
        total_sales = 0.0

        for key, fields in self.noz_inputs.items():
            try:
                op = float(fields["open"].get() or 0)
                cl = float(fields["close"].get() or 0)
                rt = float(fields["rate"].get() or 0)
                lit = max(0.0, cl - op)
                amt = lit * rt
                fields["lit_lbl"].config(text=f"{lit:.2f}")
                fields["amt_lbl"].config(text=f"₹ {amt:.2f}")
                total_sales += amt
            except ValueError:
                pass

        try: online = float(self.ent_online.get() or 0)
        except ValueError: online = 0.0
        try: otp = float(self.ent_otp.get() or 0)
        except ValueError: otp = 0.0
        try: hp_pay = float(self.ent_hp_pay.get() or 0)
        except ValueError: hp_pay = 0.0
        try: cash = float(self.ent_cash.get() or 0)
        except ValueError: cash = 0.0
        try: test = float(self.ent_testing.get() or 0)
        except ValueError: test = 0.0

        exp_total = 0.0
        for item in self.expense_rows:
            try: exp_total += float(item["amt"].get() or 0)
            except ValueError: pass

        collected = cash + online + otp + hp_pay
        diff = collected + exp_total + test - total_sales

        if abs(diff) < 0.5:
            self.lbl_tally.config(bg="#10b981", text=f"Total Sales: ₹ {total_sales:,.2f}  |  Difference: ₹ 0.00 (Balanced ✅)")
        elif diff < 0:
            self.lbl_tally.config(bg="#ef4444", text=f"Total Sales: ₹ {total_sales:,.2f}  |  Difference: - ₹ {abs(diff):,.2f} (Short Cash ⚠️)")
        else:
            self.lbl_tally.config(bg="#f59e0b", text=f"Total Sales: ₹ {total_sales:,.2f}  |  Difference: + ₹ {diff:,.2f} (Excess Cash ℹ️)")

    def save_shift_action(self):
        p_no = self.cmb_pump.current() + 1
        d_val = self.ent_date.get().strip()
        staff_str = self.cmb_staff.get()
        staff_id = staff_str.split(" - ")[0] if " - " in staff_str else staff_str

        if not d_val:
            messagebox.showerror("Error", "Please specify a shift date.")
            return

        is_cng = (p_no == 3)
        nozzle_readings = []
        p_lit, p_amt, d_lit, d_amt, c_kg, c_amt = 0, 0, 0, 0, 0, 0

        for key, fields in self.noz_inputs.items():
            op = float(fields["open"].get() or 0)
            cl = float(fields["close"].get() or 0)
            rt = float(fields["rate"].get() or 0)
            lit = max(0.0, cl - op)
            amt = lit * rt
            f_type = "CNG" if "CNG" in key else ("Petrol" if "Petrol" in key else "Diesel")
            noz_no = int(key.split("_")[1])

            if f_type == "Petrol": p_lit += lit; p_amt += amt
            elif f_type == "Diesel": d_lit += lit; d_amt += amt
            elif f_type == "CNG": c_kg += lit; c_amt += amt

            nozzle_readings.append({
                "nozzle_no": noz_no,
                "fuel_type": f_type,
                "opening_reading": op,
                "closing_reading": cl,
                "litres": lit,
                "rate": rt,
                "amount": amt
            })

        exp_details = []
        for item in self.expense_rows:
            try:
                amt = float(item["amt"].get() or 0)
                if amt > 0:
                    exp_details.append({
                        "expense_type": item["cat"].get(),
                        "amount": amt,
                        "remarks": item["rem"].get()
                    })
            except ValueError:
                pass

        payload = {
            "date": d_val,
            "pump_no": p_no,
            "staff_id": staff_id,
            "staff_name": staff_id,
            "petrol_litres": p_lit, "petrol_amount": p_amt,
            "diesel_litres": d_lit, "diesel_amount": d_amt,
            "cng_kg": c_kg, "cng_amount": c_amt,
            "total_sales": p_amt + d_amt + c_amt,
            "online_amount": float(self.ent_online.get() or 0),
            "otp_amount": float(self.ent_otp.get() or 0),
            "hp_pay_amount": float(self.ent_hp_pay.get() or 0),
            "cash_total": float(self.ent_cash.get() or 0),
            "testing_amount": float(self.ent_testing.get() or 0),
            "expenditure_details": exp_details,
            "nozzle_readings": nozzle_readings
        }

        res = save_shift(payload)
        if res.get("ok"):
            messagebox.showinfo("Success", f"Shift {res.get('shift_id')} successfully saved to offline SQLite database!")
            self.reset_entry_form()
            self.notebook.select(1) # Switch to shift history
        else:
            messagebox.showerror("Error", res.get("error", "Failed to save shift."))

    def reset_entry_form(self):
        for item in self.expense_rows:
            item["frame"].destroy()
        self.expense_rows.clear()
        self.ent_online.delete(0, tk.END)
        self.ent_otp.delete(0, tk.END)
        self.ent_hp_pay.delete(0, tk.END)
        self.ent_cash.delete(0, tk.END)
        self.ent_testing.delete(0, tk.END)
        self.load_openings_for_pump()

    # ==========================================
    # TAB 2: SHIFT HISTORY
    # ==========================================
    def init_shifts_tab(self):
        ctrl_frame = tk.Frame(self.tab_shifts, bg="#0b1329")
        ctrl_frame.pack(fill=tk.X, padx=10, pady=8)

        tk.Button(ctrl_frame, text="🔄 Refresh Records", bg="#1e293b", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", command=self.load_shifts).pack(side=tk.LEFT, padx=4)
        tk.Button(ctrl_frame, text="🗑️ Delete Selected Shift", bg="#ef4444", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", command=self.delete_selected_shift).pack(side=tk.RIGHT, padx=4)

        tree_cols = ("date", "pump", "staff", "sales", "cash", "online", "otp", "hp_pay", "exp", "diff")
        self.tree_shifts = ttk.Treeview(self.tab_shifts, columns=tree_cols, show="headings", height=20)
        
        self.tree_shifts.heading("date", text="Date")
        self.tree_shifts.heading("pump", text="Pump")
        self.tree_shifts.heading("staff", text="Staff ID")
        self.tree_shifts.heading("sales", text="Total Sales (₹)")
        self.tree_shifts.heading("cash", text="Net Cash (₹)")
        self.tree_shifts.heading("online", text="Online (₹)")
        self.tree_shifts.heading("otp", text="OTP (₹)")
        self.tree_shifts.heading("hp_pay", text="HP Pay (₹)")
        self.tree_shifts.heading("exp", text="Expenses (₹)")
        self.tree_shifts.heading("diff", text="Difference (₹)")

        self.tree_shifts.column("date", width=95)
        self.tree_shifts.column("pump", width=65)
        self.tree_shifts.column("staff", width=85)
        self.tree_shifts.column("sales", width=120)
        self.tree_shifts.column("cash", width=110)
        self.tree_shifts.column("online", width=95)
        self.tree_shifts.column("otp", width=95)
        self.tree_shifts.column("hp_pay", width=95)
        self.tree_shifts.column("exp", width=95)
        self.tree_shifts.column("diff", width=110)

        self.tree_shifts.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

    def load_shifts(self):
        for row in self.tree_shifts.get_children():
            self.tree_shifts.delete(row)
        
        shifts = get_shifts()
        for s in shifts:
            self.tree_shifts.insert("", tk.END, iid=s["shift_id"], values=(
                s["date"],
                f"P{s['pump_no']}",
                s["staff_id"],
                f"₹ {s['total_sales']:,.2f}",
                f"₹ {s['cash_total']:,.2f}",
                f"₹ {s['online_amount']:,.2f}",
                f"₹ {s['otp_amount']:,.2f}",
                f"₹ {s['hp_pay_amount']:,.2f}",
                f"₹ {s['expenditure']:,.2f}",
                f"₹ {s['difference']:,.2f}"
            ))

    def delete_selected_shift(self):
        sel = self.tree_shifts.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a shift from the list to delete.")
            return
        shift_id = sel[0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete shift {shift_id}?"):
            delete_shift(shift_id)
            self.load_shifts()
            messagebox.showinfo("Deleted", "Shift record removed.")

    # ==========================================
    # TAB 3: CALENDAR
    # ==========================================
    def init_cal_tab(self):
        hdr = tk.Frame(self.tab_cal, bg="#0b1329")
        hdr.pack(fill=tk.X, padx=14, pady=8)

        self.cal_year = datetime.now().year
        self.cal_month = datetime.now().month

        tk.Button(hdr, text="← Prev Month", bg="#1e293b", fg="#ffffff", relief="flat", command=self.cal_prev_month).pack(side=tk.LEFT)
        self.lbl_cal_title = tk.Label(hdr, text="", bg="#0b1329", fg="#ffffff", font=("Segoe UI", 12, "bold"))
        self.lbl_cal_title.pack(side=tk.LEFT, padx=14)
        tk.Button(hdr, text="Next Month →", bg="#1e293b", fg="#ffffff", relief="flat", command=self.cal_next_month).pack(side=tk.LEFT)

        self.cal_grid_frame = tk.Frame(self.tab_cal, bg="#0b1329")
        self.cal_grid_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)

    def cal_prev_month(self):
        self.cal_month -= 1
        if self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1
        self.load_calendar()

    def cal_next_month(self):
        self.cal_month += 1
        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        self.load_calendar()

    def load_calendar(self):
        for w in self.cal_grid_frame.winfo_children():
            w.destroy()

        import calendar
        month_name = calendar.month_name[self.cal_month]
        self.lbl_cal_title.config(text=f"{month_name} {self.cal_year}")

        cal_data = get_calendar_analysis(self.cal_year, self.cal_month)

        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for col, d in enumerate(days):
            tk.Label(self.cal_grid_frame, text=d, bg="#0b1329", fg="#94a3b8", font=("Segoe UI", 9, "bold")).grid(row=0, column=col, padx=4, pady=4)

        first_weekday, num_days = calendar.monthrange(self.cal_year, self.cal_month)
        # In Python calendar, Monday is 0. Convert to Sunday=0
        start_col = (first_weekday + 1) % 7

        today_str = datetime.now().strftime("%Y-%m-%d")
        row = 1
        col = start_col

        for day in range(1, num_days + 1):
            date_str = f"{self.cal_year:04d}-{self.cal_month:02d}-{day:02d}"
            info = cal_data.get(date_str, {})
            cnt = info.get("count", 0)
            is_entered = (cnt > 0)
            is_past = (date_str <= today_str)
            has_double = bool(info.get("double_pumps"))
            has_mis = info.get("has_mismatch", False)

            bg_color = "#131f37"
            fg_color = "#94a3b8"
            if is_entered:
                bg_color = "#064e3b" # dark green
                fg_color = "#34d399"
            elif is_past:
                bg_color = "#450a0a" # dark red
                fg_color = "#f87171"

            bd_color = "#f59e0b" if has_mis else "#1e293b"

            cell = tk.Frame(self.cal_grid_frame, bg=bg_color, highlightbackground=bd_color, highlightthickness=1.5, width=130, height=70)
            cell.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            cell.pack_propagate(False)

            tk.Label(cell, text=f"{day}", bg=bg_color, fg="#ffffff", font=("Segoe UI", 10, "bold")).pack(anchor="nw", padx=4, pady=2)
            
            badge_text = f"✅ {cnt} Shifts" if is_entered else ("⚠️ Missing" if is_past else "Upcoming")
            tk.Label(cell, text=badge_text, bg=bg_color, fg=fg_color, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=4)

            if has_double:
                tk.Label(cell, text=f"⚡ {','.join(info['double_pumps'])}", bg=bg_color, fg="#60a5fa", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=4)
            if has_mis:
                tk.Label(cell, text="⚠️ Mismatch", bg=bg_color, fg="#fbbf24", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=4)

            col += 1
            if col > 6:
                col = 0
                row += 1

    # ==========================================
    # TAB 4: STOCK PURCHASES
    # ==========================================
    def init_stock_tab(self):
        f = tk.LabelFrame(self.tab_stock, text=" Inward Fuel Stock Entry ", bg="#131f37", fg="#34d399", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        f.pack(fill=tk.X, padx=10, pady=6)

        r1 = tk.Frame(f, bg="#131f37")
        r1.pack(fill=tk.X)

        tk.Label(r1, text="Date:", bg="#131f37", fg="#94a3b8").grid(row=0, column=0, padx=4)
        self.ent_pdate = tk.Entry(r1, bg="#0c1527", fg="#ffffff", width=12)
        self.ent_pdate.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_pdate.grid(row=0, column=1, padx=4)

        tk.Label(r1, text="Fuel:", bg="#131f37", fg="#94a3b8").grid(row=0, column=2, padx=4)
        self.cmb_pfuel = ttk.Combobox(r1, values=["Petrol", "Diesel", "CNG"], state="readonly", width=10)
        self.cmb_pfuel.current(0)
        self.cmb_pfuel.grid(row=0, column=3, padx=4)

        tk.Label(r1, text="Qty (L/KG):", bg="#131f37", fg="#94a3b8").grid(row=0, column=4, padx=4)
        self.ent_pqty = tk.Entry(r1, bg="#0c1527", fg="#ffffff", width=12)
        self.ent_pqty.grid(row=0, column=5, padx=4)

        tk.Label(r1, text="Rate ₹:", bg="#131f37", fg="#94a3b8").grid(row=0, column=6, padx=4)
        self.ent_prate = tk.Entry(r1, bg="#0c1527", fg="#ffffff", width=10)
        self.ent_prate.grid(row=0, column=7, padx=4)

        tk.Button(r1, text="💾 Save Purchase", bg="#10b981", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", command=self.save_stock_action).grid(row=0, column=8, padx=10)

        # Purchases Table
        cols = ("date", "fuel", "qty", "rate", "total", "supplier", "invoice")
        self.tree_stock = ttk.Treeview(self.tab_stock, columns=cols, show="headings", height=15)
        for c in cols: self.tree_stock.heading(c, text=c.capitalize())
        self.tree_stock.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

    def save_stock_action(self):
        try:
            qty = float(self.ent_pqty.get() or 0)
            rt = float(self.ent_prate.get() or 0)
            save_stock_purchase({
                "purchase_date": self.ent_pdate.get(),
                "fuel_type": self.cmb_pfuel.get(),
                "quantity_kg": qty,
                "rate": rt,
                "total_amount": qty * rt,
                "supplier": "HPCL Terminal"
            })
            messagebox.showinfo("Saved", "Stock purchase record saved!")
            self.load_stock_table()
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values.")

    def load_stock_table(self):
        for r in self.tree_stock.get_children(): self.tree_stock.delete(r)
        for p in get_stock_purchases():
            self.tree_stock.insert("", tk.END, values=(p["purchase_date"], p["fuel_type"], p["quantity_kg"], f"₹ {p['rate']:.2f}", f"₹ {p['total_amount']:,.2f}", p["supplier"], p["invoice_no"]))

    # ==========================================
    # TAB 5: STAFF & SETTINGS
    # ==========================================
    def init_staff_tab(self):
        top_f = tk.Frame(self.tab_staff, bg="#0b1329")
        top_f.pack(fill=tk.X, padx=10, pady=6)

        f_rate = tk.LabelFrame(top_f, text=" Daily Fuel Rates (₹) ", bg="#131f37", fg="#60a5fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        f_rate.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        s = get_settings()
        tk.Label(f_rate, text="MS Petrol Rate ₹/L:", bg="#131f37", fg="#94a3b8").grid(row=0, column=0, pady=4, sticky="w")
        self.set_prate = tk.Entry(f_rate, bg="#0c1527", fg="#ffffff", width=12)
        self.set_prate.insert(0, s.get("pRate", "116.96"))
        self.set_prate.grid(row=0, column=1, pady=4)

        tk.Label(f_rate, text="HSD Diesel Rate ₹/L:", bg="#131f37", fg="#94a3b8").grid(row=1, column=0, pady=4, sticky="w")
        self.set_drate = tk.Entry(f_rate, bg="#0c1527", fg="#ffffff", width=12)
        self.set_drate.insert(0, s.get("dRate", "105.01"))
        self.set_drate.grid(row=1, column=1, pady=4)

        tk.Label(f_rate, text="CNG Rate ₹/KG:", bg="#131f37", fg="#94a3b8").grid(row=2, column=0, pady=4, sticky="w")
        self.set_crate = tk.Entry(f_rate, bg="#0c1527", fg="#ffffff", width=12)
        self.set_crate.insert(0, s.get("cRate", "114.00"))
        self.set_crate.grid(row=2, column=1, pady=4)

        tk.Button(f_rate, text="Save Rates", bg="#2563eb", fg="#ffffff", relief="flat", command=self.save_rates_action).grid(row=3, column=0, columnspan=2, pady=8)

        # Staff Table
        self.tree_staff = ttk.Treeview(self.tab_staff, columns=("id", "name", "role", "mobile", "status"), show="headings", height=12)
        for c in ("id", "name", "role", "mobile", "status"): self.tree_staff.heading(c, text=c.capitalize())
        self.tree_staff.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

    def save_rates_action(self):
        set_setting("pRate", self.set_prate.get().strip())
        set_setting("dRate", self.set_drate.get().strip())
        set_setting("cRate", self.set_crate.get().strip())
        messagebox.showinfo("Saved", "Daily fuel rates updated successfully.")

    def load_staff_table(self):
        for r in self.tree_staff.get_children(): self.tree_staff.delete(r)
        for s in get_staff_list():
            self.tree_staff.insert("", tk.END, values=(s["staff_id"], s["staff_name"], s["role"], s["mobile"] or "—", s["status"]))

    # ==========================================
    # TAB 6: BACKUP & RESTORE
    # ==========================================
    def init_backup_tab(self):
        f = tk.Frame(self.tab_backup, bg="#0b1329")
        f.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        tk.Label(f, text="Local SQLite Database Backups", font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#0b1329").pack(anchor="w", pady=4)
        tk.Label(f, text="Backups are stored inside fuel_bunk_offline/backups/. You can restore any snapshot with one click.", fg="#94a3b8", bg="#0b1329").pack(anchor="w", pady=2)

        tk.Button(f, text="Create New Backup Snapshot", bg="#10b981", fg="#ffffff", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6, command=self.quick_backup).pack(anchor="w", pady=10)

        self.listbox_backups = tk.Listbox(f, bg="#131f37", fg="#ffffff", font=("Consolas", 10), height=14)
        self.listbox_backups.pack(fill=tk.BOTH, expand=True, pady=6)

        btn_bar = tk.Frame(f, bg="#0b1329")
        btn_bar.pack(fill=tk.X, pady=6)
        tk.Button(btn_bar, text="Restore Selected Backup", bg="#ef4444", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4, command=self.restore_backup_action).pack(side=tk.LEFT)

    def quick_backup(self):
        res = backup_database()
        if res.get("ok"):
            messagebox.showinfo("Backup Created", f"Successfully backed up database to:\n{res.get('filename')}")
            self.load_backup_list()

    def load_backup_list(self):
        self.listbox_backups.delete(0, tk.END)
        for b in list_backups():
            self.listbox_backups.insert(tk.END, b)

    def restore_backup_action(self):
        sel = self.listbox_backups.curselection()
        if not sel:
            messagebox.showwarning("Select", "Please select a backup file to restore.")
            return
        filename = self.listbox_backups.get(sel[0])
        if messagebox.askyesno("Confirm Restore", f"Restoring will overwrite current database with {filename}.\nProceed?"):
            res = restore_database(filename)
            if res.get("ok"):
                messagebox.showinfo("Restored", "Database restored successfully!")
                self.load_shifts()
            else:
                messagebox.showerror("Error", res.get("error"))

if __name__ == "__main__":
    init_db()
    app = FuelBunkApp()
    app.mainloop()
