from datetime import datetime
import calendar
import time as time_mod
"""
https://docs.micropython.org/en/latest/library/time.html
"""

def localtime(secs = None):
    return time_mod.localtime(secs)

def sleep(param):
    time_mod.sleep(param)


def time():
    """
    Returns the number of seconds, as an integer, since the Epoch
    :return: 
    """
    return (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()


def gmtime(secs = None):
    return time_mod.gmtime(secs)

def mktime(date_tuple):
    t = datetime(date_tuple[0], date_tuple[1], date_tuple[2],date_tuple[3] ,date_tuple[4],date_tuple[5])
    return calendar.timegm(t.timetuple())