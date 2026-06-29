def date_prefix(period: str) -> str | None:
    from datetime import date, timedelta
    today = date.today()
    p = period.lower()
    MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
              "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
    if p == "last month":
        first = today.replace(day=1)
        last = (first - timedelta(days=1)).replace(day=1)
        return last.strftime("%Y-%m")
    if p == "this month":
        return today.strftime("%Y-%m")
    if p == "this year":
        return str(today.year)
    if p in MONTHS:
        return f"{today.year}-{str(MONTHS[p]).zfill(2)}"
    return None