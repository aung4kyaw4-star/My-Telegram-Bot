def check_duplicate_note(category, title):
    """မှတ်စု ထပ်နေလား စစ်ဆေးခြင်း"""
    session = SessionLocal()
    try:
        existing = session.query(Note).filter(
            Note.category == category,
            Note.title == title,
            Note.status == 'active'
        ).first()
        return existing is not None
    finally:
        session.close()


def check_duplicate_transaction(trans_type, amount, description, person=""):
    """ငွေစာရင်း ထပ်နေလား စစ်ဆေးခြင်း"""
    session = SessionLocal()
    try:
        today = get_now().strftime("%Y-%m-%d")
        existing = session.query(Transaction).filter(
            Transaction.date == today,
            Transaction.type == trans_type,
            Transaction.amount == amount,
            Transaction.description == description,
            Transaction.status == 'active'
        ).first()
        return existing is not None
    finally:
        session.close()


def check_duplicate_schedule(date, time, title):
    """အစီအစဉ် ထပ်နေလား စစ်ဆေးခြင်း"""
    session = SessionLocal()
    try:
        existing = session.query(Schedule).filter(
            Schedule.date == date,
            Schedule.time == time,
            Schedule.title == title
        ).first()
        return existing is not None
    finally:
        session.close()
