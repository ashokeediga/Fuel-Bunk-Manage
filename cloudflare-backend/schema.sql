-- ====================================================================
-- FUEL BUNK SHIFT MANAGER - CLOUDFLARE D1 (SQLITE) DATABASE SCHEMA
-- Ultra-fast serverless relational schema for Cloudflare D1
-- ====================================================================

-- 1. STAFF MASTER
CREATE TABLE IF NOT EXISTS Staff (
    Staff_ID TEXT PRIMARY KEY,
    Staff_Name TEXT NOT NULL,
    Mobile TEXT DEFAULT '',
    Role TEXT NOT NULL CHECK(Role IN ('Owner','Admin','Manager','Employee')),
    PIN_Hash TEXT NOT NULL,
    Status TEXT DEFAULT 'Active',
    Remarks TEXT DEFAULT '',
    Job_Role TEXT DEFAULT '',
    Salary_Type TEXT DEFAULT 'Daily Fixed',
    Salary_Rate REAL DEFAULT 0
);

-- 2. PUMPS MASTER
CREATE TABLE IF NOT EXISTS Pump_Master (
    Pump_No INTEGER PRIMARY KEY,
    Pump_Name TEXT NOT NULL,
    Nozzle_1 TEXT DEFAULT '',
    Nozzle_2 TEXT DEFAULT '',
    Status TEXT DEFAULT 'Active',
    Remarks TEXT DEFAULT ''
);

-- 3. SHIFTS TABLE
CREATE TABLE IF NOT EXISTS Shifts (
    Shift_ID TEXT PRIMARY KEY,
    Date TEXT NOT NULL,
    Shift TEXT DEFAULT 'S1',
    Staff_ID TEXT NOT NULL,
    Staff_Name TEXT NOT NULL,
    Pump_No INTEGER NOT NULL,
    Petrol_Litres REAL DEFAULT 0,
    Petrol_Amount REAL DEFAULT 0,
    Diesel_Litres REAL DEFAULT 0,
    Diesel_Amount REAL DEFAULT 0,
    CNG_KG REAL DEFAULT 0,
    CNG_Amount REAL DEFAULT 0,
    Total_Sales REAL DEFAULT 0,
    Online_Amount REAL DEFAULT 0,
    OTP_Amount REAL DEFAULT 0,
    Cash_Total REAL DEFAULT 0,
    Change_Amount REAL DEFAULT 0,
    Expenditure REAL DEFAULT 0,
    Expenditure_Type TEXT DEFAULT '',
    Expenditure_Remarks TEXT DEFAULT '',
    Testing_Amount REAL DEFAULT 0,
    Total_Collected REAL DEFAULT 0,
    Difference REAL DEFAULT 0,
    Status TEXT DEFAULT 'Submitted',
    Entered_By TEXT DEFAULT '',
    Entered_By_Name TEXT DEFAULT '',
    Created_At TEXT NOT NULL,
    Updated_At TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shifts_date ON Shifts(Date);
CREATE INDEX IF NOT EXISTS idx_shifts_pump ON Shifts(Pump_No);
CREATE INDEX IF NOT EXISTS idx_shifts_staff ON Shifts(Staff_ID);

-- 4. NOZZLE READINGS
CREATE TABLE IF NOT EXISTS Nozzle_Readings (
    Reading_ID TEXT PRIMARY KEY,
    Shift_ID TEXT NOT NULL,
    Date TEXT NOT NULL,
    Staff_ID TEXT NOT NULL,
    Pump_No INTEGER NOT NULL,
    Nozzle_No INTEGER NOT NULL,
    Fuel_Type TEXT NOT NULL,
    Opening_Reading REAL NOT NULL,
    Closing_Reading REAL NOT NULL,
    Litres REAL DEFAULT 0,
    Rate REAL DEFAULT 0,
    Amount REAL DEFAULT 0,
    FOREIGN KEY(Shift_ID) REFERENCES Shifts(Shift_ID) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nozzle_date_pump ON Nozzle_Readings(Date, Pump_No);
CREATE INDEX IF NOT EXISTS idx_nozzle_shift ON Nozzle_Readings(Shift_ID);

-- 5. CASH DETAILS
CREATE TABLE IF NOT EXISTS Cash_Details (
    Cash_ID TEXT PRIMARY KEY,
    Shift_ID TEXT NOT NULL,
    Date TEXT NOT NULL,
    Staff_ID TEXT NOT NULL,
    Pump_No INTEGER NOT NULL,
    Denomination INTEGER NOT NULL,
    Quantity INTEGER NOT NULL,
    Amount REAL NOT NULL,
    FOREIGN KEY(Shift_ID) REFERENCES Shifts(Shift_ID) ON DELETE CASCADE
);

-- 6. PAYMENTS (ONLINE, OTP, CASH, CREDIT)
CREATE TABLE IF NOT EXISTS Payments (
    Payment_ID TEXT PRIMARY KEY,
    Shift_ID TEXT NOT NULL,
    Date TEXT NOT NULL,
    Staff_ID TEXT NOT NULL,
    Pump_No INTEGER NOT NULL,
    Payment_Type TEXT NOT NULL,
    Amount REAL NOT NULL,
    Reference_No TEXT DEFAULT '',
    Remarks TEXT DEFAULT '',
    FOREIGN KEY(Shift_ID) REFERENCES Shifts(Shift_ID) ON DELETE CASCADE
);

-- 7. OTP SETTLEMENTS (HPCL / FLEET CARDS)
CREATE TABLE IF NOT EXISTS OTP_Settlement (
    Settlement_ID TEXT PRIMARY KEY,
    Shift_ID TEXT NOT NULL,
    Sales_Date TEXT NOT NULL,
    Staff_ID TEXT NOT NULL,
    Pump_No INTEGER NOT NULL,
    OTP_Amount REAL NOT NULL,
    Settlement_Date TEXT DEFAULT '',
    Settled_Amount REAL DEFAULT 0,
    Pending_Amount REAL DEFAULT 0,
    Status TEXT DEFAULT 'Pending',
    Remarks TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_otp_date ON OTP_Settlement(Sales_Date);

-- 8. STOCK PURCHASES (TANKER RECEIPT)
CREATE TABLE IF NOT EXISTS Stock_Purchases (
    Purchase_ID TEXT PRIMARY KEY,
    Purchase_Date TEXT NOT NULL,
    Fuel_Type TEXT NOT NULL,
    Quantity_KG REAL NOT NULL,
    Rate REAL NOT NULL,
    Total_Amount REAL NOT NULL,
    Supplier TEXT DEFAULT 'HPCL',
    Invoice_No TEXT DEFAULT '',
    Payment_Type TEXT DEFAULT 'Credit',
    Remarks TEXT DEFAULT '',
    Entered_By TEXT DEFAULT '',
    Entered_By_Name TEXT DEFAULT '',
    Created_At TEXT NOT NULL
);

-- 9. DSR REGISTERS (DAILY STOCK & SALES)
CREATE TABLE IF NOT EXISTS DSR_Opening_Stock (
    Date TEXT NOT NULL,
    Fuel_Type TEXT NOT NULL,
    Opening_Stock REAL NOT NULL,
    Remarks TEXT DEFAULT '',
    Entered_By TEXT DEFAULT '',
    Entered_By_Name TEXT DEFAULT '',
    Updated_At TEXT NOT NULL,
    PRIMARY KEY(Date, Fuel_Type)
);

CREATE TABLE IF NOT EXISTS DSR_Daily_Dip (
    Date TEXT NOT NULL,
    Fuel_Type TEXT NOT NULL,
    Closing_Dip REAL NOT NULL,
    Remarks TEXT DEFAULT '',
    Entered_By TEXT DEFAULT '',
    Entered_By_Name TEXT DEFAULT '',
    Updated_At TEXT NOT NULL,
    PRIMARY KEY(Date, Fuel_Type)
);

-- 10. SALARY DEDUCTIONS
CREATE TABLE IF NOT EXISTS Salary_Deductions (
    Deduction_ID TEXT PRIMARY KEY,
    Month TEXT NOT NULL,
    Staff_ID TEXT NOT NULL,
    Staff_Name TEXT NOT NULL,
    Shortage_Total REAL DEFAULT 0,
    Approved_Deduction REAL DEFAULT 0,
    Reason TEXT DEFAULT '',
    Approved_By TEXT DEFAULT '',
    Approved_By_Name TEXT DEFAULT '',
    Approved_At TEXT DEFAULT '',
    Status TEXT DEFAULT 'Pending'
);

-- 11. AUDIT LOG (TRACKS ALL EDITS & DATE CHANGES)
CREATE TABLE IF NOT EXISTS Audit_Log (
    Audit_ID TEXT PRIMARY KEY,
    Action TEXT NOT NULL,
    Shift_ID TEXT NOT NULL,
    Date TEXT NOT NULL,
    Pump_No INTEGER NOT NULL,
    Staff_ID TEXT NOT NULL,
    Changed_By TEXT NOT NULL,
    Changed_By_Name TEXT DEFAULT '',
    Changed_At TEXT NOT NULL,
    Reason TEXT DEFAULT '',
    Old_Data TEXT DEFAULT '',
    New_Data TEXT DEFAULT ''
);

-- 12. APP SETTINGS
CREATE TABLE IF NOT EXISTS Settings (
    Setting TEXT PRIMARY KEY,
    Value TEXT NOT NULL
);

-- ====================================================================
-- SEED DEFAULT DATA
-- ====================================================================

INSERT OR IGNORE INTO Staff (Staff_ID, Staff_Name, Role, PIN_Hash, Status) VALUES
('ADMIN', 'Super Admin', 'Owner', '03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4', 'Active'),
('OWN001', 'Owner', 'Owner', '0ffe1abd1a08215353c233d6e009613e95eec4253832a761af28ff37ac5a150c', 'Active'),
('MGR001', 'Manager', 'Manager', 'edee29f882543b956620b26d0ee0e7e950399b1c4222f5de05e06425b4c995e9', 'Active'),
('EMP001', 'Employee 1', 'Employee', '318aee3fed8c9d040d35a7fc1fa776fb31303833aa2de885354ddf3d44d8fb69', 'Active'),
('EMP002', 'Employee 2', 'Employee', '79f06f8fde333461739f220090a23cb2a79f6d714bee100d0e4b4af249294619', 'Active');

INSERT OR IGNORE INTO Pump_Master (Pump_No, Pump_Name, Nozzle_1, Nozzle_2, Status) VALUES
(1, 'Pump 1 (MS/HSD)', 'Petrol', 'Diesel', 'Active'),
(2, 'Pump 2 (MS/HSD)', 'Petrol', 'Diesel', 'Active'),
(3, 'Pump 3 (CNG)', 'CNG', 'CNG', 'Active');

INSERT OR IGNORE INTO Settings (Setting, Value) VALUES
('App_Name', 'Fuel Bunk Shift Manager'),
('Bunk_Name', 'NLK Filling Station'),
('DSR_Daily_Dip_Petrol', '20'),
('DSR_Daily_Dip_Diesel', '20'),
('DSR_Daily_Dip_CNG', '0'),
('DSR_Tank_Capacity_Petrol', '16000'),
('DSR_Tank_Capacity_Diesel', '25000'),
('DSR_Tank_Capacity_CNG', '0'),
('MS_Rate', '116.96'),
('HSD_Rate', '105.01'),
('CNG_Rate', '90.00');
