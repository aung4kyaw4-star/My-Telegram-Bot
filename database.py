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
        category TEXT,
        status TEXT DEFAULT 'active'
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
    
    # မြန်မာလို ရက်စွဲပြန်ပို့
    month_names = ["ဇန်နဝါရီ", "ဖေဖော်ဝါရီ", "မတ်", "ဧပြီ", "မေ", "ဇွန်", 
                   "ဇူလိုင်", "သြဂုတ်", "စက်တင်ဘာ", "အောက်တိုဘာ", "နိုဝင်ဘာ", "ဒီဇင်ဘာ"]
    date_parts = date.split('-')
    month_str = month_names[int(date_parts[1]) - 1]
    myanmar_date = f"{date_parts[2]} {month_str} {date_parts[0]}"
    
    return f"✅ {transaction_type} {amount} ကျပ် ({myanmar_date} {time}) ကို အောင်မြင်စွာ မှတ်သားပြီးပါပြီ။"

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

def get_detailed_report(days=0, months=0):
    """အသေးစိတ်စာရင်းယူမယ် (ရက်စွဲ၊ အချိန်၊ လူ၊ ပမာဏ၊ ဖော်ပြချက် အကုန်ပါမယ်)"""
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
    
    # အသေးစိတ်ငွေစာရင်း (ရက်စွဲ၊ အချိန်၊ အမျိုးအစား၊ ပမာဏ၊ ဖော်ပြချက်၊ လူ)
    c.execute("""SELECT date, time, type, amount, description, person 
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
    
    conn.close()
    
    # Report စတင်ဆောက်မယ်
    report = f"📊 **{title} အသေးစိတ် အစီရင်ခံစာ**\n"
    report += f"📅 စာရင်းကောက်ချိန်: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # အကျဉ်းချုပ်
    report += "💰 **ငွေစာရင်း အကျဉ်းချုပ်**\n"
    total_in = 0
    total_out = 0
    summary_dict = {}
    for t in summary:
        summary_dict[t[0]] = t[1]
        if t[0] in ["ယူငွေ", "ပြန်ဆပ်ငွေ"]:
            total_in += t[1]
        else:
            total_out += t[1]
    
    # အကုန်ပြမယ်
    type_order = ["ယူငွေ", "သုံးငွေ", "ချေးငွေ", "ပြန်ဆပ်ငွေ"]
    for t in type_order:
        if t in summary_dict:
            report += f"  {t}: {summary_dict[t]} ကျပ်\n"
    
    report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n"
    report += f"  📉 ထွက်ငွေ: {total_out} ကျပ်\n"
    report += f"  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
    
    # အသေးစိတ်စာရင်း
    if transactions:
        report += "📋 **အသေးစိတ် ငွေစာရင်း**\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for t in transactions:
            date, time_val, trans_type, amount, desc, person = t
            
            # မြန်မာလို ရက်စွဲပုံစံ
            date_parts = date.split('-')
            month_names = ["ဇန်နဝါရီ", "ဖေဖော်ဝါရီ", "မတ်", "ဧပြီ", "မေ", "ဇွန်", 
                          "ဇူလိုင်", "သြဂုတ်", "စက်တင်ဘာ", "အောက်တိုဘာ", "နိုဝင်ဘာ", "ဒီဇင်ဘာ"]
            month_str = month_names[int(date_parts[1]) - 1]
            myanmar_date = f"{date_parts[2]} {month_str} {date_parts[0]}"
            
            # အမျိုးအစားလိုက် အထူးပြမယ်
            if trans_type == "ပြန်ဆပ်ငွေ":
                report += f"🔄 **{trans_type}**\n"
                report += f"   📅 {myanmar_date} ({time_val})\n"
                report += f"   💰 {amount} ကျပ်\n"
                if person and person.strip():
                    report += f"   👤 {person} ကို ပြန်ဆပ်\n"
                if desc and desc.strip():
                    report += f"   📝 {desc}\n"
            
            elif trans_type == "ချေးငွေ":
                report += f"💳 **{trans_type}**\n"
                report += f"   📅 {myanmar_date} ({time_val})\n"
                report += f"   💰 {amount} ကျပ်\n"
                if person and person.strip():
                    report += f"   👤 {person} ဆီမှ ချေး\n"
                if desc and desc.strip():
                    report += f"   📝 {desc}\n"
            
            elif trans_type == "သုံးငွေ":
                report += f"💸 **{trans_type}**\n"
                report += f"   📅 {myanmar_date} ({time_val})\n"
                report += f"   💰 {amount} ကျပ်\n"
                if desc and desc.strip():
                    report += f"   📝 {desc}\n"
                if person and person.strip():
                    report += f"   👤 {person}\n"
            
            elif trans_type == "ယူငွေ":
                report += f"💹 **{trans_type}**\n"
                report += f"   📅 {myanmar_date} ({time_val})\n"
                report += f"   💰 {amount} ကျပ်\n"
                if desc and desc.strip():
                    report += f"   📝 {desc}\n"
                if person and person.strip():
                    report += f"   👤 {person} ဆီမှ ရ\n"
            
            else:
                report += f"📌 **{trans_type}**\n"
                report += f"   📅 {myanmar_date} ({time_val})\n"
                report += f"   💰 {amount} ကျပ်\n"
                if desc and desc.strip():
                    report += f"   📝 {desc}\n"
                if person and person.strip():
                    report += f"   👤 {person}\n"
            
            report += "\n"
    
    else:
        report += "📋 စာရင်းမရှိပါ။\n"
    
    return report

def get_debt_details():
    """အကြွေးအသေးစိတ်စာရင်း"""
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()
    
    # လူတစ်ယောက်ချင်းစီရဲ့ အကြွေး
    c.execute("""SELECT person, SUM(amount), COUNT(*) 
                 FROM transactions 
                 WHERE type = 'ချေးငွေ' AND status = 'active'
                 GROUP BY person""")
    debts = c.fetchall()
    
    # ပြန်ဆပ်ပြီးသားစာရင်း
    c.execute("""SELECT person, SUM(amount), COUNT(*) 
                 FROM transactions 
                 WHERE type = 'ပြန်ဆပ်ငွေ' AND status = 'active'
                 GROUP BY person""")
    repayments = c.fetchall()
    
    conn.close()
    
    report = "📋 **အကြွေး အသေးစိတ်စာရင်း**\n\n"
    
    if not debts:
        report += "အကြွေးမရှိပါ။\n"
        return report
    
    # ပြန်ဆပ်ပြီးသားကို dict နဲ့သိမ်းမယ်
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
    
    return report

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
        return f"⚠️ {person} ဆီက အကြွေးမရှိပါ။"
    
    if amount > current_debt:
        return f"⚠️ {person} ဆီက အကြွေးက {current_debt} ကျပ်ပဲရှိပါတယ်။ {amount} ကျပ်ထပ်မဆပ်နိုင်ပါ။"
    
    # ပြန်ဆပ်ငွေအဖြစ် မှတ်မယ်
    add_transaction("ပြန်ဆပ်ငွေ", amount, f"{person} ကို ပြန်ဆပ်", person)
    
    remaining = current_debt - amount
    if remaining == 0:
        return f"""✅ {person} ဆီက အကြွေး အကုန်ပြန်ဆပ်ပြီးပါပြီ။
        
📋 အကြွေးမှတ်တမ်းကို ဘယ်လိုလုပ်ချင်လဲ။
• 'ဖျက်ပါ' - မှတ်တမ်းကိုဖျက်မယ်
• 'ထားပါ' - သမိုင်းကြောင်းအတွက် ဆက်ထားမယ်

ကျေးဇူးပြုပြီး ရွေးချယ်ပါ။"""
    else:
        return f"✅ {person} ဆီက အကြွေး {amount} ကျပ် ပြန်ဆပ်ပြီးပါပြီ။ ကျန်အကြွေး: {remaining} ကျပ်"
