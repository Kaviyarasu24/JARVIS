from datetime import datetime


def get_current_time_text() -> str:
    """Return a friendly spoken time string."""
    return f"The current time is {datetime.now().strftime('%I:%M %p')}."
