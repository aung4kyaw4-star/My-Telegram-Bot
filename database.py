import sqlite3
import datetime
import os
import json

def init_db():
    """Database ကို စတင်သတ်မှတ်မယ်"""
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
        category TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )''')
    
    # မှတ်စု Table (အလုပ်၊ ကိုယ်ရေး၊ အခြား)
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
    
    # Backup Log Table
    c.execute('''CREATE TABLE IF NOT EXISTS backup_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_date TEXT,
        backup_time TEXT,
        record_count INTEGER,
        status TEXT
    )''')
    
    conn.commit()
    conn.close()
    
    # Database ကို Backup လုပ်မယ်
    backup_database()

def backup_database():
    """Database ကို Backup သိမ်းမယ်"""
    try:
        # Backup folder ဖန်တီးမယ်
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        # Backup file name
        now = datetime.datetime.now()
        backup_name = f"backups/finance_backup_{now.strftime('%Y-%m-%d')}.db"
        
        # Database ကို copy ကူးမယ်
        import shutil
        if os.path.exists('finance.db'):
            shutil.copy2('finance.db', backup_name)
            
            # Backup log သိမ်းမယ်
            conn = sqlite3.connect('finance.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM transactions")
            count = c.fetchone()[0]
            conn.close()
            
            conn = sqlite3.connect('finance.db')
            c = conn.cursor()
            c.execute("INSERT INTO backup_log (backup_date, backup_time, record_count, status) VALUES (?, ?, ?, ?)",
                      (now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), count, 'success'))
            conn.commit()
            conn.close()
            
            print(f"✅ Backup saved: {backup_name}")
    except Exception as e:
        print(f"❌ Backup error: {e}")

def add_transaction(transaction_type, amount, description="", person="", category=""):
    """ငွေစာရင်းထည့်မယ်"""
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
    
    # ပြန်ဖြေမယ်
    return format_response(f"✅ ဆရာရဲ့ {transaction_type} {amount} ကျပ်ကို အကျွန်မှတ်ထားလိုက်ပါပြီဆရာ။")

def add_note(category, title, description=""):
    """မှတ်စုထည့်မယ် (အလုပ်၊ ကိုယ်ရေး၊ အခြား)"""
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
    """အစီအစဉ်သိမ်းမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # အစီအစဉ် Table ရှိမရှိစစ်မယ်
    c.execute('''CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        time TEXT,
        title TEXT,
        description TEXT,
        reminder_hours INTEGER DEFAULT 2,
        created_at TEXT
    )''')
    
    # သတိပေးချက် Table
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        schedule_id INTEGER,
        reminder_time TEXT,
        message TEXT,
        is_sent INTEGER DEFAULT 0
    )''')
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO schedules (date, time, title, description, reminder_hours, created_at) VALUES (?, ?, ?, ?, ?, ?)",
              (date, time, title, description, reminder_hours, now))
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
    return format_response(f"✅ ဆရာရဲ့ အစီအစဉ် '{title}' ကို {date} {time} တွင် အကျွန်မှတ်သားပြီး အချိန်မှန်သတိပေးပါမည်ဆရာ။")

def get_due_reminders():
    """သတိပေးရန်ကျန်နေသေးတဲ့အချက်တွေ"""
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

def format_response(message):
    """ဆရာနဲ့အကျွန်ပုံစံ ပြန်ဖြေမယ်"""
    return f"{message}"

def get_full_daily_report():
    """နေ့စဉ် အပြည့်အစုံစာရင်း - ငွေ၊ အလုပ်၊ ကိုယ်ရေး၊ အခြား အကုန်ပါမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # ၁။ ငွေစာရင်း
    c.execute("""SELECT type, SUM(amount) 
                 FROM transactions 
                 WHERE date = ? AND status = 'active'
                 GROUP BY type""", (today,))
    summary = c.fetchall()
    
    c.execute("""SELECT date, time, type, amount, description, person, category 
                 FROM transactions 
                 WHERE date = ? AND status = 'active'
                 ORDER BY time DESC""", (today,))
    transactions = c.fetchall()
    
    # ၂။ မှတ်စုများ (အလုပ်၊ ကိုယ်ရေး၊ အခြား)
    c.execute("""SELECT category, title, description, time 
                 FROM notes 
                 WHERE date = ? AND status = 'active'
                 ORDER BY time DESC""", (today,))
    notes = c.fetchall()
    
    conn.close()
    
    # Report စတင်ဆောက်မယ်
    report = f"📊 **{today} နေ့စဉ် အပြည့်အစုံ အစီရင်ခံစာ**\n"
    report += f"📅 စာရင်းကောက်ချိန်: {now}\n\n"
    
    # ====== ငွေစာရင်း ======
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
    
    report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n"
    report += f"  📉 ထွက်ငွေ: {total_out} ကျပ်\n"
    report += f"  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
    
    # အသေးစိတ်ငွေစာရင်း
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
    
    # ====== မှတ်စုများ ======
    if notes:
        report += "\n📝 **မှတ်စုများ**\n"
        category_names = {
            'work': '💼 အလုပ်ကိစ္စ',
            'personal': '👤 ကိုယ်ရေးကိုယ်တာကိစ္စ',
            'other': '📌 အခြားကိစ္စ'
        }
        for category, title, description, time_val in notes:
            cat_name = category_names.get(category, category)
            report += f"\n  {cat_name}\n"
            report += f"  ⏰ {time_val}\n"
            report += f"  📌 {title}\n"
            if description:
                report += f"  📝 {description}\n"
    else:
        report += "\n📝 ဒီနေ့မှတ်စုမရှိပါ။\n"
    
    return format_response(report)

def get_detailed_report(days=0, months=0):
    """အချိန်ကာလအလိုက် အသေးစိတ်စာရင်း"""
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
    
    # ငွေစာရင်း
    c.execute("""SELECT date, time, type, amount, description, person, category 
                 FROM transactions 
                 WHERE date >= ? AND status = 'active'
                 ORDER BY date DESC, time DESC""", (start_str,))
    transactions = c.fetchall()
    
    # အကျဉ်းချုပ်
    c.execute("""SELECT type, SUM(amount) 
                 FROM transactions 
                 WHERE date >= ? AND status = 'active'
                 GROUP BY type""", (start_str,))
    summary = c.fetchall()
    
    # မှတ်စုများ
    c.execute("""SELECT date, time, category, title, description 
                 FROM notes 
                 WHERE date >= ? AND status = 'active'
                 ORDER BY date DESC, time DESC""", (start_str,))
    notes = c.fetchall()
    
    conn.close()
    
    report = f"📊 **{title} အသေးစိတ် အစီရင်ခံစာ**\n"
    report += f"📅 စာရင်းကောက်ချိန်: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # ငွေစာရင်းအကျဉ်းချုပ်
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
    
    report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n"
    report += f"  📉 ထွက်ငွေ: {total_out} ကျပ်\n"
    report += f"  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
    
    # အသေးစိတ်ငွေစာရင်း
    if transactions:
        report += "📋 **ငွေစာရင်းအသေးစိတ်**\n"
        for t in transactions:
            date, time_val, trans_type, amount, desc, person, category = t
            date_parts = date.split('-')
            month_names = ["ဇန်နဝါရီ", "ဖေဖော်ဝါရီ", "မတ်", "ဧပြီ", "မေ", "ဇွန်", 
                          "ဇူလိုင်", "သြဂုတ်", "စက်တင်ဘာ", "အောက်တိုဘာ", "နိုဝင်ဘာ", "ဒီဇင်ဘာ"]
            month_str = month_names[int(date_parts[1]) - 1]
            myanmar_date = f"{date_parts[2]} {month_str} {date_parts[0]}"
            
            report += f"\n  📅 {myanmar_date} ({time_val})\n"
            report += f"  📌 {trans_type} {amount} ကျပ်"
            if desc:
                report += f"\n  📝 {desc}"
            if person:
                report += f"\n  👤 {person}"
            report += "\n"
    else:
        report += "  ငွေစာရင်းမရှိပါ။\n"
    
    # မှတ်စုများ
    if notes:
        report += "\n📝 **မှတ်စုများ**\n"
        category_names = {
            'work': '💼 အလုပ်ကိစ္စ',
            'personal': '👤 ကိုယ်ရေးကိုယ်တာကိစ္စ',
            'other': '📌 အခြားကိစ္စ'
        }
        for date, time_val, category, title, description in notes:
            cat_name = category_names.get(category, category)
            date_parts = date.split('-')
            month_names = ["ဇန်နဝါရီ", "ဖေဖော်ဝါရီ", "မတ်", "ဧပြီ", "မေ", "ဇွန်", 
                          "ဇူလိုင်", "သြဂုတ်", "စက်တင်ဘာ", "အောက်တိုဘာ", "နိုဝင်ဘာ", "ဒီဇင်ဘာ"]
            month_str = month_names[int(date_parts[1]) - 1]
            myanmar_date = f"{date_parts[2]} {month_str} {date_parts[0]}"
            
            report += f"\n  {cat_name}\n"
            report += f"  📅 {myanmar_date} ({time_val})\n"
            report += f"  📌 {title}\n"
            if description:
                report += f"  📝 {description}\n"
    
    return format_response(report)

def get_debt_details():
    """အကြွေးအသေးစိတ်စာရင်း"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    c.execute("""SELECT person, SUM(amount), COUNT(*) 
                 FROM transactions 
                 WHERE type = 'ချေးငွေ' AND status = 'active'
                 GROUP BY person""")
    debts = c.fetchall()
    
    c.execute("""SELECT person, SUM(amount), COUNT(*) 
                 FROM transactions 
                 WHERE type = 'ပြန်ဆပ်ငွေ' AND status = 'active'
                 GROUP BY person""")
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
        
        report += f"👤 **{person}**\n"
        report += f"   ချေးငွေ: {total_debt} ကျပ် ({count} ကြိမ်)\n"
        if repaid["amount"] > 0:
            report += f"   ပြန်ဆပ်: {repaid['amount']} ကျပ် ({repaid['count']} ကြိမ်)\n"
        report += f"   ကျန်အကြွေး: {remaining} ကျပ်\n\n"
    
    return format_response(report)

def get_debt_for_person(person):
    """လူတစ်ယောက်ရဲ့ အကြွေးကိုယူမယ်"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    c.execute("""SELECT SUM(amount) 
                 FROM transactions 
                 WHERE type = 'ချေးငွေ' AND person = ? AND status = 'active'""", (person,))
    result = c.fetchone()[0]
    conn.close()
    return result if result else 0

def repay_debt(person, amount):
    """အကြွေးပြန်ဆပ်မယ်"""
    current_debt = get_debt_for_person(person)
    if current_debt == 0:
        return format_response(f"⚠️ {person} ဆီက အကြွေးမရှိပါဆရာ။")
    
    if amount > current_debt:
        return format_response(f"⚠️ {person} ဆီက အကြွေးက {current_debt} ကျပ်ပဲရှိပါတယ်ဆရာ။ {amount} ကျပ်ထပ်မဆပ်နိုင်ပါ။")
    
    add_transaction("ပြန်ဆပ်ငွေ", amount, f"{person} ကို ပြန်ဆပ်", person)
    
    remaining = current_debt - amount
    if remaining == 0:
        return format_response(f"""✅ {person} ဆီက အကြွေး အကုန်ပြန်ဆပ်ပြီးပါပြီဆရာ။
        
📋 အကြွေးမှတ်တမ်းကို ဘယ်လိုလုပ်ချင်လဲဆရာ။
• 'ဖျက်ပါ' - မှတ်တမ်းကိုဖျက်မယ်
• 'ထားပါ' - သမိုင်းကြောင်းအတွက် ဆက်ထားမယ်

ကျေးဇူးပြုပြီး ရွေးချယ်ပါဆရာ။""")
    else:
        return format_response(f"✅ {person} ဆီက အကြွေး {amount} ကျပ် ပြန်ဆပ်ပြီးပါပြီဆရာ။ ကျန်အကြွေး: {remaining} ကျပ်")
