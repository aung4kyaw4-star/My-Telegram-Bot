import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # ငွေစာရင်း Table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        type TEXT,
        amount REAL,
        description TEXT,
        person TEXT,
        category TEXT
    )''')
    
    # အစီအစဉ် Table
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        title TEXT,
        description TEXT,
        reminder_hours INTEGER DEFAULT 2
    )''')
    
    # သတိပေးချက် Table
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        reminder_time TEXT,
        message TEXT,
        is_sent INTEGER DEFAULT 0
    )''')
    
    conn.commit()
    conn.close()

def add_transaction(transaction_type, amount, description="", person="", category=""):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M")
    c.execute("""INSERT INTO transactions 
                 (date, time, type, amount, description, person, category) 
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (date, time, transaction_type, amount, description, person, category))
    conn.commit()
    conn.close()
    return f"✅ {transaction_type} ငွေ {amount} ကျပ်ကို အောင်မြင်စွာ မှတ်သားပြီးပါပြီ။"

def add_schedule_with_reminder(date, time, title, description="", reminder_hours=2):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    c.execute("INSERT INTO schedules (date, time, title, description, reminder_hours) VALUES (?, ?, ?, ?, ?)",
              (date, time, title, description, reminder_hours))
    schedule_id = c.lastrowid
    
    from datetime import datetime, timedelta
    event_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    reminder_datetime = event_datetime - timedelta(hours=reminder_hours)
    reminder_time = reminder_datetime.strftime("%Y-%m-%d %H:%M")
    
    c.execute("INSERT INTO reminders (schedule_id, reminder_time, message) VALUES (?, ?, ?)",
              (schedule_id, reminder_time, f"⏰ သတိပေးချက်: {title} ကို {date} {time} တွင် ကျင်းပမည်"))
    
    conn.commit()
    conn.close()
    return f"✅ အစီအစဉ် '{title}' ကို {date} {time} တွင် မှတ်သားပြီး အချိန်မှန်သတိပေးပါမည်။"

def get_due_reminders():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("SELECT id, message FROM reminders WHERE reminder_time <= ? AND is_sent = 0", (now,))
    reminders = c.fetchall()
    conn.close()
    return reminders

def mark_reminder_sent(reminder_id):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def get_daily_report():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    c.execute("SELECT type, SUM(amount) FROM transactions WHERE date = ? GROUP BY type", (today,))
    today_trans = c.fetchall()
    
    c.execute("SELECT time, title, description FROM schedules WHERE date = ? ORDER BY time", (today,))
    today_sched = c.fetchall()
    
    conn.close()
    
    report = f"📊 **{today} နေ့စဉ် အစီရင်ခံစာ**\n\n"
    report += "💰 **ငွေစာရင်း အကျဉ်းချုပ်**\n"
    
    total_in = 0
    total_out = 0
    for t in today_trans:
        if t[0] in ["ယူငွေ", "ပြန်ဆပ်ငွေ"]:
            total_in += t[1]
        else:
            total_out += t[1]
    
    report += f"ဝင်ငွေ: {total_in} ကျပ်\n"
    report += f"ထွက်ငွေ: {total_out} ကျပ်\n"
    report += f"လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
    
    report += "📅 **ဒီနေ့ အစီအစဉ်များ**\n"
    if today_sched:
        for s in today_sched:
            report += f"⏰ {s[0]} - {s[1]}\n"
    else:
        report += "ဒီနေ့အတွက် သတ်မှတ်ထားတဲ့ အစီအစဉ်မရှိပါ။\n"
    
    return report

def get_all_debts():
    """အကြွေးစာရင်းအကုန်ယူမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("SELECT person, SUM(amount) FROM transactions WHERE type = 'ချေးငွေ' GROUP BY person")
    debts = c.fetchall()
    conn.close()
    
    if not debts:
        return "📋 **အကြွေးစာရင်း**\n\nအကြွေးမရှိပါ။"
    
    report = "📋 **အကြွေးစာရင်း**\n\n"
    for person, amount in debts:
        report += f"👤 {person}: {amount} ကျပ်\n"
    return report

def get_debt_for_person(person):
    """လူတစ်ယောက်ရဲ့ အကြွေးကိုယူမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("SELECT SUM(amount) FROM transactions WHERE type = 'ချေးငွေ' AND person = ?", (person,))
    result = c.fetchone()[0]
    conn.close()
    return result if result else 0

def repay_debt(person, amount):
    """အကြွေးပြန်ဆပ်မယ်"""
    current_debt = get_debt_for_person(person)
    if current_debt == 0:
        return f"⚠️ {person} ဆီက အကြွေးမရှိပါ။"
    
    if amount > current_debt:
        return f"⚠️ {person} ဆီက အကြွေးက {current_debt} ကျပ်ပဲရှိပါတယ်။ {amount} ကျပ်ထပ်မဆပ်နိုင်ပါ။"
    
    # ပြန်ဆပ်ငွေအဖြစ် မှတ်မယ်
    add_transaction("ပြန်ဆပ်ငွေ", amount, f"{person} ကို ပြန်ဆပ်", person)
    
    remaining = current_debt - amount
    if remaining == 0:
        return f"✅ {person} ဆီက အကြွေး {amount} ကျပ် အကုန်ပြန်ဆပ်ပြီးပါပြီ။"
    else:
        return f"✅ {person} ဆီက အကြွေး {amount} ကျပ် ပြန်ဆပ်ပြီးပါပြီ။ ကျန်အကြွေး: {remaining} ကျပ်"
