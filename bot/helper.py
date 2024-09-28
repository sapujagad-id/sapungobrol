from datetime import datetime, timezone

def relative_time(date: datetime) -> str:
    '''
    Parameters
    -----
    date: datetime or string in the format of <YYYY-MM-DD hh:mm:ss+TZ> \n
    this is meant to support TIMESTAMPTZ from postgres
    
    Returns
    -----
    relative time: string in the format of "x days ago" or "x minutes ago"
    '''
    parsed_date = datetime.fromisoformat(str(date).replace("+00:00", ""))

    # Get the current time
    now = datetime.now() # Ensure we use the same timezone
    print("awooga", parsed_date, now)

    # Compute the time difference (as a timedelta object)
    delta = now - parsed_date
    
    seconds = delta.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    weeks = days // 7
    months = days // 30
    years = days // 365
    
        
    if years >= 1:
        return f"{int(years)} year{'s' if years > 1 else ''} ago"
    elif months >= 1:
        return f"{int(months)} month{'s' if months > 1 else ''} ago"
    elif weeks >= 1:
        return f"{int(weeks)} week{'s' if weeks > 1 else ''} ago"
    elif days >= 1:
        return f"{int(days)} day{'s' if days > 1 else ''} ago"
    elif hours >= 1:
        return f"{int(hours)} hour{'s' if hours > 1 else ''} ago"
    elif minutes >= 1:
        return f"{int(minutes)} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"