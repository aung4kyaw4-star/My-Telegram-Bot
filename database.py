import sqlite3
import datetime
import os
import json

def init_db():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        type TEXT,
        amount REAL,
        description TEXT,
        person TEXT,
        category TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        category TEXT,
        title TEXT,
        description TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        title TEXT,
        description TEXT,
        reminder_hours INTEGER DEFAULT 2,
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        reminder_time TEXT,
        message TEXT,
        is_sent INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS backup_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_date TEXT,
        backup_time TEXT,
        record_count INTEGER,
        status TEXT
    )''')
    
    conn.commit()
    conn.close()
    backup_database()

def backup_database():
    try:
        if not os.path.exists('backups'):
            os.makedirs('backups')
        now = datetime.datetime.now()
        backup_name = f"backups/finance_backup_{now.strftime('%Y-%m-%d')}.db"
        import shutil
        if os.path.exists('finance.db'):
            shutil.copy2('finance.db', backup_name)
            print(f"✅ Backup saved: {backup_name}")
    except Exception as e:
        print(f"❌ Backup error: {e}")

def format_response(message):
    return f"{message}"

def add_transaction(transaction_type, amount, description="", person="", category=""):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("""INSERT INTO transactions 
                 (date, time, type, amount, description, person, category, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (date, time, transaction_type, amount, description, person, category, created_at))
    conn.commit()
    conn.close()
    return format_response(f"✅ ဆရာရဲ့ {transaction_type} {amount} ကျပ်ကို အကျွန်မှတ်ထားလိုက်ပါပြီဆရာ။")

def add_note(category, title, description=""):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("""INSERT INTO notes 
                 (date, time, category, title, description, created_at) 
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (date, time, category, title, description, created_at))
    conn.commit()
    conn.close()
    
    category_names = {
        'work': 'အလုပ်ကိစ္စ',
        'personal': 'ကိုယ်ရေးကိုယ်တာကိစ္စ',
        'other': 'အခြားကိစ္စ'
    }
    cat_name = category_names.get(category, category)
    return format_response(f"✅ ဆရာရဲ့ {cat_name} '{title}' ကို အကျွန်မှတ်ထားလိုက်ပါပြီဆရာ။")

def add_schedule_with_reminder(date, time, title, description="", reminder_hours=2):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO schedules (date, time, title, description, reminder_hours, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (date, time, title, description, reminder_hours, now))
    schedule_id = c.lastrowid
    
    from datetime import datetime, timedelta
    event_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    reminder_datetime = event_datetime - timedelta(hours=reminder_hours)
    reminder_time = reminder_datetime.strftime("%Y-%m-%d %H:%M")
    
    c.execute("INSERT INTO reminders (schedule_id, reminder_time, message) VALUES (?, ?, ?)",
              (schedule_id, reminder_time, f"⏰ သတိပေးချက်: {title} ကို {date} {time} တွင် ကျင်းပမည်"))
    conn.commit()
    conn.close()
    return format_response(f"✅ ဆရာရဲ့ အစီအစဉ် '{title}' ကို {date} {time} တွင် အကျွန်မှတ်သားပြီး အချိန်မှန်သတိပေးပါမည်ဆရာ။")

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

def get_full_daily_report():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    c.execute("""SELECT type, SUM(amount) FROM transactions WHERE date = ? AND status = 'active' GROUP BY type""", (today,))
    summary = c.fetchall()
    
    c.execute("""SELECT date, time, type, amount, description, person, category FROM transactions WHERE date = ? AND status = 'active' ORDER BY time DESC""", (today,))
    transactions = c.fetchall()
    
    c.execute("""SELECT category, title, description, time FROM notes WHERE date = ? AND status = 'active' ORDER BY time DESC""", (today,))
    notes = c.fetchall()
    conn.close()
    
    report = f"📊 **{today} နေ့စဉ် အပြည့်အစုံ အစီရင်ခံစာ**\n📅 စာရင်းကောက်ချိန်: {now}\n\n"
    
    report += "💰 **ငွေစာရင်း**\n"
    total_in = 0
    total_out = 0
    summary_dict = {}
    for s in summary:
        summary_dict[s[0]] = s[1]
        if s[0] in ["ယူငွေ", "ပြန်ဆပ်ငွေ"]:
            total_in += s[1]
        else:
            total_out += s[1]
    
    type_order = ["ယူငွေ", "သုံးငွေ", "ချေးငွေ", "ပြန်ဆပ်ငွေ"]
    for t in type_order:
        if t in summary_dict:
            report += f"  {t}: {summary_dict[t]} ကျပ်\n"
    report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n  📉 ထွက်ငွေ: {total_out} ကျပ်\n  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
    
    if transactions:
        report += "📋 **ငွေစာရင်းအသေးစိတ်**\n"
        for t in transactions:
            date, time_val, trans_type, amount, desc, person, category = t
            report += f"  • {time_val} - {trans_type} {amount} ကျပ်"
            if desc:
                report += f" ({desc})"
            if person:
                report += f" - {person}"
            report += "\n"
    else:
        report += "  ဒီနေ့ငွေစာရင်းမရှိပါ။\n"
    
    if notes:
        report += "\n📝 **မှတ်စုများ**\n"
        category_names = {'work': '💼 အလုပ်ကိစ္စ', 'personal': '👤 ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': '📌 အခြားကိစ္စ'}
        for category, title, description, time_val in notes:
            cat_name = category_names.get(category, category)
            report += f"\n  {cat_name}\n  ⏰ {time_val}\n  📌 {title}\n"
            if description:
                report += f"  📝 {description}\n"
    else:
        report += "\n📝 ဒီနေ့မှတ်စုမရှိပါ။\n"
    
    return format_response(report)

def get_detailed_report(days=0, months=0):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    from datetime import datetime, timedelta
    now = datetime.now()
    today = now.date()
    
    if months > 0:
        start_date = today - timedelta(days=30*months)
        start_str = start_date.strftime("%Y-%m-%d")
        title = f"လွန်ခဲ့တဲ့ {months} လ"
    elif days > 0:
        start_date = today - timedelta(days=days)
        start_str = start_date.strftime("%Y-%m-%d")
        title = f"လွန်ခဲ့တဲ့ {days} ရက်"
    else:
        start_str = today.strftime("%Y-%m-%d")
        title = "ဒီနေ့"
    
    c.execute("""SELECT date, time, type, amount, description, person, category FROM transactions WHERE date >= ? AND status = 'active' ORDER BY date DESC, time DESC""", (start_str,))
    transactions = c.fetchall()
    
    c.execute("""SELECT type, SUM(amount) FROM transactions WHERE date >= ? AND status = 'active' GROUP BY type""", (start_str,))
    summary = c.fetchall()
    
    c.execute("""SELECT date, time, category, title, description FROM notes WHERE date >= ? AND status = 'active' ORDER BY date DESC, time DESC""", (start_str,))
    notes = c.fetchall()
    conn.close()
    
    report = f"📊 **{title} အသေးစိတ် အစီရင်ခံစာ**\n📅 စာရင်းကောက်ချိန်: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    report += "💰 **ငွေစာရင်း အကျဉ်းချုပ်**\n"
    total_in = 0
    total_out = 0
    summary_dict = {}
    for s in summary:
        summary_dict[s[0]] = s[1]
        if s[0] in ["ယူငွေ", "ပြန်ဆပ်ငွေ"]:
            total_in += s[1]
        else:
            total_out += s[1]
    
    type_order = ["ယူငွေ", "သုံးငွေ", "ချေးငွေ", "ပြန်ဆပ်ငွေ"]
    for t in type_order:
        if t in summary_dict:
            report += f"  {t}: {summary_dict[t]} ကျပ်\n"
    report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n  📉 ထွက်ငွေ: {total_out} ကျပ်\n  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
    
    if transactions:
        report += "📋 **ငွေစာရင်းအသေးစိတ်**\n"
        for t in transactions:
            date, time_val, trans_type, amount, desc, person, category = t
            report += f"\n  📅 {date} ({time_val})\n  📌 {trans_type} {amount} ကျပ်"
            if desc:
                report += f"\n  📝 {desc}"
            if person:
                report += f"\n  👤 {person}"
            report += "\n"
    else:
        report += "  ငွေစာရင်းမရှိပါ။\n"
    
    if notes:
        report += "\n📝 **မှတ်စုများ**\n"
        category_names = {'work': '💼 အလုပ်ကိစ္စ', 'personal': '👤 ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': '📌 အခြားကိစ္စ'}
        for date, time_val, category, title, description in notes:
            cat_name = category_names.get(category, category)
            report += f"\n  {cat_name}\n  📅 {date} ({time_val})\n  📌 {title}\n"
            if description:
                report += f"  📝 {description}\n"
    
    return format_response(report)

def get_category_report(category):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    category_names = {'work': 'အလုပ်ကိစ္စ', 'personal': 'ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': 'အခြားကိစ္စ'}
    cat_name = category_names.get(category, category)
    
    c.execute("""SELECT date, time, title, description FROM notes WHERE category = ? AND status = 'active' ORDER BY date DESC, time DESC""", (category,))
    notes = c.fetchall()
    conn.close()
    
    if not notes:
        return format_response(f"📋 {cat_name} စာရင်းမရှိပါဆရာ။")
    
    report = f"📋 **{cat_name} စာရင်း**\n\n"
    for date, time_val, title, description in notes:
        report += f"📅 {date} ({time_val})\n📌 {title}\n"
        if description:
            report += f"📝 {description}\n"
        report += "\n"
    return format_response(report)

def get_debt_details():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("""SELECT person, SUM(amount), COUNT(*) FROM transactions WHERE type = 'ချေးငွေ' AND status = 'active' GROUP BY person""")
    debts = c.fetchall()
    c.execute("""SELECT person, SUM(amount), COUNT(*) FROM transactions WHERE type = 'ပြန်ဆပ်ငွေ' AND status = 'active' GROUP BY person""")
    repayments = c.fetchall()
    conn.close()
    
    if not debts:
        return format_response("📋 အကြွေးမရှိပါဆရာ။")
    
    report = "📋 **အကြွေး အသေးစိတ်စာရင်း**\n\n"
    repay_dict = {}
    for person, amount, count in repayments:
        repay_dict[person] = {"amount": amount, "count": count}
    
    for person, total_debt, count in debts:
        repaid = repay_dict.get(person, {"amount": 0, "count": 0})
        remaining = total_debt - repaid["amount"]
        report += f"👤 **{person}**\n   ချေးငွေ: {total_debt} ကျပ် ({count} ကြိမ်)\n"
        if repaid["amount"] > 0:
            report += f"   ပြန်ဆပ်: {repaid['amount']} ကျပ် ({repaid['count']} ကြိမ်)\n"
        report += f"   ကျန်အကြွေး: {remaining} ကျပ်\n\n"
    return format_response(report)

def get_debt_for_person(person):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("""SELECT SUM(amount) FROM transactions WHERE type = 'ချေးငွေ' AND person = ? AND status = 'active'""", (person,))
    result = c.fetchone()[0]
    conn.close()
    return result if result else 0

def repay_debt(person, amount):
    current_debt = get_debt_for_person(person)
    if current_debt == 0:
        return format_response(f"⚠️ {person} ဆီက အကြွေးမရှိပါဆရာ။")
    if amount > current_debt:
        return format_response(f"⚠️ {person} ဆီက အကြွေးက {current_debt} ကျပ်ပဲရှိပါတယ်ဆရာ။ {amount} ကျပ်ထပ်မဆပ်နိုင်ပါ။")
    
    add_transaction("ပြန်ဆပ်ငွေ", amount, f"{person} ကို ပြန်ဆပ်", person)
    remaining = current_debt - amount
    if remaining == 0:
        return format_response(f"✅ {person} ဆီက အကြွေး အကုန်ပြန်ဆပ်ပြီးပါပြီဆရာ။")
    else:
        return format_response(f"✅ {person} ဆီက အကြွေး {amount} ကျပ် ပြန်ဆပ်ပြီးပါပြီဆရာ။ ကျန်အကြွေး: {remaining} ကျပ်")

# ============ ဖျက်ခြင်း Function များ ============

def delete_all_transactions():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions")
    c.execute("DELETE FROM notes")
    c.execute("DELETE FROM schedules")
    c.execute("DELETE FROM reminders")
    conn.commit()
    conn.close()
    backup_database()
    return format_response("✅ ဆရာရဲ့ စာရင်းအကုန်ကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")

def delete_today_transactions():
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    c.execute("DELETE FROM transactions WHERE date = ?", (today,))
    c.execute("DELETE FROM notes WHERE date = ?", (today,))
    conn.commit()
    conn.close()
    backup_database()
    return format_response(f"✅ ဆရာရဲ့ {today} စာရင်းကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")

def delete_category_transactions(category_type):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE type = ?", (category_type,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    backup_database()
    return format_response(f"✅ ဆရာရဲ့ {category_type} စာရင်း {deleted} ခုကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")

def delete_category_notes(category):
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    category_names = {'work': 'အလုပ်ကိစ္စ', 'personal': 'ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': 'အခြားကိစ္စ'}
    cat_name = category_names.get(category, category)
    c.execute("DELETE FROM notes WHERE category = ?", (category,))
    deleted = c.rowcount
    conn.commit()
    conn.close()
    backup_database()
    return format_response(f"✅ ဆရာရဲ့ {cat_name} မှတ်စု {deleted} ခုကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")
