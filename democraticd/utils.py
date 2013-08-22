import datetime

def iso_8601(dt):
    if dt.tzinfo:
        dt = dt.astimezone(tz=datetime.timezone.utc).replace(tzinfo=None)
    return dt.replace(microsecond=0).isoformat() + 'Z'


class DebugLevel:
    ESSENTIAL = 0
    INFO = 1
    DEBUG = 2
