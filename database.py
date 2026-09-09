import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # ငွေစာရင်း Table
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        amount REAL,
        description TEXT,
        category TEXT
    )''')
    
    # လုပ်ငန်းအချက်အလက် / အစီအစဉ် Table
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        title TEXT,
        description TEXT,
        reminder_days INTEGER DEFAULT 1
    )''')
    
    # သတိပေးချက် Table (အသစ်)
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        reminder_time TEXT,
        message TEXT,
        is_sent INTEGER DEFAULT 0,
        FOREIGN KEY(schedule_id) REFERENCES schedules(id)
    )''')
    
    conn.commit()
    conn.close()

def add_transaction(transaction_type, amount, description, category=""):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO transactions (date, type, amount, description, category) VALUES (?, ?, ?, ?, ?)",
              (date, transaction_type, amount, description, category))
    conn.commit()
    conn.close()
    return f"✅ {transaction_type} ငွေ {amount} ကျပ်ကို အောင်မြင်စွာ မှတ်သားပြီးပါပြီ။"

def add_schedule_with_reminder(date, time, title, description="", reminder_hours=2):
    """အစီအစဉ်နဲ့ သတိပေးချက်ကို အတူတူထည့်မယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # အစီအစဉ်ထည့်မယ်
    c.execute("INSERT INTO schedules (date, time, title, description) VALUES (?, ?, ?, ?)",
              (date, time, title, description))
    schedule_id = c.lastrowid
    
    # သတိပေးချက်အချိန်တွက်မယ်
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
    """ပို့ရန်ကျန်နေသေးတဲ့ သတိပေးချက်တွေကိုယူမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    c.execute("SELECT id, message FROM reminders WHERE reminder_time <= ? AND is_sent = 0", (now,))
    reminders = c.fetchall()
    conn.close()
    return reminders

def mark_reminder_sent(reminder_id):
    """သတိပေးချက်ပို့ပြီးရင် အမှတ်အသားပြုမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def get_daily_report():
    """နေ့စဉ်အစီရင်ခံစာ"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # ဒီနေ့ငွေစာရင်း
    c.execute("SELECT type, SUM(amount) FROM transactions WHERE date LIKE ? GROUP BY type", (today + '%',))
    today_trans = c.fetchall()
    
    # ဒီနေ့အစီအစဉ်
    c.execute("SELECT time, title, description FROM schedules WHERE date = ? ORDER BY time", (today,))
    today_sched = c.fetchall()
    
    conn.close()
    
    report = f"📊 **{today} နေ့စဉ် အစီရင်ခံစာ**\n\n"
    report += "💰 **ငွေစာရင်း အကျဉ်းချုပ်**\n"
    total_in = 0
    total_out = 0
    for t in today_trans:
        if t[0] == "ယူငွေ" or t[0] == "ပြန်ဆပ်ငွေ":
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
