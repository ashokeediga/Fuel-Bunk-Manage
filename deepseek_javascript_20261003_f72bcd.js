/* ═══════════════════════════════════════════════════════════════
   Fuel Bunk Shift Manager — Google Apps Script Backend v16
   DSR Register (paper format) + Stock + Salary + OTP + Audit
   ═══════════════════════════════════════════════════════════════ */

const SHEETS = {
  SHIFTS: 'Shifts',
  NOZZLE: 'Nozzle_Readings',
  CASH: 'Cash_Details',
  PAYMENTS: 'Payments',
  OTP: 'OTP_Settlement',
  PUMPS: 'Pump_Master',
  STAFF: 'Staff',
  SETTINGS: 'Settings',
  AUDIT: 'Audit_Log',
  STOCK_PURCHASES: 'Stock_Purchases',
  EXPENDITURE: 'Expenditure_Details',
  DSR_OPENING: 'DSR_Opening_Stock',
  DSR_DIP: 'DSR_Daily_Dip',
  SALARY_DEDUCTIONS: 'Salary_Deductions'
};

const HEADERS = {
  Shifts: ["Shift_ID","Date","Staff_ID","Staff_Name","Pump_No","Petrol_Litres","Petrol_Amount","Diesel_Litres","Diesel_Amount","CNG_KG","CNG_Amount","Total_Sales","Online_Amount","OTP_Amount","Cash_Total","Change_Amount","Expenditure","Total_Collected","Difference","Status","Entered_By","Entered_By_Name","Created_At","Updated_At"],
  Nozzle_Readings: ["Reading_ID","Shift_ID","Date","Staff_ID","Pump_No","Nozzle_No","Fuel_Type","Opening_Reading","Closing_Reading","Litres","Rate","Amount"],
  Cash_Details: ["Cash_ID","Shift_ID","Date","Staff_ID","Pump_No","Denomination","Quantity","Amount"],
  Payments: ["Payment_ID","Shift_ID","Date","Staff_ID","Pump_No","Payment_Type","Amount","Reference_No","Remarks"],
  OTP_Settlement: ["Settlement_ID","Shift_ID","Sales_Date","Staff_ID","Pump_No","OTP_Amount","Settlement_Date","Settled_Amount","Pending_Amount","Status","Remarks"],
  Pump_Master: ["Pump_No","Pump_Name","Nozzle_1","Nozzle_2","Status","Remarks"],
  Staff: ["Staff_ID","Staff_Name","Mobile","Role","PIN_Hash","Status","Remarks","Job_Role","Salary_Type","Salary_Rate"],
  Settings: ["Setting","Value"],
  Audit_Log: ["Audit_ID","Action","Shift_ID","Date","Pump_No","Staff_ID","Changed_By","Changed_By_Name","Changed_At","Reason","Old_Data","New_Data"],
  Stock_Purchases: ["Purchase_ID","Purchase_Date","Fuel_Type","Quantity_KG","Rate","Total_Amount","Supplier","Invoice_No","Payment_Type","Remarks","Entered_By","Entered_By_Name","Created_At"],
  Expenditure_Details: ["Expenditure_ID","Shift_ID","Date","Staff_ID","Pump_No","Expenditure_Type","Amount","Remarks","Entered_By","Entered_By_Name","Created_At"],
  DSR_Opening_Stock: ["Date","Fuel_Type","Opening_Stock","Remarks","Entered_By","Entered_By_Name","Updated_At"],
  DSR_Daily_Dip: ["Date","Fuel_Type","Closing_Dip","Remarks","Entered_By","Entered_By_Name","Updated_At"],
  Salary_Deductions: ["Deduction_ID","Month","Staff_ID","Staff_Name","Shortage_Total","Approved_Deduction","Reason","Approved_By","Approved_By_Name","Approved_At","Status"]
};

/* ═══════════════════════ HTTP HANDLERS ═══════════════════════ */

function doGet(e) {
  return json_({ok:true, status:"ok", service:"Fuel Bunk Shift Manager API v16"});
}

function doPost(e) {
  try {
    const p = e && e.postData && e.postData.contents ? JSON.parse(e.postData.contents) : {};
    const action = p.action || '';
    if (action === 'setup') return json_(setupDefaultUsers_());
    let result;

    switch (action) {
      case 'loginUser': result = loginUser_(p); break;
      case 'getStaff': result = getStaff_(p); break;
      case 'saveStaff': result = saveStaff_(p); break;
      case 'getSalaryReport': result = getSalaryReport_(p); break;
      case 'approveSalaryDeduction': result = approveSalaryDeduction_(p); break;
      case 'getPumps': result = getPumps_(); break;
      case 'saveShift': result = saveShift_(p); break;
      case 'getShifts': result = getShifts_(p); break;
      case 'getShift': result = getShift_(p); break;
      case 'updateShift': result = updateShift_(p); break;
      case 'getLastClosing': result = getLastClosing_(p); break;
      case 'saveNozzleReadings': result = saveNozzleReadings_(p); break;
      case 'saveCashDetails': result = saveCashDetails_(p); break;
      case 'savePayment': result = savePayment_(p); break;
      case 'saveExpenditure': result = saveExpenditure_(p); break;
      case 'getExpenditures': result = getExpenditures_(p); break;
      case 'saveOTPSettlement': result = saveOTPSettlement_(p); break;
      case 'getOTPPending': result = getOTPPending_(p); break;
      case 'settleOTP': result = settleOTP_(p); break;
      case 'getOTPSettlements': result = getOTPSettlements_(); break;
      case 'saveStockPurchase': result = saveStockPurchase_(p); break;
      case 'getStockPurchases': result = getStockPurchases_(p); break;
      case 'getDashboard': result = getDashboard_(p); break;
      case 'getDashboardData': result = getDashboardData_(p); break;
      case 'getReportData': result = getReportData_(p); break;
      case 'getDSRData': result = getDSRData_(p); break;
      case 'getDSRRegister': result = getDSRRegister_(p); break;
      case 'saveDSROpening': result = saveDSROpening_(p); break;
      case 'saveDSRDip': result = saveDSRDip_(p); break;
      case 'saveDSRDipReading': result = saveDSRDipReading_(p); break;
      case 'saveSetting': result = saveSettingAction_(p); break;
      default: throw new Error('Unknown action: ' + action);
    }
    return json_(result);
  } catch (err) {
    return json_({ok:false, error:String(err.message || err)});
  }
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ss_() { return SpreadsheetApp.getActiveSpreadsheet(); }

/* ═══════════════════════ SETUP ═══════════════════════ */

function setupSheets_() {
  const ss = ss_();
  Object.keys(HEADERS).forEach(name => {
    let sh = ss.getSheetByName(name);
    if (!sh) sh = ss.insertSheet(name);
    const headers = HEADERS[name];
    const current = sh.getRange(1,1,1,headers.length).getValues()[0];
    const blank = current.every(v => v === '');
    if (sh.getLastRow() === 0 || blank) sh.getRange(1,1,1,headers.length).setValues([headers]);
    else {
      for (let i=0; i<headers.length; i++) {
        if (current[i] !== headers[i]) sh.getRange(1,i+1).setValue(headers[i]);
      }
    }
    sh.setFrozenRows(1);
  });
  // Add default pumps if empty
  const psh = ss.getSheetByName(SHEETS.PUMPS);
  if (psh.getLastRow() < 2) {
    psh.appendRow([1,"Pump 1","MS Nozzle 1 / HSD Nozzle 1","MS Nozzle 2 / HSD Nozzle 2","Active",""]);
    psh.appendRow([2,"Pump 2","MS Nozzle 1 / HSD Nozzle 1","MS Nozzle 2 / HSD Nozzle 2","Active",""]);
    psh.appendRow([3,"CNG Pump","CNG Nozzle 1","CNG Nozzle 2","Active","CNG pump"]);
  }
}

function setupDefaultUsers_() {
  setupSheets_();
  const sh = ss_().getSheetByName(SHEETS.STAFF);
  const rows = getObjects_(sh);
  const defaults = [
    ["OWN001","Owner","Owner","Active","1111"],
    ["MGR001","Manager","Manager","Active","2222"],
    ["EMP001","Employee 1","Employee","Active","3333"],
    ["EMP002","Employee 2","Employee","Active","4444"]
  ];
  const existing = {};
  rows.forEach(r => existing[String(r.Staff_ID)] = true);
  defaults.forEach(d => {
    if (!existing[d[0]]) {
      sh.appendRow([d[0],d[1],"",d[2],hashPin_(d[4]),d[3],"",d[2],"Daily Fixed",0]);
    }
  });
  // Default settings
  const stg = ss_().getSheetByName(SHEETS.SETTINGS);
  const setRows = getObjects_(stg);
  const defaults2 = [
    ["App_Name","Fuel Bunk Shift Manager"],
    ["Bunk_Name","NLK Filling Station"],
    ["DSR_Daily_Dip_Petrol",20],
    ["DSR_Daily_Dip_Diesel",20],
    ["DSR_Daily_Dip_CNG",0],
    ["DSR_Tank_Capacity_Petrol",16000],
    ["DSR_Tank_Capacity_Diesel",25000],
    ["DSR_Tank_Capacity_CNG",0]
  ];
  const setExist = {};
  setRows.forEach(r => setExist[String(r.Setting)] = true);
  defaults2.forEach(x => { if (!setExist[x[0]]) stg.appendRow(x); });

  return {ok:true, message:"Setup complete. Demo PINs: OWN001=1111, MGR001=2222, EMP001=3333, EMP002=4444. CHANGE before production."};
}

/* ═══════════════════════ UTILITIES ═══════════════════════ */

function hashPin_(pin) {
  if (!/^\d{4}$/.test(String(pin))) throw new Error('PIN must be exactly 4 digits');
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(pin), Utilities.Charset.UTF_8);
  return bytes.map(b => { const v = b < 0 ? b + 256 : b; return ('0' + v.toString(16)).slice(-2); }).join('');
}

function getObjects_(sh) {
  if (!sh || sh.getLastRow() < 2) return [];
  const vals = sh.getRange(1,1,sh.getLastRow(),sh.getLastColumn()).getValues();
  const headers = vals[0];
  return vals.slice(1).filter(row => row.some(v => v !== '')).map(row => {
    const o = {}; headers.forEach((h,i) => o[h] = row[i]); return o;
  });
}

function normalizeDate_(v) {
  if (v instanceof Date) return Utilities.formatDate(v, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  const s = String(v||'').trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  const m = s.match(/^(\d{1,2})[\/-](\d{1,2})[\/-](\d{4})$/);
  if (m) return m[3]+'-'+('0'+m[2]).slice(-2)+'-'+('0'+m[1]).slice(-2);
  return s;
}

function num_(v) { const n = Number(v); return isNaN(n) ? 0 : n; }

function findStaff_(id) {
  return getObjects_(ss_().getSheetByName(SHEETS.STAFF))
    .find(r => String(r.Staff_ID).toUpperCase() === String(id).toUpperCase());
}

function findShiftById_(id) {
  return getObjects_(ss_().getSheetByName(SHEETS.SHIFTS))
    .find(r => String(r.Shift_ID) === String(id));
}

function findShiftByDatePump_(date, pump) {
  return getObjects_(ss_().getSheetByName(SHEETS.SHIFTS))
    .find(r => normalizeDate_(r.Date) === normalizeDate_(date) && Number(r.Pump_No) === Number(pump));
}

function loginContext_(p) {
  if (!p.currentUser || !p.currentUser.Staff_ID) throw new Error('Login required');
  return p.currentUser;
}

function requireRole_(p, roles) {
  const user = loginContext_(p);
  if (!roles.includes(user.Role)) throw new Error('Permission denied');
  return user;
}

function addDays_(dateStr, n) {
  const p = dateStr.split('-').map(Number);
  const d = new Date(p[0], p[1]-1, p[2]);
  d.setDate(d.getDate() + n);
  return Utilities.formatDate(d, Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

function parseMonthRange_(month) {
  const m = String(month||'').match(/^(\d{4})-(\d{2})$/);
  if (!m) throw new Error('Month must be YYYY-MM');
  const y = Number(m[1]), mo = Number(m[2]);
  const start = Utilities.formatDate(new Date(y, mo-1, 1), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  const end = Utilities.formatDate(new Date(y, mo, 0), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  return {start, end};
}

function getSettingValue_(key, fallback) {
  const sh = ss_().getSheetByName(SHEETS.SETTINGS);
  if (!sh) return fallback;
  const r = getObjects_(sh).find(x => String(x.Setting) === String(key));
  return r && r.Value !== '' ? num_(r.Value) : fallback;
}

function saveSettingValue_(key, value) {
  let sh = ss_().getSheetByName(SHEETS.SETTINGS);
  if (!sh) { setupSheets_(); sh = ss_().getSheetByName(SHEETS.SETTINGS); }
  const rows = getObjects_(sh);
  const idx = rows.findIndex(x => String(x.Setting) === String(key));
  if (idx >= 0) sh.getRange(idx+2, 2).setValue(value);
  else sh.appendRow([key, value]);
}

/* ═══════════════════════ LOGIN ═══════════════════════ */

function loginUser_(p) {
  const id = String(p.staffId || '').trim().toUpperCase();
  const pin = String(p.pin || '').trim();
  const pinHash = String(p.pinHash || '').trim();
  if (!id) throw new Error('Enter User ID');
  if (pin && !/^\d{4}$/.test(pin)) throw new Error('PIN must be exactly 4 digits');
  if (!pin && !pinHash) throw new Error('PIN is required');

  const rows = getObjects_(ss_().getSheetByName(SHEETS.STAFF));
  const user = rows.find(r => String(r.Staff_ID).trim().toUpperCase() === id);
  if (!user) throw new Error('Invalid User ID');
  if (String(user.Status).toLowerCase() !== 'active') throw new Error('User is inactive');
  if (String(user.PIN_Hash) !== (pinHash || hashPin_(pin))) throw new Error('Invalid PIN');

  return {ok:true, user:{
    Staff_ID:String(user.Staff_ID),
    Staff_Name:String(user.Staff_Name),
    Role:String(user.Role),
    Mobile:String(user.Mobile || ''),
    Status:String(user.Status)
  }};
}

/* ═══════════════════════ STAFF ═══════════════════════ */

function getStaff_(p) {
  const rows = getObjects_(ss_().getSheetByName(SHEETS.STAFF));
  const activeOnly = p.activeOnly !== false;
  const role = p.role ? String(p.role).toLowerCase() : '';
  return {ok:true, staff: rows.filter(r =>
    (!activeOnly || String(r.Status).toLowerCase()==='active') &&
    (!role || String(r.Role).toLowerCase()===role)
  ).map(r => ({
    Staff_ID:String(r.Staff_ID), Staff_Name:String(r.Staff_Name),
    Mobile:String(r.Mobile||''), Role:String(r.Role),
    Job_Role:String(r.Job_Role||''), Salary_Type:String(r.Salary_Type||'Daily Fixed'),
    Salary_Rate:num_(r.Salary_Rate), Status:String(r.Status), Remarks:String(r.Remarks||'')
  }))};
}

function saveStaff_(p) {
  requireRole_(p, ['Owner']);
  const id = String(p.staffId||'').trim().toUpperCase();
  const name = String(p.staffName||'').trim();
  const role = String(p.role||'').trim();
  const jobRole = String(p.jobRole||'').trim();
  const salaryType = String(p.salaryType||'Daily Fixed').trim();
  const salaryRate = num_(p.salaryRate);
  const status = String(p.status||'Active').trim();
  const mobile = String(p.mobile||'').trim();
  const pin = String(p.pin||'').trim();
  const suppliedHash = String(p.pinHash||'').trim();

  if (!id || !name) throw new Error('Staff ID and Name are required');
  if (!['Employee','Manager','Owner'].includes(role)) throw new Error('Invalid access role');
  if (!['Monthly Fixed','Daily Fixed'].includes(salaryType)) throw new Error('Invalid salary type');
  if (salaryRate < 0) throw new Error('Salary rate cannot be negative');
  if (pin && !/^\d{4}$/.test(pin)) throw new Error('PIN must be exactly 4 digits');

  const sh = ss_().getSheetByName(SHEETS.STAFF);
  const rows = getObjects_(sh);
  const idx = rows.findIndex(r => String(r.Staff_ID).toUpperCase() === id);
  let pinHash = idx >= 0 ? String(rows[idx].PIN_Hash || '') : '';
  if (pin) pinHash = hashPin_(pin);
  else if (suppliedHash) pinHash = suppliedHash;
  if (!pinHash) throw new Error('4-digit PIN is required for a new user');

  const row = [id,name,mobile,role,pinHash,status,String(p.remarks||''),jobRole,salaryType,salaryRate];
  if (idx >= 0) sh.getRange(idx+2,1,1,row.length).setValues([row]);
  else sh.appendRow(row);
  return {ok:true,message:'Staff saved'};
}

/* ═══════════════════════ PUMPS ═══════════════════════ */

function getPumps_() {
  const rows = getObjects_(ss_().getSheetByName(SHEETS.PUMPS));
  return {ok:true,pumps:rows.map(r => ({
    Pump_No:String(r.Pump_No), Pump_Name:String(r.Pump_Name),
    Nozzle_1:String(r.Nozzle_1), Nozzle_2:String(r.Nozzle_2),
    Status:String(r.Status), Remarks:String(r.Remarks||'')
  }))};
}

/* ═══════════════════════ SHIFT SAVE ═══════════════════════ */

function saveShift_(p) {
  const user = loginContext_(p);
  const data = p.data || {};
  const staffId = String(data.Staff_ID || user.Staff_ID).trim().toUpperCase();
  const pump = Number(data.Pump_No);
  const date = normalizeDate_(data.Date);

  if (!date || !pump) throw new Error('Date and Pump are required');

  if (user.Role === 'Employee' && staffId !== String(user.Staff_ID).toUpperCase())
    throw new Error('Employee can only save own entry');
  if (!['Employee','Manager','Owner'].includes(user.Role)) throw new Error('Invalid role');

  const todayKey = normalizeDate_(new Date());
  if (date < todayKey && !['Manager','Owner'].includes(user.Role)) {
    throw new Error('Previous Date entry is allowed only for Manager or Owner');
  }

  const staff = findStaff_(staffId);
  if (!staff) throw new Error('Selected employee not found');
  if (String(staff.Status).toLowerCase() !== 'active') throw new Error('Selected user is inactive');

  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const existing = findShiftByDatePump_(date, pump);
    if (existing) throw new Error('Duplicate Entry: this date and pump already have a saved entry');

    const shiftId = 'SH-' + Utilities.getUuid().slice(0,8).toUpperCase();
    const now = new Date();

    const row = [
      shiftId, date, staffId, String(staff.Staff_Name), pump,
      num_(data.Petrol_Litres), num_(data.Petrol_Amount),
      num_(data.Diesel_Litres), num_(data.Diesel_Amount),
      num_(data.CNG_KG), num_(data.CNG_Amount),
      num_(data.Total_Sales), num_(data.Online_Amount), num_(data.OTP_Amount),
      num_(data.Cash_Total), num_(data.Change_Amount), num_(data.Expenditure),
      num_(data.Total_Collected), num_(data.Difference),
      String(data.Status || 'Saved'),
      String(user.Staff_ID), String(user.Staff_Name), now, now
    ];
    ss_().getSheetByName(SHEETS.SHIFTS).appendRow(row);

    saveRelatedTabs_(Object.assign({}, data, {
      Shift_ID: shiftId,
      Entered_By: user.Staff_ID,
      Entered_By_Name: user.Staff_Name
    }));

    return {ok:true, shiftId:shiftId, message:'Shift and all related tabs saved successfully'};
  } finally {
    lock.releaseLock();
  }
}

function saveRelatedTabs_(data) {
  saveNozzleReadings_({data:data});
  saveCashDetails_({data:data});
  savePayment_({data:data});

  if (num_(data.Expenditure) > 0) {
    saveExpenditure_({
      currentUser:{Staff_ID:data.Entered_By||'SYSTEM',Staff_Name:data.Entered_By_Name||'System',Role:'Owner'},
      data:{
        Shift_ID:data.Shift_ID, Date:data.Date, Staff_ID:data.Staff_ID, Pump_No:data.Pump_No,
        Amount:num_(data.Expenditure),
        Expenditure_Type:data.Expenditure_Type||'General',
        Remarks:data.Expenditure_Remarks||''
      }
    });
  }

  if (num_(data.OTP_Amount) > 0) {
    saveOTPSettlement_({
      data:{
        Shift_ID:data.Shift_ID, Date:data.Date, Staff_ID:data.Staff_ID, Pump_No:data.Pump_No,
        OTP_Amount:data.OTP_Amount, Settled_Amount:0,
        Remarks:'Initial OTP pending settlement'
      }
    });
  }
}

/* ═══════════════════════ SHIFTS GET ═══════════════════════ */

function getShifts_(p) {
  const user = loginContext_(p);
  const rows = getObjects_(ss_().getSheetByName(SHEETS.SHIFTS));
  let out = rows;
  if (user.Role === 'Employee') {
    out = rows.filter(r => String(r.Staff_ID).toUpperCase() === String(user.Staff_ID).toUpperCase());
  } else if (user.Role === 'Manager') {
    if (p.staffId) out = rows.filter(r => String(r.Staff_ID).toUpperCase() === String(p.staffId).toUpperCase());
    else out = [];
  } else if (user.Role === 'Owner') {
    if (p.staffId) out = rows.filter(r => String(r.Staff_ID).toUpperCase() === String(p.staffId).toUpperCase());
  }
  if (p.date) out = out.filter(r => normalizeDate_(r.Date) === normalizeDate_(p.date));
  return {ok:true,shifts:out.reverse().map(shiftPublic_)};
}

function getShift_(p) {
  const user = loginContext_(p);
  const id = String(p.shiftId||'');
  const row = findShiftById_(id);
  if (!row) throw new Error('Shift not found');
  if (user.Role === 'Employee' && String(row.Staff_ID).toUpperCase() !== String(user.Staff_ID).toUpperCase())
    throw new Error('Permission denied');
  return {ok:true,shift:buildFullShift_(row)};
}

function shiftPublic_(r) {
  const o={};
  HEADERS.Shifts.forEach(h => o[h] = r[h]);
  return o;
}

function buildFullShift_(row) {
  const shiftId = String(row.Shift_ID);
  return Object.assign({}, shiftPublic_(row), {
    Nozzle_Readings: getObjects_(ss_().getSheetByName(SHEETS.NOZZLE)).filter(r=>String(r.Shift_ID)===shiftId),
    Cash_Details: getObjects_(ss_().getSheetByName(SHEETS.CASH)).filter(r=>String(r.Shift_ID)===shiftId),
    Payments: getObjects_(ss_().getSheetByName(SHEETS.PAYMENTS)).filter(r=>String(r.Shift_ID)===shiftId),
    OTP_Settlement: getObjects_(ss_().getSheetByName(SHEETS.OTP)).filter(r=>String(r.Shift_ID)===shiftId),
    Expenditure_Details: getObjects_(ss_().getSheetByName(SHEETS.EXPENDITURE)).filter(r=>String(r.Shift_ID)===shiftId)
  });
}

/* ═══════════════════════ OWNER EDIT ═══════════════════════ */

function updateShift_(p) {
  const user = requireRole_(p, ['Owner']);
  const data = p.data || {};
  const shiftId = String(data.Shift_ID || '');
  const reason = String(p.reason || '').trim();
  if (!shiftId || !reason) throw new Error('Shift ID and edit reason are required');

  const sh = ss_().getSheetByName(SHEETS.SHIFTS);
  const rows = getObjects_(sh);
  const idx = rows.findIndex(r => String(r.Shift_ID) === shiftId);
  if (idx < 0) throw new Error('Shift not found');

  const old = buildFullShift_(rows[idx]);
  const newDate = normalizeDate_(data.Date);
  const newPump = Number(data.Pump_No);
  const duplicate = findShiftByDatePump_(newDate,newPump);
  if (duplicate && String(duplicate.Shift_ID) !== shiftId)
    throw new Error('Another entry already exists for this Date + Pump');

  const staffId = String(data.Staff_ID||rows[idx].Staff_ID).toUpperCase();
  const staff = findStaff_(staffId);
  if (!staff) throw new Error('Employee not found');

  const newRow = [
    shiftId,newDate,staffId,String(staff.Staff_Name),newPump,
    num_(data.Petrol_Litres),num_(data.Petrol_Amount),
    num_(data.Diesel_Litres),num_(data.Diesel_Amount),
    num_(data.CNG_KG),num_(data.CNG_Amount),
    num_(data.Total_Sales),num_(data.Online_Amount),num_(data.OTP_Amount),
    num_(data.Cash_Total),num_(data.Change_Amount),num_(data.Expenditure),
    num_(data.Total_Collected),num_(data.Difference),
    'Edited',String(rows[idx].Entered_By),String(rows[idx].Entered_By_Name),
    rows[idx].Created_At,new Date()
  ];
  sh.getRange(idx+2,1,1,newRow.length).setValues([newRow]);

  // Child records replace
  [SHEETS.NOZZLE,SHEETS.CASH,SHEETS.PAYMENTS,SHEETS.OTP,SHEETS.EXPENDITURE].forEach(name => {
    const csh = ss_().getSheetByName(name);
    const objs = getObjects_(csh);
    for (let i=objs.length-1;i>=0;i--) {
      if (String(objs[i].Shift_ID) === shiftId) csh.deleteRow(i+2);
    }
  });
  saveRelatedTabs_(Object.assign({}, data, {
    Entered_By: rows[idx].Entered_By,
    Entered_By_Name: rows[idx].Entered_By_Name
  }));

  const audit = ss_().getSheetByName(SHEETS.AUDIT);
  audit.appendRow([
    'AUD-'+Utilities.getUuid().slice(0,8).toUpperCase(),'EDIT',shiftId,newDate,newPump,staffId,
    user.Staff_ID,user.Staff_Name,new Date(),reason,JSON.stringify(old),JSON.stringify(data)
  ]);

  return {ok:true,message:'Owner edit saved with audit log'};
}

/* ═══════════════════════ CHILD SAVES ═══════════════════════ */

function saveNozzleReadings_(p) {
  const data = p.data || {};
  if (!data.Shift_ID) throw new Error('Shift_ID required');
  const sh = ss_().getSheetByName(SHEETS.NOZZLE);
  const arr = data.Nozzle_Readings || [];
  arr.forEach(x => sh.appendRow([
    'RD-'+Utilities.getUuid().slice(0,8).toUpperCase(),data.Shift_ID,normalizeDate_(data.Date),
    String(data.Staff_ID),Number(data.Pump_No),Number(x.Nozzle_No),String(x.Fuel_Type),
    num_(x.Opening_Reading),num_(x.Closing_Reading),num_(x.Litres),num_(x.Rate),num_(x.Amount)
  ]));
  return {ok:true};
}

function saveCashDetails_(p) {
  const data = p.data || {};
  if (!data.Shift_ID) throw new Error('Shift_ID required');
  const sh = ss_().getSheetByName(SHEETS.CASH);
  const arr = data.Cash_Details || [];
  arr.forEach(x => sh.appendRow([
    'CA-'+Utilities.getUuid().slice(0,8).toUpperCase(),data.Shift_ID,normalizeDate_(data.Date),
    String(data.Staff_ID),Number(data.Pump_No),Number(x.Denomination),Number(x.Quantity),num_(x.Amount)
  ]));
  return {ok:true};
}

function savePayment_(p) {
  const data = p.data || {};
  if (!data.Shift_ID) throw new Error('Shift_ID required');
  const sh = ss_().getSheetByName(SHEETS.PAYMENTS);
  const arr = data.Payments || [];
  arr.forEach(x => sh.appendRow([
    'PY-'+Utilities.getUuid().slice(0,8).toUpperCase(),data.Shift_ID,normalizeDate_(data.Date),
    String(data.Staff_ID),Number(data.Pump_No),String(x.Payment_Type),num_(x.Amount),
    String(x.Reference_No||''),String(x.Remarks||'')
  ]));
  return {ok:true};
}

function saveExpenditure_(p) {
  const user = loginContext_(p);
  const data = p.data || {};
  if (!data.Shift_ID) throw new Error('Shift_ID required');
  const amount = num_(data.Amount);
  if (amount < 0) throw new Error('Expenditure amount cannot be negative');
  const sh = ss_().getSheetByName(SHEETS.EXPENDITURE);
  sh.appendRow([
    'EX-'+Utilities.getUuid().slice(0,8).toUpperCase(),
    String(data.Shift_ID), normalizeDate_(data.Date),
    String(data.Staff_ID || user.Staff_ID), Number(data.Pump_No),
    String(data.Expenditure_Type || 'General'), amount,
    String(data.Remarks || ''),
    String(user.Staff_ID), String(user.Staff_Name), new Date()
  ]);
  return {ok:true,message:'Expenditure saved'};
}

function getExpenditures_(p) {
  const user = loginContext_(p);
  const rows = getObjects_(ss_().getSheetByName(SHEETS.EXPENDITURE));
  let out = rows;
  if (user.Role === 'Employee') out = rows.filter(r => String(r.Staff_ID).toUpperCase() === String(user.Staff_ID).toUpperCase());
  else if (user.Role === 'Manager') out = p.staffId ? rows.filter(r => String(r.Staff_ID).toUpperCase() === String(p.staffId).toUpperCase()) : [];
  else if (user.Role === 'Owner') { if (p.staffId) out = rows.filter(r => String(r.Staff_ID).toUpperCase() === String(p.staffId).toUpperCase()); }
  return {ok:true,rows:out.reverse()};
}

/* ═══════════════════════ LAST CLOSING ═══════════════════════ */

function getLastClosing_(p) {
  const pump = Number(p.pumpNo);
  const targetDate = normalizeDate_(p.date || new Date());
  const nozzleRows = getObjects_(ss_().getSheetByName(SHEETS.NOZZLE));

  const rows = nozzleRows.filter(r => Number(r.Pump_No)===pump).filter(r => normalizeDate_(r.Date) < targetDate);
  const latest = {};
  rows.forEach(r => {
    const key = String(r.Fuel_Type)+'_'+String(r.Nozzle_No);
    const d = normalizeDate_(r.Date);
    const prev = latest[key];
    if (!prev || d > prev.date) latest[key] = {closing:num_(r.Closing_Reading),date:d};
  });

  const futureRows = nozzleRows.filter(r => Number(r.Pump_No)===pump).filter(r => normalizeDate_(r.Date) > targetDate);
  const next = {};
  futureRows.forEach(r => {
    const key = String(r.Fuel_Type)+'_'+String(r.Nozzle_No);
    const d = normalizeDate_(r.Date);
    const prev = next[key];
    const opening = num_(r.Opening_Reading);
    if (!prev || d < prev.date) next[key] = {opening:opening,date:d};
  });

  return {ok:true, closing:latest, nextOpening:next, forDate:targetDate};
}

/* ═══════════════════════ OTP ═══════════════════════ */

function saveOTPSettlement_(p) {
  const data = p.data || {};
  if (!data.Shift_ID) throw new Error('Shift_ID required');
  const otp = num_(data.OTP_Amount);
  if (otp <= 0) return {ok:true,message:'No OTP amount'};
  const settled = num_(data.Settled_Amount);
  const pending = Math.max(0, otp-settled);
  const status = pending <= 0 ? 'Settled' : 'Pending';
  ss_().getSheetByName(SHEETS.OTP).appendRow([
    'OTP-'+Utilities.getUuid().slice(0,8).toUpperCase(), data.Shift_ID, normalizeDate_(data.Date),
    String(data.Staff_ID), Number(data.Pump_No), otp,
    data.Settlement_Date ? normalizeDate_(data.Settlement_Date) : '',
    settled, pending, status, String(data.Remarks||'')
  ]);
  return {ok:true,status:status};
}

function getOTPPending_(p) {
  requireRole_(p, ['Owner']);
  const rows = getObjects_(ss_().getSheetByName(SHEETS.OTP));
  return {ok:true,rows:rows.filter(r => String(r.Status).toLowerCase()!=='settled').map(r => ({
    id:String(r.Settlement_ID), date:normalizeDate_(r.Sales_Date), pump:r.Pump_No,
    staff:r.Staff_ID, otp:num_(r.OTP_Amount), status:String(r.Status||'Pending'),
    settled:num_(r.Settled_Amount), pending:num_(r.Pending_Amount)
  }))};
}

function settleOTP_(p) {
  requireRole_(p, ['Owner']);
  const id = String(p.id||''); const amount = num_(p.amount); const date = normalizeDate_(p.date);
  if (!id || amount < 0 || !date) throw new Error('Settlement ID, amount and date are required');
  const sh = ss_().getSheetByName(SHEETS.OTP); const rows = getObjects_(sh);
  const idx = rows.findIndex(r => String(r.Settlement_ID) === id);
  if (idx < 0) throw new Error('OTP settlement not found');
  const old = rows[idx]; const otp = num_(old.OTP_Amount);
  if (amount > otp) throw new Error('Settled amount cannot exceed OTP amount');
  const pending = Math.max(0, otp-amount); const status = pending <= 0 ? 'Settled' : 'Pending';
  sh.getRange(idx+2, 7, 1, 4).setValues([[date, amount, pending, status]]);
  return {ok:true, status, pending};
}

function getOTPSettlements_() {
  return {ok:true, rows: getObjects_(ss_().getSheetByName(SHEETS.OTP)).reverse()};
}

/* ═══════════════════════ STOCK PURCHASE ═══════════════════════ */

function saveStockPurchase_(p) {
  const u = p.currentUser || {};
  if (!['Manager','Owner'].includes(String(u.Role))) {
    return {ok:false, error:'Only Manager or Owner can enter Stock Purchase.'};
  }
  const d = p.data || {};
  const qty = num_(d.Quantity_KG);
  const rate = num_(d.Rate);
  const amount = (d.Total_Amount !== undefined && d.Total_Amount !== '') ? num_(d.Total_Amount) : qty*rate;
  if (!d.Purchase_Date || !d.Fuel_Type || qty <= 0 || rate < 0) {
    return {ok:false, error:'Purchase Date, Fuel Type, Quantity and Rate are required.'};
  }
  const sh = ss_().getSheetByName(SHEETS.STOCK_PURCHASES);
  if (!sh) return {ok:false, error:'Stock_Purchases sheet not found. Run setup.'};
  const id = 'PUR-'+Utilities.getUuid().slice(0,8).toUpperCase();
  sh.appendRow([
    id, d.Purchase_Date, d.Fuel_Type, qty, rate, amount,
    d.Supplier||'', d.Invoice_No||'', d.Payment_Type||'',
    d.Remarks||'', u.Staff_ID||'', u.Staff_Name||'', new Date()
  ]);
  return {ok:true, purchaseId:id, message:'Stock Purchase saved successfully'};
}

function getStockPurchases_(p) {
  const u = p.currentUser || {};
  if (!['Manager','Owner'].includes(String(u.Role))) {
    return {ok:false, error:'Only Manager or Owner can view Stock Purchases.'};
  }
  return {ok:true, rows:getObjects_(ss_().getSheetByName(SHEETS.STOCK_PURCHASES))};
}

/* ═══════════════════════ DASHBOARD ═══════════════════════ */

function getDashboard_(p) {
  const user = loginContext_(p);
  const shifts = getShifts_(p).shifts;
  let totalSales=0,totalCash=0,totalOnline=0,totalOTP=0;
  shifts.forEach(s => {
    totalSales += num_(s.Total_Sales); totalCash += num_(s.Cash_Total);
    totalOnline += num_(s.Online_Amount); totalOTP += num_(s.OTP_Amount);
  });
  return {ok:true, role:user.Role, summary:{
    shiftCount:shifts.length, totalSales, totalCash, totalOnline, totalOTP,
    totalCollected: totalCash+totalOnline+totalOTP
  }, shifts:shifts};
}

function getDashboardData_(p) {
  requireRole_(p, ['Owner']);
  const rows = getObjects_(ss_().getSheetByName(SHEETS.SHIFTS));
  const now = new Date();
  const tz = Session.getScriptTimeZone();
  const endDate = Utilities.formatDate(now, tz, 'yyyy-MM-dd');
  const start = new Date(now.getTime() - 29*24*60*60*1000);
  const startDate = Utilities.formatDate(start, tz, 'yyyy-MM-dd');
  const inRange = rows.filter(r => { const d = normalizeDate_(r.Date); return d >= startDate && d <= endDate; });
  const todayRows = inRange.filter(r => normalizeDate_(r.Date) === endDate);
  const sum = rs => rs.reduce((a,r) => {
    a.count++; a.Total_Sales += num_(r.Total_Sales); a.Cash_Total += num_(r.Cash_Total);
    a.Online_Amount += num_(r.Online_Amount); a.OTP_Amount += num_(r.OTP_Amount);
    a.Expenditure += num_(r.Expenditure); a.Difference += num_(r.Difference);
    a.Petrol_Litres += num_(r.Petrol_Litres); a.Diesel_Litres += num_(r.Diesel_Litres);
    a.CNG_KG += num_(r.CNG_KG); a.Petrol_Amount += num_(r.Petrol_Amount);
    a.Diesel_Amount += num_(r.Diesel_Amount); a.CNG_Amount += num_(r.CNG_Amount);
    return a;
  }, {count:0,Total_Sales:0,Cash_Total:0,Online_Amount:0,OTP_Amount:0,Expenditure:0,Difference:0,Petrol_Litres:0,Diesel_Litres:0,CNG_KG:0,Petrol_Amount:0,Diesel_Amount:0,CNG_Amount:0});
  const totals = sum(inRange), today = sum(todayRows);
  const trend = [];
  for (let i=6;i>=0;i--) {
    const dt = new Date(now.getTime()-i*86400000);
    const ds = Utilities.formatDate(dt, tz, 'yyyy-MM-dd');
    const rs = inRange.filter(r => normalizeDate_(r.Date) === ds);
    trend.push({date:ds, sales:sum(rs).Total_Sales});
  }
  const byPump = {};
  inRange.forEach(r => { const k = String(r.Pump_No); if (!byPump[k]) byPump[k] = {sales:0,count:0}; byPump[k].sales += num_(r.Total_Sales); byPump[k].count++; });
  const staffMap = {};
  inRange.forEach(r => {
    const k = String(r.Staff_ID);
    if (!staffMap[k]) staffMap[k] = {name:String(r.Staff_Name||k),sales:0,diff:0,count:0};
    staffMap[k].sales += num_(r.Total_Sales); staffMap[k].diff += num_(r.Difference); staffMap[k].count++;
  });
  const byStaff = Object.values(staffMap).sort((a,b) => b.sales-a.sales);
  const recentDiffs = inRange.filter(r => Math.abs(num_(r.Difference)) > 0.009)
    .sort((a,b) => String(b.Date).localeCompare(String(a.Date))).slice(0,10)
    .map(r => ({date:normalizeDate_(r.Date), pump:r.Pump_No, diff:num_(r.Difference)}));
  return {ok:true, data:{totals, today, trend, byPump, byStaff, recentDiffs}};
}

/* ═══════════════════════ SALARY ═══════════════════════ */

function getSalaryReport_(p) {
  requireRole_(p, ['Owner']);
  const month = String(p.month||'').trim();
  if (!/^\d{4}-\d{2}$/.test(month)) throw new Error('Month is required');
  const range = parseMonthRange_(month);
  const staffRows = getObjects_(ss_().getSheetByName(SHEETS.STAFF));
  const shifts = getObjects_(ss_().getSheetByName(SHEETS.SHIFTS))
    .filter(r => { const d = normalizeDate_(r.Date); return d >= range.start && d <= range.end; });

  const byStaff = {};
  shifts.forEach(r => {
    const id = String(r.Staff_ID||'').trim().toUpperCase();
    if (!id) return;
    if (!byStaff[id]) byStaff[id] = {days:new Set(), shortage:0, surplus:0};
    byStaff[id].days.add(normalizeDate_(r.Date));
    const diff = num_(r.Difference);
    if (diff < 0) byStaff[id].shortage += Math.abs(diff);
    if (diff > 0) byStaff[id].surplus += diff;
  });

  const dedRows = getObjects_(ss_().getSheetByName(SHEETS.SALARY_DEDUCTIONS));
  const approved = {};
  dedRows.filter(r => String(r.Month)===month && String(r.Status||'').toLowerCase()==='approved')
    .forEach(r => {
      const id = String(r.Staff_ID||'').trim().toUpperCase();
      approved[id] = (approved[id]||0) + num_(r.Approved_Deduction);
    });

  const rows = staffRows.map(r => {
    const id = String(r.Staff_ID||'').trim();
    const x = byStaff[id.toUpperCase()] || {days:new Set(), shortage:0, surplus:0};
    const type = String(r.Salary_Type||'Daily Fixed');
    const rate = num_(r.Salary_Rate);
    const days = x.days.size;
    const gross = type === 'Monthly Fixed' ? rate : days*rate;
    const shortage = Math.round(x.shortage*100)/100;
    const approvedDed = Math.min(shortage, Math.round((approved[id.toUpperCase()]||0)*100)/100);
    const pending = Math.max(0, shortage-approvedDed);
    const net = Math.max(0, gross-approvedDed);
    return {
      staffId:id, name:String(r.Staff_Name||''), accessRole:String(r.Role||''),
      jobRole:String(r.Job_Role||''), salaryType:type, rate,
      daysWorked:days, grossSalary:gross, shortage, approvedDeduction:approvedDed,
      pendingDeduction:pending, netSalary:net,
      surplus:Math.round(x.surplus*100)/100, status:String(r.Status||'')
    };
  });

  const active = rows.filter(r => r.status.toLowerCase()==='active');
  const totals = active.reduce((a,r) => {
    a.gross += r.grossSalary; a.shortage += r.shortage;
    a.approved += r.approvedDeduction; a.pending += r.pendingDeduction; a.net += r.netSalary;
    return a;
  }, {gross:0, shortage:0, approved:0, pending:0, net:0});

  return {ok:true, data:{
    month, start:range.start, end:range.end, rows,
    totalSalary:totals.net, totalGross:totals.gross,
    totalShortage:totals.shortage, totalApprovedDeduction:totals.approved,
    totalPendingDeduction:totals.pending, activeStaff:active.length
  }};
}

function approveSalaryDeduction_(p) {
  requireRole_(p, ['Owner']);
  const month = String(p.month||'').trim();
  const staffId = String(p.staffId||'').trim().toUpperCase();
  const amount = num_(p.amount);
  const reason = String(p.reason||'').trim();
  if (!/^\d{4}-\d{2}$/.test(month)) throw new Error('Month is required');
  if (!staffId) throw new Error('Staff ID is required');
  if (amount <= 0) throw new Error('Deduction amount must be greater than zero');
  if (!reason) throw new Error('Reason is required');
  const staff = findStaff_(staffId); if (!staff) throw new Error('Staff not found');
  const report = getSalaryReport_({currentUser:p.currentUser, month});
  const row = report.data.rows.find(x => x.staffId.toUpperCase() === staffId);
  if (!row) throw new Error('Staff not found');
  if (amount > row.pendingDeduction + 0.001)
    throw new Error('Deduction cannot exceed pending shortage ₹'+row.pendingDeduction);
  const sh = ss_().getSheetByName(SHEETS.SALARY_DEDUCTIONS);
  const id = 'SD-'+Utilities.getUuid().slice(0,8).toUpperCase();
  const u = p.currentUser||{};
  sh.appendRow([id, month, staffId, staff.Staff_Name, row.shortage, amount, reason, u.Staff_ID||'', u.Staff_Name||'', new Date(), 'Approved']);
  return {ok:true, message:'Salary deduction approved', deductionId:id};
}

/* ═══════════════════════ REPORTS ═══════════════════════ */

function getReportData_(p) {
  requireRole_(p, ['Owner']);
  const from = normalizeDate_(p.from), to = normalizeDate_(p.to), type = String(p.type||'daily');
  if (!from || !to) throw new Error('From and To dates are required');
  let shifts = getObjects_(ss_().getSheetByName(SHEETS.SHIFTS))
    .filter(r => { const d = normalizeDate_(r.Date); return d >= from && d <= to; });
  if (p.pump) shifts = shifts.filter(r => String(r.Pump_No) === String(p.pump));
  if (p.staff) shifts = shifts.filter(r => String(r.Staff_ID) === String(p.staff));
  if (p.shift) shifts = shifts.filter(r => String(r.Shift) === String(p.shift));

  const summary = shifts.reduce((a,r) => {
    a.Total_Sales += num_(r.Total_Sales);
    a.Total_Collected += num_(r.Total_Collected);
    a.Expenditure += num_(r.Expenditure);
    a.Difference += num_(r.Difference);
    return a;
  }, {Total_Sales:0,Total_Collected:0,Expenditure:0,Difference:0});

  let rows = [];
  const sumGroup = (keyFn) => {
    const m = {};
    shifts.forEach(r => { const k = keyFn(r); if (!m[k]) m[k] = []; m[k].push(r); });
    return Object.keys(m).sort().map(k => {
      const rs = m[k];
      const z = {count:rs.length, petrolL:0, dieselL:0, cngL:0, sales:0, cash:0, online:0, otp:0, diff:0};
      rs.forEach(r => {
        z.petrolL += num_(r.Petrol_Litres); z.dieselL += num_(r.Diesel_Litres);
        z.cngL += num_(r.CNG_KG); z.sales += num_(r.Total_Sales);
        z.cash += num_(r.Cash_Total); z.online += num_(r.Online_Amount);
        z.otp += num_(r.OTP_Amount); z.diff += num_(r.Difference);
      });
      return Object.assign({key:k}, z);
    });
  };

  if (type === 'daily') rows = sumGroup(r => normalizeDate_(r.Date)).map(x => ({date:x.key,count:x.count,petrolL:x.petrolL,dieselL:x.dieselL,cngL:x.cngL,sales:x.sales,cash:x.cash,online:x.online,otp:x.otp,diff:x.diff}));
  else if (type === 'pump') rows = sumGroup(r => String(r.Pump_No)).map(x => ({pump:x.key,count:x.count,petrolL:x.petrolL,dieselL:x.dieselL,cngL:x.cngL,sales:x.sales,diff:x.diff}));
  else if (type === 'employee') rows = sumGroup(r => String(r.Staff_ID)).map(x => ({name:(shifts.find(r => String(r.Staff_ID)===x.key)||{}).Staff_Name||x.key,count:x.count,sales:x.sales,cash:x.cash,diff:x.diff}));
  else if (type === 'shift') rows = sumGroup(r => String(r.Shift||'')).map(x => ({shift:x.key,count:x.count,sales:x.sales,cash:x.cash,diff:x.diff}));
  else if (type === 'difference') rows = shifts.map(r => ({date:normalizeDate_(r.Date),shift:r.Shift||'',pump:r.Pump_No,staff:r.Staff_Name||r.Staff_ID,sales:num_(r.Total_Sales),collected:num_(r.Total_Collected),exp:num_(r.Expenditure),diff:num_(r.Difference)}));
  else if (type === 'expenditure') {
    const ex = getObjects_(ss_().getSheetByName(SHEETS.EXPENDITURE)).filter(r => {
      const d = normalizeDate_(r.Date);
      return d >= from && d <= to && (!p.pump || String(r.Pump_No)===String(p.pump)) && (!p.staff || String(r.Staff_ID)===String(p.staff));
    });
    const shiftMap = {}; shifts.forEach(r => shiftMap[String(r.Shift_ID)] = r.Shift||'');
    rows = ex.map(r => ({date:normalizeDate_(r.Date),shift:shiftMap[String(r.Shift_ID)]||'',pump:r.Pump_No,staff:r.Staff_ID,type:r.Expenditure_Type||'',amount:num_(r.Amount),remarks:r.Remarks||''}));
  }
  else if (type === 'otp') {
    const otp = getObjects_(ss_().getSheetByName(SHEETS.OTP)).filter(r => { const d = normalizeDate_(r.Sales_Date); return d >= from && d <= to; });
    const shiftMap = {}; shifts.forEach(r => shiftMap[String(r.Shift_ID)] = r.Shift||'');
    rows = otp.map(r => ({date:normalizeDate_(r.Sales_Date),shift:shiftMap[String(r.Shift_ID)]||'',pump:r.Pump_No,staff:r.Staff_ID,otp:num_(r.OTP_Amount),status:r.Status||'Pending',settled:num_(r.Settled_Amount),pending:num_(r.Pending_Amount)}));
  }
  else if (type === 'nozzle') {
    const nr = getObjects_(ss_().getSheetByName(SHEETS.NOZZLE)).filter(r => {
      const d = normalizeDate_(r.Date);
      return d >= from && d <= to && (!p.pump || String(r.Pump_No)===String(p.pump)) && (!p.staff || String(r.Staff_ID)===String(p.staff));
    });
    const shiftMap = {}; shifts.forEach(r => shiftMap[String(r.Shift_ID)] = r.Shift||'');
    rows = nr.map(r => ({date:normalizeDate_(r.Date),shift:shiftMap[String(r.Shift_ID)]||'',pump:r.Pump_No,fuel:r.Fuel_Type,nozzle:r.Nozzle_No,open:num_(r.Opening_Reading),close:num_(r.Closing_Reading),litres:num_(r.Litres),rate:num_(r.Rate),amount:num_(r.Amount)}));
  }
  else if (type === 'stock') {
    const sp = getObjects_(ss_().getSheetByName(SHEETS.STOCK_PURCHASES)).filter(r => { const d = normalizeDate_(r.Purchase_Date); return d >= from && d <= to; });
    rows = sp.map(r => ({date:normalizeDate_(r.Purchase_Date),fuel:r.Fuel_Type,qty:num_(r.Quantity_KG),rate:num_(r.Rate),amount:num_(r.Total_Amount),supplier:r.Supplier||'',invoice:r.Invoice_No||'',payment:r.Payment_Type||''}));
  }

  return {ok:true, rows, summary};
}

/* ═══════════════════════ DSR — REGISTER (paper format) ═══════════════════════ */

function dsrUnit_(fuel) { return String(fuel)==='CNG' ? 'KG' : 'L'; }
function dsrSalesField_(fuel) { return String(fuel)==='Petrol' ? 'Petrol_Litres' : String(fuel)==='Diesel' ? 'Diesel_Litres' : 'CNG_KG'; }
function dsrDipKey_(fuel) { return 'DSR_Daily_Dip_'+String(fuel); }

function saveSettingAction_(p) {
  requireRole_(p, ['Owner']);
  const key = String(p.key||'').trim();
  if (!key) throw new Error('Setting key required');
  saveSettingValue_(key, p.value);
  return {ok:true};
}

function saveDSROpening_(p) {
  const u = requireRole_(p, ['Owner']);
  const date = normalizeDate_(p.date), fuel = String(p.fuel||''), opening = num_(p.opening);
  if (!date || !['Petrol','Diesel','CNG'].includes(fuel) || opening < 0)
    throw new Error('Date, Fuel and Opening Stock are required');
  let sh = ss_().getSheetByName(SHEETS.DSR_OPENING);
  if (!sh) { setupSheets_(); sh = ss_().getSheetByName(SHEETS.DSR_OPENING); }
  const rows = getObjects_(sh);
  const idx = rows.findIndex(r => normalizeDate_(r.Date) === date && String(r.Fuel_Type) === fuel);
  const row = [date, fuel, opening, String(p.remarks||''), u.Staff_ID||'', u.Staff_Name||'', new Date()];
  if (idx >= 0) sh.getRange(idx+2, 1, 1, row.length).setValues([row]);
  else sh.appendRow(row);
  return {ok:true};
}

function saveDSRDip_(p) {
  requireRole_(p, ['Owner']);
  const fuel = String(p.fuel||''), dip = num_(p.dip);
  if (!['Petrol','Diesel','CNG'].includes(fuel) || dip < 0) throw new Error('Invalid fuel/dip');
  saveSettingValue_(dsrDipKey_(fuel), dip);
  return {ok:true};
}

function saveDSRDipReading_(p) {
  const u = requireRole_(p, ['Owner']);
  const date = normalizeDate_(p.date);
  const fuel = String(p.fuel||'');
  const closingDip = num_(p.closingDip);
  const remarks = String(p.remarks||'');
  if (!date) throw new Error('Date required');
  if (!['Petrol','Diesel','CNG'].includes(fuel)) throw new Error('Invalid fuel');
  if (closingDip < 0) throw new Error('Closing Dip must be 0 or positive');

  let sh = ss_().getSheetByName(SHEETS.DSR_DIP);
  if (!sh) { setupSheets_(); sh = ss_().getSheetByName(SHEETS.DSR_DIP); }
  const rows = getObjects_(sh);
  const idx = rows.findIndex(r => normalizeDate_(r.Date) === date && String(r.Fuel_Type) === fuel);
  const row = [date, fuel, closingDip, remarks, u.Staff_ID||'', u.Staff_Name||'', new Date()];
  if (idx >= 0) sh.getRange(idx+2, 1, 1, row.length).setValues([row]);
  else sh.appendRow(row);
  return {ok:true, message:'Daily dip saved'};
}

function getDSRRegister_(p) {
  requireRole_(p, ['Owner']);
  const fuel = String(p.fuel||'Petrol');
  if (!['Petrol','Diesel','CNG'].includes(fuel)) throw new Error('Invalid fuel');
  const range = parseMonthRange_(p.month);
  const unit = dsrUnit_(fuel);
  const salesField = dsrSalesField_(fuel);

  const defaultPumpTest = getSettingValue_(dsrDipKey_(fuel), fuel==='CNG' ? 0 : 20);
  const tankCapacity = getSettingValue_('DSR_Tank_Capacity_' + fuel, 0);

  const shifts = getObjects_(ss_().getSheetByName(SHEETS.SHIFTS));
  const purchases = getObjects_(ss_().getSheetByName(SHEETS.STOCK_PURCHASES));
  const openingRows = getObjects_(ss_().getSheetByName(SHEETS.DSR_OPENING));
  const dipSheet = ss_().getSheetByName(SHEETS.DSR_DIP);
  const dipRows = dipSheet ? getObjects_(dipSheet) : [];

  const salesByDate = {};
  shifts.forEach(r => {
    const d = normalizeDate_(r.Date);
    if (d && d >= range.start && d <= range.end)
      salesByDate[d] = (salesByDate[d]||0) + num_(r[salesField]);
  });

  const receiptByDate = {};
  purchases.forEach(r => {
    const d = normalizeDate_(r.Purchase_Date);
    if (d && d >= range.start && d <= range.end && String(r.Fuel_Type) === fuel)
      receiptByDate[d] = (receiptByDate[d]||0) + num_(r.Quantity_KG);
  });

  const manualOpening = {};
  openingRows.forEach(r => {
    if (String(r.Fuel_Type) === fuel) {
      const d = normalizeDate_(r.Date);
      if (d) manualOpening[d] = num_(r.Opening_Stock);
    }
  });

  const dipByDate = {};
  dipRows.forEach(r => {
    if (String(r.Fuel_Type) === fuel) {
      const d = normalizeDate_(r.Date);
      if (d) dipByDate[d] = num_(r.Closing_Dip);
    }
  });

  let openingForMonth = manualOpening.hasOwnProperty(range.start) ? manualOpening[range.start] : null;
  if (openingForMonth === null) {
    const prior = Object.keys(dipByDate).filter(d => d < range.start).sort().pop();
    if (prior) openingForMonth = dipByDate[prior];
  }

  const rows = [];
  let prevClosing = openingForMonth;
  let cumSales = 0, cumVar = 0;

  for (let d = range.start; d <= range.end; d = addDays_(d,1)) {
    let opening = prevClosing;
    if (manualOpening.hasOwnProperty(d)) opening = manualOpening[d];

    const receipt = receiptByDate[d] || 0;
    const openingVal = (opening === null ? 0 : opening);
    const totalStock = openingVal + receipt;
    const salesMeter = salesByDate[d] || 0;
    const pumpTest = defaultPumpTest;
    const netSales = salesMeter - pumpTest;
    cumSales += netSales;

    const hasDip = dipByDate.hasOwnProperty(d);
    const closingDip = hasDip ? dipByDate[d] : null;
    const salesDip = (hasDip && opening !== null) ? (openingVal + receipt - closingDip) : null;
    const varDaily = (salesDip !== null) ? (netSales - salesDip) : null;
    if (varDaily !== null) cumVar += varDaily;

    rows.push({
      date:d, opening:opening, receipt:receipt, totalStock:totalStock,
      salesByMeter:salesMeter, pumpTest:pumpTest, netSales:netSales,
      cumulativeSales:cumSales, salesByDip:salesDip, closingDip:closingDip,
      variationDaily:varDaily,
      variationCumulative:(varDaily !== null) ? cumVar : null,
      remarks:''
    });

    if (hasDip) prevClosing = closingDip;
    else if (opening !== null) prevClosing = openingVal + receipt - netSales;
    else prevClosing = null;
  }

  const summary = {
    opening: openingForMonth,
    receipt: rows.reduce((a,r) => a + r.receipt, 0),
    salesMeter: rows.reduce((a,r) => a + r.salesByMeter, 0),
    pumpTest: rows.reduce((a,r) => a + r.pumpTest, 0),
    netSales: rows.reduce((a,r) => a + r.netSales, 0),
    salesDip: rows.filter(r => r.salesByDip !== null).reduce((a,r) => a + r.salesByDip, 0),
    variation: cumVar,
    closing: rows.length
      ? (rows[rows.length-1].closingDip !== null
          ? rows[rows.length-1].closingDip
          : (rows[rows.length-1].opening + rows[rows.length-1].receipt - rows[rows.length-1].netSales))
      : null
  };

  return {ok:true, data:{
    fuel, unit,
    monthStart: range.start, monthEnd: range.end,
    tankCapacity, defaultPumpTest,
    openingForMonth, rows, summary
  }};
}

// Legacy DSR (kept for backward compatibility)
function getDSRData_(p) {
  requireRole_(p, ['Owner']);
  return getDSRRegister_(p);
}