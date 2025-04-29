import datetime

def format_week_range(days: list[datetime.date]) -> str:
    """Format a list of dates into a week range string (DD.MM - DD.MM)."""
    if not days:
        return ""
    start, end = days[0], days[-1]
    # Always use DD.MM format for both start and end
    return f"{start.strftime('%d.%m')} - {end.strftime('%d.%m')}"
