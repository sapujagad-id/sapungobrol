from datetime import datetime

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
    now = datetime.now()

    # compute the time difference
    delta = now - parsed_date
    seconds = delta.total_seconds()

    # define time units in seconds
    time_units = [
        (60, 'minute'),
        (60 * 60, 'hour'),
        (60 * 60 * 24, 'day'),
        (60 * 60 * 24 * 7, 'week'),
        (60 * 60 * 24 * 30, 'month'),
        (60 * 60 * 24 * 365, 'year')
    ]

    for unit_seconds, unit_name in reversed(time_units):
        if seconds >= unit_seconds:
            value = int(seconds // unit_seconds)
            return f"{value} {unit_name}{'s' if value > 1 else ''} ago"
    return "just now"