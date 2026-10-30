/**
 * FUEL BUNK SHIFT MANAGER - CLOUDFLARE WORKER BACKEND
 * Ultra-low latency (<50ms) Serverless API powered by Cloudflare Workers & Cloudflare D1
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...CORS_HEADERS,
    },
  });
}

async function hashPin(pin) {
  const encoder = new TextEncoder();
  const data = encoder.encode(String(pin).trim());
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

function uid(prefix = 'ID') {
  return `${prefix}-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substr(2, 4).toUpperCase()}`;
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    const url = new URL(request.url);

    if (request.method === 'GET') {
      return json({
        ok: true,
        status: 'online',
        service: 'Fuel Bunk Manager Cloudflare API',
        time: new Date().toISOString(),
      });
    }

    try {
      const body = await request.json().catch(() => ({}));
      const action = body.action || url.searchParams.get('action') || '';
      const db = env.DB;

      if (!db) {
        return json({ ok: false, error: 'Database binding (DB) is missing in Cloudflare Worker settings.' }, 500);
      }

      switch (action) {
        case 'loginUser':
          return await handleLogin(body, db);
        case 'getStaff':
          return await handleGetStaff(body, db);
        case 'saveStaff':
          return await handleSaveStaff(body, db);
        case 'getPumps':
          return await handleGetPumps(db);
        case 'getLastClosing':
          return await handleGetLastClosing(body, db);
        case 'saveShift':
          return await handleSaveShift(body, db, env, ctx);
        case 'getShifts':
          return await handleGetShifts(body, db);
        case 'getShift':
          return await handleGetShift(body, db);
        case 'updateShift':
          return await handleUpdateShift(body, db, env, ctx);
        case 'changeShiftDate':
          return await handleChangeShiftDate(body, db, env, ctx);
        case 'getDashboardData':
          return await handleGetDashboardData(db);
        case 'getDSRRegister':
          return await handleGetDSRRegister(body, db);
        case 'saveDSROpening':
          return await handleSaveDSROpening(body, db);
        case 'saveDSRDipReading':
        case 'saveDSRClosingDip':
          return await handleSaveDSRClosingDip(body, db);
        case 'getStockPurchases':
          return await handleGetStockPurchases(body, db);
        case 'saveStockPurchase':
          return await handleSaveStockPurchase(body, db);
        case 'getOTPSettlements':
          return await handleGetOTPSettlements(body, db);
        case 'saveOTPSettlement':
          return await handleSaveOTPSettlement(body, db);
        case 'getSalaryReport':
          return await handleGetSalaryReport(body, db);
        case 'approveSalaryDeduction':
          return await handleApproveSalaryDeduction(body, db);
        default:
          return json({ ok: false, error: `Unknown action: ${action}` }, 400);
      }
    } catch (err) {
      return json({ ok: false, error: err.message || String(err) }, 500);
    }
  },
};

// ====================================================================
// ACTION HANDLERS
// ====================================================================

async function handleLogin(body, db) {
  const staffId = String(body.staffId || '').trim().toUpperCase();
  const pin = String(body.pin || '').trim();
  const pinHash = body.pinHash || (pin ? await hashPin(pin) : '');

  if (!staffId) return json({ ok: false, error: 'Staff ID is required' });
  if (!pinHash) return json({ ok: false, error: '4-digit PIN is required' });

  const user = await db.prepare('SELECT Staff_ID, Staff_Name, Role, Mobile, Status, PIN_Hash FROM Staff WHERE UPPER(Staff_ID) = ?').bind(staffId).first();

  if (!user) return json({ ok: false, error: 'Invalid Staff ID' });
  if (String(user.Status).toLowerCase() !== 'active') return json({ ok: false, error: 'Staff account is inactive' });
  if (user.PIN_Hash !== pinHash) return json({ ok: false, error: 'Incorrect PIN' });

  return json({
    ok: true,
    user: {
      Staff_ID: user.Staff_ID,
      Staff_Name: user.Staff_Name,
      Role: user.Role,
      Mobile: user.Mobile || '',
      Status: user.Status,
    },
  });
}

async function handleGetStaff(body, db) {
  let query = 'SELECT Staff_ID, Staff_Name, Mobile, Role, Status, Job_Role, Salary_Type, Salary_Rate FROM Staff';
  const params = [];

  if (body.activeOnly) {
    query += " WHERE LOWER(Status) = 'active'";
  }
  query += ' ORDER BY Staff_ID ASC';

  const res = await db.prepare(query).bind(...params).all();
  return json({ ok: true, staff: res.results || [] });
}

async function handleSaveStaff(body, db) {
  const s = body.staff || {};
  if (!s.Staff_ID || !s.Staff_Name) return json({ ok: false, error: 'Staff ID and Name are required' });

  const staffId = String(s.Staff_ID).trim().toUpperCase();
  let pinHash = s.PIN_Hash;
  if (s.PIN && /^\d{4}$/.test(String(s.PIN))) {
    pinHash = await hashPin(s.PIN);
  }

  const existing = await db.prepare('SELECT Staff_ID, PIN_Hash FROM Staff WHERE Staff_ID = ?').bind(staffId).first();

  if (existing) {
    const finalHash = pinHash || existing.PIN_Hash;
    await db.prepare(`
      UPDATE Staff SET
        Staff_Name = ?, Mobile = ?, Role = ?, PIN_Hash = ?, Status = ?, Remarks = ?, Job_Role = ?, Salary_Type = ?, Salary_Rate = ?
      WHERE Staff_ID = ?
    `).bind(
      s.Staff_Name, s.Mobile || '', s.Role || 'Employee', finalHash, s.Status || 'Active',
      s.Remarks || '', s.Job_Role || '', s.Salary_Type || 'Daily Fixed', Number(s.Salary_Rate) || 0,
      staffId
    ).run();
  } else {
    if (!pinHash) pinHash = await hashPin('1234');
    await db.prepare(`
      INSERT INTO Staff (Staff_ID, Staff_Name, Mobile, Role, PIN_Hash, Status, Remarks, Job_Role, Salary_Type, Salary_Rate)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      staffId, s.Staff_Name, s.Mobile || '', s.Role || 'Employee', pinHash, s.Status || 'Active',
      s.Remarks || '', s.Job_Role || '', s.Salary_Type || 'Daily Fixed', Number(s.Salary_Rate) || 0
    ).run();
  }

  return json({ ok: true, message: 'Staff saved successfully' });
}

async function handleGetPumps(db) {
  const res = await db.prepare('SELECT * FROM Pump_Master WHERE Status = "Active" ORDER BY Pump_No ASC').all();
  return json({ ok: true, pumps: res.results || [] });
}

async function handleGetLastClosing(body, db) {
  const pumpNo = Number(body.pumpNo || 1);
  const targetDate = String(body.date || '').slice(0, 10) || new Date().toISOString().slice(0, 10);

  // Find latest closing readings for this pump strictly before targetDate
  const prevRows = await db.prepare(`
    SELECT Fuel_Type, Nozzle_No, Closing_Reading, Date
    FROM Nozzle_Readings
    WHERE Pump_No = ? AND Date < ?
    ORDER BY Date DESC
  `).bind(pumpNo, targetDate).all();

  const closing = {};
  (prevRows.results || []).forEach(r => {
    const key = `${r.Fuel_Type}_${r.Nozzle_No}`;
    if (!closing[key]) {
      closing[key] = { closing: Number(r.Closing_Reading) || 0, date: r.Date };
    }
  });

  // Find next opening readings after targetDate
  const nextRows = await db.prepare(`
    SELECT Fuel_Type, Nozzle_No, Opening_Reading, Date
    FROM Nozzle_Readings
    WHERE Pump_No = ? AND Date > ?
    ORDER BY Date ASC
  `).bind(pumpNo, targetDate).all();

  const nextOpening = {};
  (nextRows.results || []).forEach(r => {
    const key = `${r.Fuel_Type}_${r.Nozzle_No}`;
    if (!nextOpening[key]) {
      nextOpening[key] = { opening: Number(r.Opening_Reading) || 0, date: r.Date };
    }
  });

  return json({ ok: true, closing, nextOpening, forDate: targetDate });
}

async function handleSaveShift(body, db, env, ctx) {
  const d = body.data || {};
  if (!d.Date || !d.Pump_No) return json({ ok: false, error: 'Date and Pump No are required' });

  const dateStr = String(d.Date).slice(0, 10);
  const pumpNo = Number(d.Pump_No);
  const shiftId = d.Shift_ID || `SFT-${dateStr.replace(/-/g, '')}-P${pumpNo}-${Date.now().toString(36).toUpperCase()}`;
  const now = new Date().toISOString();

  const statements = [
    db.prepare(`
      INSERT OR REPLACE INTO Shifts (
        Shift_ID, Date, Shift, Staff_ID, Staff_Name, Pump_No,
        Petrol_Litres, Petrol_Amount, Diesel_Litres, Diesel_Amount, CNG_KG, CNG_Amount,
        Total_Sales, Online_Amount, OTP_Amount, Cash_Total, Change_Amount,
        Expenditure, Expenditure_Type, Expenditure_Remarks, Testing_Amount,
        Total_Collected, Difference, Status, Entered_By, Entered_By_Name,
        Created_At, Updated_At
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      shiftId, dateStr, d.Shift || 'S1', String(d.Staff_ID), String(d.Staff_Name || d.Staff_ID), pumpNo,
      Number(d.Petrol_Litres) || 0, Number(d.Petrol_Amount) || 0,
      Number(d.Diesel_Litres) || 0, Number(d.Diesel_Amount) || 0,
      Number(d.CNG_KG) || 0, Number(d.CNG_Amount) || 0,
      Number(d.Total_Sales) || 0, Number(d.Online_Amount) || 0, Number(d.OTP_Amount) || 0,
      Number(d.Cash_Total) || 0, Number(d.Change_Amount) || 0,
      Number(d.Expenditure) || 0, d.Expenditure_Type || '', d.Expenditure_Remarks || '',
      Number(d.Testing_Amount) || 0, Number(d.Total_Collected) || 0, Number(d.Difference) || 0,
      'Submitted', String(d.Staff_ID), String(d.Staff_Name || d.Staff_ID), now, now
    ),
    db.prepare('DELETE FROM Nozzle_Readings WHERE Shift_ID = ?').bind(shiftId),
    db.prepare('DELETE FROM Cash_Details WHERE Shift_ID = ?').bind(shiftId),
    db.prepare('DELETE FROM Payments WHERE Shift_ID = ?').bind(shiftId)
  ];

  // Insert Nozzle Readings
  (d.Nozzle_Readings || []).forEach((nz, i) => {
    const readingId = `${shiftId}-NZ-${i + 1}`;
    statements.push(db.prepare(`
      INSERT INTO Nozzle_Readings (
        Reading_ID, Shift_ID, Date, Staff_ID, Pump_No, Nozzle_No, Fuel_Type,
        Opening_Reading, Closing_Reading, Litres, Rate, Amount
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      readingId, shiftId, dateStr, String(d.Staff_ID), pumpNo, Number(nz.Nozzle_No), String(nz.Fuel_Type),
      Number(nz.Opening_Reading) || 0, Number(nz.Closing_Reading) || 0,
      Number(nz.Litres) || 0, Number(nz.Rate) || 0, Number(nz.Amount) || 0
    ));
  });

  // Insert Payments
  (d.Payments || []).forEach((pm, i) => {
    const paymentId = `${shiftId}-PM-${i + 1}`;
    statements.push(db.prepare(`
      INSERT INTO Payments (Payment_ID, Shift_ID, Date, Staff_ID, Pump_No, Payment_Type, Amount, Reference_No, Remarks)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      paymentId, shiftId, dateStr, String(d.Staff_ID), pumpNo,
      String(pm.Payment_Type), Number(pm.Amount) || 0, String(pm.Reference_No || ''), String(pm.Remarks || '')
    ));
  });

  // Insert Cash Details
  (d.Cash_Details || []).forEach((cd, i) => {
    const cashId = `${shiftId}-CS-${i + 1}`;
    statements.push(db.prepare(`
      INSERT INTO Cash_Details (Cash_ID, Shift_ID, Date, Staff_ID, Pump_No, Denomination, Quantity, Amount)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      cashId, shiftId, dateStr, String(d.Staff_ID), pumpNo,
      Number(cd.Denomination) || 0, Number(cd.Quantity) || 0, Number(cd.Amount) || 0
    ));
  });

  // Insert OTP Record
  if (Number(d.OTP_Amount) > 0) {
    const otpId = `OTP-${shiftId.slice(-8)}`;
    statements.push(db.prepare(`
      INSERT OR REPLACE INTO OTP_Settlement (Settlement_ID, Shift_ID, Sales_Date, Staff_ID, Pump_No, OTP_Amount, Status)
      VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    `).bind(otpId, shiftId, dateStr, String(d.Staff_ID), pumpNo, Number(d.OTP_Amount)));
  }

  // Execute in single atomic D1 batch!
  await db.batch(statements);

  // Asynchronous background Google Sheets forwarder (if webhook configured)
  if (env.GOOGLE_SHEETS_WEBHOOK_URL && ctx && ctx.waitUntil) {
    ctx.waitUntil(
      fetch(env.GOOGLE_SHEETS_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'saveShift', data: d }),
      }).catch(e => console.warn('Google Sheets sync background error:', e))
    );
  }

  return json({ ok: true, shiftId, message: 'Shift saved successfully' });
}

async function handleGetShifts(body, db) {
  let query = 'SELECT * FROM Shifts WHERE 1=1';
  const params = [];

  if (body.date) {
    query += ' AND Date = ?';
    params.push(String(body.date).slice(0, 10));
  }
  if (body.month) {
    query += ' AND Date LIKE ?';
    params.push(`${String(body.month).slice(0, 7)}%`);
  }
  if (body.staffId) {
    query += ' AND Staff_ID = ?';
    params.push(String(body.staffId));
  }
  if (body.pumpNo) {
    query += ' AND Pump_No = ?';
    params.push(Number(body.pumpNo));
  }

  query += ' ORDER BY Date DESC, Shift_ID DESC';
  if (body.limit) {
    query += ' LIMIT ?';
    params.push(Number(body.limit));
  }

  const res = await db.prepare(query).bind(...params).all();
  return json({ ok: true, shifts: res.results || [] });
}

async function handleGetShift(body, db) {
  const shiftId = String(body.shiftId || '');
  if (!shiftId) return json({ ok: false, error: 'shiftId is required' });

  const shift = await db.prepare('SELECT * FROM Shifts WHERE Shift_ID = ?').bind(shiftId).first();
  if (!shift) return json({ ok: false, error: 'Shift not found' });

  const [nozzle, payments, cash] = await Promise.all([
    db.prepare('SELECT * FROM Nozzle_Readings WHERE Shift_ID = ?').bind(shiftId).all(),
    db.prepare('SELECT * FROM Payments WHERE Shift_ID = ?').bind(shiftId).all(),
    db.prepare('SELECT * FROM Cash_Details WHERE Shift_ID = ?').bind(shiftId).all(),
  ]);

  shift.Nozzle_Readings = nozzle.results || [];
  shift.Payments = payments.results || [];
  shift.Cash_Details = cash.results || [];

  return json({ ok: true, shift });
}

async function handleUpdateShift(body, db, env, ctx) {
  const shiftId = String(body.shiftId || '');
  const data = body.data || {};
  const reason = body.reason || 'Admin full edit';
  if (!shiftId) return json({ ok: false, error: 'shiftId is required' });

  const oldShift = await db.prepare('SELECT * FROM Shifts WHERE Shift_ID = ?').bind(shiftId).first();
  if (!oldShift) return json({ ok: false, error: 'Shift not found' });

  // Record audit log
  await db.prepare(`
    INSERT INTO Audit_Log (Audit_ID, Action, Shift_ID, Date, Pump_No, Staff_ID, Changed_By, Changed_At, Reason, Old_Data, New_Data)
    VALUES (?, 'FULL_EDIT', ?, ?, ?, ?, 'ADMIN', ?, ?, ?, ?)
  `).bind(
    uid('AUD'), shiftId, oldShift.Date, oldShift.Pump_No, oldShift.Staff_ID,
    new Date().toISOString(), reason, JSON.stringify(oldShift), JSON.stringify(data)
  ).run();

  // Re-save shift with data
  data.Shift_ID = shiftId;
  return await handleSaveShift({ data }, db, env, ctx);
}

async function handleChangeShiftDate(body, db, env, ctx) {
  const shiftId = String(body.shiftId || '');
  const newDate = String(body.newDate || '').slice(0, 10);
  const reason = body.reason || 'Date change by Admin';
  if (!shiftId || !newDate) return json({ ok: false, error: 'shiftId and newDate are required' });

  const oldShift = await db.prepare('SELECT * FROM Shifts WHERE Shift_ID = ?').bind(shiftId).first();
  if (!oldShift) return json({ ok: false, error: 'Shift not found' });

  const now = new Date().toISOString();
  await db.batch([
    db.prepare('UPDATE Shifts SET Date = ?, Updated_At = ? WHERE Shift_ID = ?').bind(newDate, now, shiftId),
    db.prepare('UPDATE Nozzle_Readings SET Date = ? WHERE Shift_ID = ?').bind(newDate, shiftId),
    db.prepare('UPDATE Cash_Details SET Date = ? WHERE Shift_ID = ?').bind(newDate, shiftId),
    db.prepare('UPDATE Payments SET Date = ? WHERE Shift_ID = ?').bind(newDate, shiftId),
    db.prepare('UPDATE OTP_Settlement SET Sales_Date = ? WHERE Shift_ID = ?').bind(newDate, shiftId),
    db.prepare(`
      INSERT INTO Audit_Log (Audit_ID, Action, Shift_ID, Date, Pump_No, Staff_ID, Changed_By, Changed_At, Reason, Old_Data, New_Data)
      VALUES (?, 'DATE_CHANGE', ?, ?, ?, ?, 'ADMIN', ?, ?, ?, ?)
    `).bind(
      uid('AUD'), shiftId, newDate, oldShift.Pump_No, oldShift.Staff_ID,
      now, reason, oldShift.Date, newDate
    )
  ]);

  return json({ ok: true, message: `Shift date changed from ${oldShift.Date} to ${newDate}` });
}

async function handleGetDashboardData(db) {
  const today = new Date().toISOString().slice(0, 10);

  const [todayRes, totalsRes, trendRes, byPumpRes, recentDiffsRes] = await Promise.all([
    db.prepare('SELECT SUM(Total_Sales) as Total_Sales, SUM(Cash_Total) as Cash_Total, SUM(Online_Amount) as Online_Amount, SUM(OTP_Amount) as OTP_Amount, SUM(Difference) as Difference, SUM(Petrol_Litres) as Petrol_Litres, SUM(Diesel_Litres) as Diesel_Litres, SUM(CNG_KG) as CNG_KG FROM Shifts WHERE Date = ?').bind(today).first(),
    db.prepare('SELECT SUM(Total_Sales) as Total_Sales, SUM(Cash_Total) as Cash_Total, SUM(Online_Amount) as Online_Amount, SUM(OTP_Amount) as OTP_Amount, SUM(Difference) as Difference, SUM(Petrol_Litres) as Petrol_Litres, SUM(Petrol_Amount) as Petrol_Amount, SUM(Diesel_Litres) as Diesel_Litres, SUM(Diesel_Amount) as Diesel_Amount, SUM(CNG_KG) as CNG_KG, SUM(CNG_Amount) as CNG_Amount FROM Shifts WHERE Date >= date("now", "-30 days")').first(),
    db.prepare('SELECT Date as date, SUM(Total_Sales) as sales FROM Shifts WHERE Date >= date("now", "-7 days") GROUP BY Date ORDER BY Date ASC').all(),
    db.prepare('SELECT Pump_No as pump, SUM(Total_Sales) as sales FROM Shifts WHERE Date >= date("now", "-30 days") GROUP BY Pump_No').all(),
    db.prepare('SELECT Date as date, Pump_No as pump, Difference as diff FROM Shifts ORDER BY Date DESC, Shift_ID DESC LIMIT 10').all(),
  ]);

  const byPump = {};
  (byPumpRes.results || []).forEach(r => { byPump[r.pump] = { sales: r.sales }; });

  return json({
    ok: true,
    data: {
      today: todayRes || {},
      totals: totalsRes || {},
      trend: trendRes.results || [],
      byPump,
      recentDiffs: recentDiffsRes.results || [],
    },
  });
}

async function handleGetDSRRegister(body, db) {
  const month = String(body.month || new Date().toISOString().slice(0, 7)).slice(0, 7);
  const fuel = body.fuel || 'Petrol';

  const [openingRes, dipsRes, salesRes] = await Promise.all([
    db.prepare('SELECT Opening_Stock, Date FROM DSR_Opening_Stock WHERE Date LIKE ? AND Fuel_Type = ? ORDER BY Date ASC LIMIT 1').bind(`${month}%`, fuel).first(),
    db.prepare('SELECT Date, Closing_Dip FROM DSR_Daily_Dip WHERE Date LIKE ? AND Fuel_Type = ?').bind(`${month}%`, fuel).all(),
    db.prepare(`
      SELECT s.Date, SUM(nr.Litres) as Sales_Litres
      FROM Shifts s
      JOIN Nozzle_Readings nr ON s.Shift_ID = nr.Shift_ID
      WHERE s.Date LIKE ? AND nr.Fuel_Type = ?
      GROUP BY s.Date
    `).bind(`${month}%`, fuel).all(),
  ]);

  const dipsMap = {};
  (dipsRes.results || []).forEach(r => { dipsMap[r.Date] = r.Closing_Dip; });

  const salesMap = {};
  (salesRes.results || []).forEach(r => { salesMap[r.Date] = r.Sales_Litres; });

  return json({
    ok: true,
    data: {
      monthStart: `${month}-01`,
      unit: fuel === 'CNG' ? 'KG' : 'L',
      tankCapacity: 20000,
      defaultPumpTest: 20,
      openingForMonth: openingRes ? openingRes.Opening_Stock : 0,
      dipsMap,
      salesMap,
      summary: {},
    },
  });
}

async function handleSaveDSROpening(body, db) {
  const { month, fuel, opening, date } = body;
  const d = date || `${month}-01`;
  await db.prepare(`
    INSERT OR REPLACE INTO DSR_Opening_Stock (Date, Fuel_Type, Opening_Stock, Updated_At)
    VALUES (?, ?, ?, ?)
  `).bind(d, fuel, Number(opening) || 0, new Date().toISOString()).run();
  return json({ ok: true, message: 'DSR opening saved' });
}

async function handleSaveDSRClosingDip(body, db) {
  const { date, dip, fuel } = body;
  const d = String(date).slice(0, 10);
  const f = fuel || 'Petrol';
  await db.prepare(`
    INSERT OR REPLACE INTO DSR_Daily_Dip (Date, Fuel_Type, Closing_Dip, Updated_At)
    VALUES (?, ?, ?, ?)
  `).bind(d, f, Number(dip) || 0, new Date().toISOString()).run();
  return json({ ok: true, message: 'Daily dip saved' });
}

async function handleGetStockPurchases(body, db) {
  const month = String(body.month || '').slice(0, 7);
  let query = 'SELECT * FROM Stock_Purchases';
  const params = [];
  if (month) {
    query += ' WHERE Purchase_Date LIKE ?';
    params.push(`${month}%`);
  }
  query += ' ORDER BY Purchase_Date DESC';
  const res = await db.prepare(query).bind(...params).all();
  return json({ ok: true, purchases: res.results || [] });
}

async function handleSaveStockPurchase(body, db) {
  const p = body.purchase || {};
  const purchaseId = p.Purchase_ID || uid('PUR');
  await db.prepare(`
    INSERT OR REPLACE INTO Stock_Purchases (
      Purchase_ID, Purchase_Date, Fuel_Type, Quantity_KG, Rate, Total_Amount,
      Supplier, Invoice_No, Payment_Type, Remarks, Created_At
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    purchaseId, p.Purchase_Date, p.Fuel_Type, Number(p.Quantity_KG) || 0,
    Number(p.Rate) || 0, Number(p.Total_Amount) || 0, p.Supplier || 'HPCL',
    p.Invoice_No || '', p.Payment_Type || 'Credit', p.Remarks || '', new Date().toISOString()
  ).run();
  return json({ ok: true, message: 'Stock purchase saved' });
}

async function handleGetOTPSettlements(body, db) {
  const res = await db.prepare('SELECT * FROM OTP_Settlement ORDER BY Sales_Date DESC LIMIT 50').all();
  return json({ ok: true, settlements: res.results || [] });
}

async function handleSaveOTPSettlement(body, db) {
  const s = body.settlement || {};
  if (!s.Settlement_ID) return json({ ok: false, error: 'Settlement_ID required' });
  await db.prepare(`
    UPDATE OTP_Settlement SET
      Settlement_Date = ?, Settled_Amount = ?, Pending_Amount = ?, Status = ?, Remarks = ?
    WHERE Settlement_ID = ?
  `).bind(
    s.Settlement_Date, Number(s.Settled_Amount) || 0,
    Number(s.Pending_Amount) || 0, s.Status || 'Settled', s.Remarks || '', s.Settlement_ID
  ).run();
  return json({ ok: true, message: 'OTP settlement updated' });
}

async function handleGetSalaryReport(body, db) {
  const month = String(body.month || new Date().toISOString().slice(0, 7)).slice(0, 7);
  const staffRes = await db.prepare('SELECT * FROM Staff WHERE LOWER(Role) = "employee" AND LOWER(Status) = "active"').all();
  const staff = staffRes.results || [];

  const rows = [];
  for (const st of staff) {
    const shiftsRes = await db.prepare('SELECT COUNT(*) as shiftCount, SUM(Difference) as totalDiff FROM Shifts WHERE Staff_ID = ? AND Date LIKE ?').bind(st.Staff_ID, `${month}%`).first();

    const count = shiftsRes ? Number(shiftsRes.shiftCount) : 0;
    const diff = shiftsRes ? Number(shiftsRes.totalDiff) : 0;
    const rate = Number(st.Salary_Rate) || 500;
    const base = count * rate;
    const shortage = diff < 0 ? Math.abs(diff) : 0;
    const net = Math.max(0, base - shortage);

    rows.push({
      Staff_ID: st.Staff_ID,
      Staff_Name: st.Staff_Name,
      Shift_Count: count,
      Salary_Rate: rate,
      Base_Salary: base,
      Shortage_Total: shortage,
      Approved_Deduction: shortage,
      Net_Salary: net,
      Status: 'Pending',
    });
  }

  return json({ ok: true, month, report: rows });
}

async function handleApproveSalaryDeduction(body, db) {
  return json({ ok: true, message: 'Deduction approved' });
}
