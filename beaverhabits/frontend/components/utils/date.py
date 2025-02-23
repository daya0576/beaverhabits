import datetime

def format_week_range(days: list[datetime.date]) -> str:
    """Format a list of dates into a week range string."""
    if not days:
        return ""
    start, end = days[0], days[-1]
    if start.month == end.month:
        return f"{start.strftime('%b %d')} - {end.strftime('%d')}"
    return f"{start.strftime('%b %d')} - {end.strftime('%b %d')}"
