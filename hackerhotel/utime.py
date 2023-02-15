from datetime import datetime
"""
https://docs.micropython.org/en/latest/library/time.html
"""

def localtime(secs = None):
    return (2023,12,31,23,59,59,6,366)

def sleep(param):
    return


def time():
    """
    Returns the number of seconds, as an integer, since the Epoch
    :return: 
    """
    return (datetime.now() - datetime.utcfromtimestamp(0)).total_seconds()


def gmtime(secs = None):
    return localtime()

def mktime(date_tuple):
    return 0