import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ✅ မြန်မာ Timezone (UTC+6:30)
MYANMAR_TZ = datetime.timezone(datetime.timedelta(hours=6, minutes=30))

def get_now():
    """မြန်မာအချိန် ရယူခြင်း"""
    return datetime.datetime.now(MYANMAR_TZ)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///finance.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    date = Column(String(20))
    time = Column(String(20))
    type = Column(String(50))
    amount = Column(Float)
    description = Column(Text)
    person = Column(String(255))
    category = Column(String(50))
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=get_now)

class Note(Base):
    __tablename__ = 'notes'
    id = Column(Integer, primary_key=True)
    date = Column(String(20))
    time = Column(String(20))
    category = Column(String(50))
    title = Column(String(255))
    description = Column(Text)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=get_now)

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    date = Column(String(20))
    time = Column(String(20))
    title = Column(String(255))
    description = Column(Text)
    reminder_hours = Column(Integer, default=2)
    created_at = Column(DateTime, default=get_now)

class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer)
    reminder_time = Column(String(20))
    message = Column(Text)
    is_sent = Column(Integer, default=0)

def init_db():
    Base.metadata.create_all(engine)
    print("✅ Database initialized!")

def format_response(message):
    return f"{message}"

def add_transaction(transaction_type, amount, description="", person="", category=""):
    session = SessionLocal()
    try:
        now = get_now()
        trans = Transaction(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            type=transaction_type,
            amount=amount,
            description=description,
            person=person,
            category=category
        )
        session.add(trans)
        session.commit()
        return format_response(f"✅ ဆရာရဲ့ {transaction_type} {amount} ကျပ်ကို အကျွန်မှတ်ထားလိုက်ပါပြီဆရာ။")
    finally:
        session.close()

def add_note(category, title, description=""):
    session = SessionLocal()
    try:
        now = get_now()
        note = Note(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            category=category,
            title=title,
            description=description
        )
        session.add(note)
        session.commit()
        category_names = {'work': 'အလုပ်ကိစ္စ', 'personal': 'ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': 'အခြားကိစ္စ'}
        cat_name = category_names.get(category, category)
        return format_response(f"✅ ဆရာရဲ့ {cat_name} '{title}' ကို အကျွန်မှတ်ထားလိုက်ပါပြီဆရာ။")
    finally:
        session.close()

def add_schedule_with_reminder(date, time, title, description="", reminder_hours=2):
    session = SessionLocal()
    try:
        schedule = Schedule(
            date=date, time=time, title=title,
            description=description, reminder_hours=reminder_hours
        )
        session.add(schedule)
        session.commit()
        
        from datetime import datetime as dt, timedelta
        event_datetime = dt.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        reminder_datetime = event_datetime - timedelta(hours=reminder_hours)
        
        reminder = Reminder(
            schedule_id=schedule.id,
            reminder_time=reminder_datetime.strftime("%Y-%m-%d %H:%M"),
            message=f"⏰ သတိပေးချက်: {title} ကို {date} {time} တွင် ကျင်းပမည်"
        )
        session.add(reminder)
        session.commit()
        return format_response(f"✅ ဆရာရဲ့ အစီအစဉ် '{title}' ကို {date} {time} တွင် အကျွန်မှတ်သားပြီး အချိန်မှန်သတိပေးပါမည်ဆရာ။")
    finally:
        session.close()

def get_due_reminders():
    session = SessionLocal()
    try:
        now = get_now().strftime("%Y-%m-%d %H:%M")
        reminders = session.query(Reminder).filter(
            Reminder.reminder_time <= now,
            Reminder.is_sent == 0
        ).all()
        return [(r.id, r.message) for r in reminders]
    finally:
        session.close()

def mark_reminder_sent(reminder_id):
    session = SessionLocal()
    try:
        reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.is_sent = 1
            session.commit()
    finally:
        session.close()

def get_full_daily_report():
    session = SessionLocal()
    try:
        now_dt = get_now()
        today = now_dt.strftime("%Y-%m-%d")
        now = now_dt.strftime("%Y-%m-%d %H:%M")
        
        transactions = session.query(Transaction).filter(
            Transaction.date == today,
            Transaction.status == 'active'
        ).order_by(Transaction.time.desc()).all()
        
        notes = session.query(Note).filter(
            Note.date == today,
            Note.status == 'active'
        ).order_by(Note.time.desc()).all()
        
        schedules = session.query(Schedule).filter(
            Schedule.date == today
        ).order_by(Schedule.time.asc()).all()
        
        summary = {}
        for t in transactions:
            if t.type not in summary:
                summary[t.type] = 0
            summary[t.type] += t.amount
        
        report = f"📊 **{today} နေ့စဉ် အပြည့်အစုံ အစီရင်ခံစာ**\n📅 စာရင်းကောက်ချိန်: {now}\n\n"
        report += "💰 **ငွေစာရင်း**\n"
        total_in = 0
        total_out = 0
        for t in ["ယူငွေ", "သုံးငွေ", "ချေးငွေ", "ပြန်ဆပ်ငွေ"]:
            if t in summary:
                report += f"  {t}: {summary[t]} ကျပ်\n"
                if t in ["ယူငွေ", "ပြန်ဆပ်ငွေ"]:
                    total_in += summary[t]
                else:
                    total_out += summary[t]
        
        report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n  📉 ထွက်ငွေ: {total_out} ကျပ်\n  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
        
        if transactions:
            report += "📋 **ငွေစာရင်းအသေးစိတ်**\n"
            for t in transactions:
                report += f"  • {t.time} - {t.type} {t.amount} ကျပ်"
                if t.description:
                    report += f" ({t.description})"
                if t.person:
                    report += f" - {t.person}"
                report += "\n"
        else:
            report += "  ဒီနေ့ငွေစာရင်းမရှိပါ။\n"
        
        if schedules:
            report += "\n📅 **ဒီနေ့ အစီအစဉ်များ**\n"
            for s in schedules:
                report += f"  ⏰ {s.time} - {s.title}\n"
                if s.description:
                    report += f"     📝 {s.description}\n"
        else:
            report += "\n📅 ဒီနေ့အတွက် သတ်မှတ်ထားတဲ့ အစီအစဉ်မရှိပါ။\n"
        
        if notes:
            report += "\n📝 **မှတ်စုများ**\n"
            category_names = {'work': '💼 အလုပ်ကိစ္စ', 'personal': '👤 ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': '📌 အခြားကိစ္စ'}
            for n in notes:
                cat_name = category_names.get(n.category, n.category)
                report += f"\n  {cat_name}\n  ⏰ {n.time}\n  📌 {n.title}\n"
                if n.description:
                    report += f"  📝 {n.description}\n"
        else:
            report += "\n📝 ဒီနေ့မှတ်စုမရှိပါ။\n"
        
        return format_response(report)
    finally:
        session.close()

def get_detailed_report(days=0, months=0):
    session = SessionLocal()
    try:
        from datetime import timedelta
        now = get_now()
        today = now.date()
        
        if months > 0:
            start_date = today - timedelta(days=30*months)
            start_str = start_date.strftime("%Y-%m-%d")
            title = f"လွန်ခဲ့တဲ့ {months} လ"
        elif days > 1000:
            start_str = "2000-01-01"
            title = "အကုန်စာရင်း"
        elif days > 0:
            start_date = today - timedelta(days=days)
            start_str = start_date.strftime("%Y-%m-%d")
            title = f"လွန်ခဲ့တဲ့ {days} ရက်"
        else:
            start_str = today.strftime("%Y-%m-%d")
            title = "ဒီနေ့"
        
        transactions = session.query(Transaction).filter(
            Transaction.date >= start_str,
            Transaction.status == 'active'
        ).order_by(Transaction.date.desc(), Transaction.time.desc()).all()
        
        notes = session.query(Note).filter(
            Note.date >= start_str,
            Note.status == 'active'
        ).order_by(Note.date.desc(), Note.time.desc()).all()
        
        schedules = session.query(Schedule).filter(
            Schedule.date >= start_str
        ).order_by(Schedule.date.asc(), Schedule.time.asc()).all()
        
        summary = {}
        for t in transactions:
            if t.type not in summary:
                summary[t.type] = 0
            summary[t.type] += t.amount
        
        report = f"📊 **{title} အသေးစိတ် အစီရင်ခံစာ**\n📅 စာရင်းကောက်ချိန်: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
        report += "💰 **ငွေစာရင်း အကျဉ်းချုပ်**\n"
        total_in = 0
        total_out = 0
        for t in ["ယူငွေ", "သုံးငွေ", "ချေးငွေ", "ပြန်ဆပ်ငွေ"]:
            if t in summary:
                report += f"  {t}: {summary[t]} ကျပ်\n"
                if t in ["ယူငွေ", "ပြန်ဆပ်ငွေ"]:
                    total_in += summary[t]
                else:
                    total_out += summary[t]
        
        report += f"\n  📈 ဝင်ငွေ: {total_in} ကျပ်\n  📉 ထွက်ငွေ: {total_out} ကျပ်\n  💰 လက်ကျန်: {total_in - total_out} ကျပ်\n\n"
        
        if transactions:
            report += "📋 **ငွေစာရင်းအသေးစိတ်**\n"
            for t in transactions:
                report += f"\n  📅 {t.date} ({t.time})\n  📌 {t.type} {t.amount} ကျပ်"
                if t.description:
                    report += f"\n  📝 {t.description}"
                if t.person:
                    report += f"\n  👤 {t.person}"
                report += "\n"
        else:
            report += "  ငွေစာရင်းမရှိပါ။\n"
        
        if schedules:
            report += "\n📅 **အစီအစဉ်များ**\n"
            for s in schedules:
                report += f"\n  📅 {s.date} ({s.time})\n  📌 {s.title}\n"
                if s.description:
                    report += f"  📝 {s.description}\n"
        
        if notes:
            report += "\n📝 **မှတ်စုများ**\n"
            category_names = {'work': '💼 အလုပ်ကိစ္စ', 'personal': '👤 ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': '📌 အခြားကိစ္စ'}
            for n in notes:
                cat_name = category_names.get(n.category, n.category)
                report += f"\n  {cat_name}\n  📅 {n.date} ({n.time})\n  📌 {n.title}\n"
                if n.description:
                    report += f"  📝 {n.description}\n"
        
        return format_response(report)
    finally:
        session.close()

def get_category_report(category):
    session = SessionLocal()
    try:
        category_names = {'work': 'အလုပ်ကိစ္စ', 'personal': 'ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': 'အခြားကိစ္စ'}
        cat_name = category_names.get(category, category)
        
        notes = session.query(Note).filter(
            Note.category == category,
            Note.status == 'active'
        ).order_by(Note.date.desc(), Note.time.desc()).all()
        
        if not notes:
            return format_response(f"📋 {cat_name} စာရင်းမရှိပါဆရာ။")
        
        report = f"📋 **{cat_name} စာရင်း**\n\n"
        for n in notes:
            report += f"📅 {n.date} ({n.time})\n📌 {n.title}\n"
            if n.description:
                report += f"📝 {n.description}\n"
            report += "\n"
        return format_response(report)
    finally:
        session.close()

def get_debt_details():
    session = SessionLocal()
    try:
        debts = session.query(Transaction).filter(
            Transaction.type == 'ချေးငွေ',
            Transaction.status == 'active'
        ).all()
        repayments = session.query(Transaction).filter(
            Transaction.type == 'ပြန်ဆပ်ငွေ',
            Transaction.status == 'active'
        ).all()
        
        if not debts:
            return format_response("📋 အကြွေးမရှိပါဆရာ။")
        
        debt_dict = {}
        for d in debts:
            if d.person:
                if d.person not in debt_dict:
                    debt_dict[d.person] = {"debt": 0, "repaid": 0, "count": 0}
                debt_dict[d.person]["debt"] += d.amount
                debt_dict[d.person]["count"] += 1
        
        for r in repayments:
            if r.person and r.person in debt_dict:
                debt_dict[r.person]["repaid"] += r.amount
        
        report = "📋 **အကြွေး အသေးစိတ်စာရင်း**\n\n"
        for person, data in debt_dict.items():
            remaining = data["debt"] - data["repaid"]
            report += f"👤 **{person}**\n"
            report += f"   ချေးငွေ: {data['debt']} ကျပ် ({data['count']} ကြိမ်)\n"
            if data["repaid"] > 0:
                report += f"   ပြန်ဆပ်: {data['repaid']} ကျပ်\n"
            report += f"   ကျန်အကြွေး: {remaining} ကျပ်\n\n"
        
        return format_response(report)
    finally:
        session.close()

def get_debt_for_person(person):
    session = SessionLocal()
    try:
        debts = session.query(Transaction).filter(
            Transaction.type == 'ချေးငွေ',
            Transaction.person == person,
            Transaction.status == 'active'
        ).all()
        total = sum(d.amount for d in debts)
        return total if total else 0
    finally:
        session.close()

def repay_debt(person, amount):
    session = SessionLocal()
    try:
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
    finally:
        session.close()

def delete_all_transactions():
    session = SessionLocal()
    try:
        session.query(Transaction).delete()
        session.query(Note).delete()
        session.query(Schedule).delete()
        session.query(Reminder).delete()
        session.commit()
        return format_response("✅ ဆရာရဲ့ စာရင်းအကုန်ကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")
    finally:
        session.close()

def delete_today_transactions():
    session = SessionLocal()
    try:
        today = get_now().strftime("%Y-%m-%d")
        session.query(Transaction).filter(Transaction.date == today).delete()
        session.query(Note).filter(Note.date == today).delete()
        session.commit()
        return format_response(f"✅ ဆရာရဲ့ {today} စာရင်းကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")
    finally:
        session.close()

def delete_category_transactions(category_type):
    session = SessionLocal()
    try:
        count = session.query(Transaction).filter(Transaction.type == category_type).delete()
        session.commit()
        return format_response(f"✅ ဆရာရဲ့ {category_type} စာရင်း {count} ခုကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")
    finally:
        session.close()

def delete_category_notes(category):
    session = SessionLocal()
    try:
        category_names = {'work': 'အလုပ်ကိစ္စ', 'personal': 'ကိုယ်ရေးကိုယ်တာကိစ္စ', 'other': 'အခြားကိစ္စ'}
        cat_name = category_names.get(category, category)
        count = session.query(Note).filter(Note.category == category).delete()
        session.commit()
        return format_response(f"✅ ဆရာရဲ့ {cat_name} မှတ်စု {count} ခုကို အကျွန်ဖျက်လိုက်ပါပြီဆရာ။")
    finally:
        session.close()
