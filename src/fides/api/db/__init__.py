from datetime import date, datetime
from json import dumps


def default_serialize(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def json_serializer(obj):
    """JSON serializer that handles dates, to plug in for SQLAlchemy engine JSON serialization"""
    return dumps(obj, default=default_serialize)
