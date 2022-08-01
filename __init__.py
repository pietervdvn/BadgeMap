import display
from CalendarDisplay import *

def main():
    clock = Clock()
    
    password = None
    passwordpath = "/sd/apps/python/badgemap/calendar1.ics.password"
    try:
        f = open(passwordpath, "r")
        password = f.read()
        f.close()
    except Exception:
        print("Could not read password file")
    
    if password is None:
        password = input("password? ")
        f = open(passwordpath, "w")
        f.write(password)
        f.close()
    c = Calendar(clock, "/sd/apps/python/badgemap/calendar1.ics", password)
    c.update((0, 0, 0, 0, 1, 0))
    events: [VEvent] = c.active_next((2022, 7, 1, 0, 0, 0), (2022, 8, 1, 0, 0, 0), 100)



display.drawFill(0)
y = draw_time((2022,7,31,19,32,00,1))
y = draw_event(dummy_day_event(), 0, y)
y = draw_event(dummy_event(), 0, y)
