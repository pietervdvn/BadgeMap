import json
import buttons
import display
import utime
import wifi
import math
import os
from Calendar import Calendar, WEEKDAYS

EUROPE_LONDON = 'GMT+0BST-1,M3.5.0/01:00:00,M10.5.0/02:00:00'
EUROPE_BRUSSELS = 'CET-1CEST-2,M3.5.0/02:00:00,M10.5.0/03:00:00'

WHITE = 0xFFFFFF
BLACK = 0x000000


class Main:
    logline = 0
    bigclock_mode = True
    font_color = BLACK
    background_color = WHITE
    """
    :type list[Calendar]
    """
    calendars = []
    timezone_offset = 1
    page = 0
    last_page_change = 0
    eligible_events = []
    lastclick = 0
    lastclick_key = None
    
    dirty = False

    def __init__(self):
        pass

    def log(self, text):
        display.drawText(0, self.logline * 12, text, BLACK)
        display.flush()
        self.logline += 1

    def format_time(self, datetime, apply_offset=True):
        hours = datetime[3] + (self.timezone_offset if apply_offset else 0)
        minutes = datetime[4]
        return '%02d:%02d' % (hours, minutes)

    def _format_date(self, datetime):
        return str(datetime[2]) + "/" + str(datetime[1])

    def draw_time(self, datetime=None, flush=True):
        """Draw the date & time.
        Returns the first free Y-height
        Clear the screen to prevent ghosting:
            - When the date changes.
            - When entering an alert.
            - When leaving an alert.
        """
        if datetime is None:
            datetime = utime.localtime()
        time_str = self.format_time(datetime, True)
        print("Time to display: ", time_str)
        big_clock = self.bigclock_mode
        font_color = self.font_color
        date_str = self._format_date(datetime)
        date_font = "permanentmarker22"
        if big_clock:
            date_font = "permanentmarker36"

        datestr_h = display.getTextHeight(date_str, date_font)
        datestr_y = 4
        if big_clock:
            datestr_y = display.height() - datestr_h - 12

        if (big_clock):
            display.drawFill(self.background_color)
            display.drawText(12, 0, time_str, font_color, '7x5', 8, 8)
        else:
            display.drawRect(0, 0, 0, datestr_h, True, self.background_color)
            display.flush()
            display.drawText(4, 0, time_str, font_color, '7x5', 4, 4)

        date_str_w = display.getTextWidth(date_str, date_font)

        display.drawText(display.width() - date_str_w - 6, datestr_y, date_str, font_color, date_font)

        weekday = WEEKDAYS[datetime[6]]
        weekday_font = date_font
        weekday_w = display.getTextWidth(weekday, weekday_font)
        weekday_h = display.getTextHeight(weekday, weekday_font)
        weekday_y = (datestr_h - weekday_h) + 4
        if big_clock:
            weekday_y = display.height() - weekday_h - 12
            weekday_w += 12
        display.drawText(display.width() - date_str_w - weekday_w - 9, weekday_y, weekday, font_color,
                         weekday_font)

        line_y = datestr_h + 11
        if not big_clock:
            display.drawLine(0, line_y, display.width(), line_y, 0x888888)
            display.drawLine(0, line_y + 1, display.width(), line_y + 1, 0xffffff)
            display.drawLine(0, line_y + 2, display.width(), line_y + 2, 0x888888)
        if flush:
            display.flush()
        return line_y + 3

    def update_calendars(self):
        for cal in self.calendars:
            display.drawRect(0, display.height() - 12, display.getTextWidth("Updating " + cal.name), 12, True, WHITE)
            display.drawText(0, display.height() - 12, "Updating " + cal.name)
            display.flush()
            cal.update(6 * 60 * 60)
        wifi.disconnect()

    def load_eligble_events(self):
        self.eligible_events.clear()
        for cal in self.calendars:
            for ev in cal.get_eligible_events(utime.time(), utime.time() + 15 * 24 * 60 * 60):
                self.eligible_events.append(ev)
        self.eligible_events.sort(key=lambda e: e.end_time())

    def draw_display(self, soft = False):
        print("Drawing display, bigclock_mode is " + str(self.bigclock_mode))
        if self.bigclock_mode or len(self.eligible_events) == 0:
            if (len(self.eligible_events)) == 0:
                display.drawText(0, display.height() - 12, "No events planned")
            self.draw_time()
            display.flush()
            return

        if not soft and not self.dirty or self.bigclock_mode:
            self.dirty = False
            display.drawFill(self.background_color)
        else:
            w = display.getTextWidth("00:00","7x5") * 8
            h = display.getTextHeight("00:00","7x5") * 8
            display.drawRect(0,0, w, h, True, self.background_color)
            display.flush()
            
        y = self.draw_time(flush=False)
        for event in self.eligible_events[0:3]:
            y = event.draw_on_display(self.format_time, self._format_date, self.font_color, self.background_color, 2, y, flush=False)
        display.flush()


    def draw_page(self):
        self.dirty = True
        items_per_page = 5
        range_start = self.page * items_per_page
        y = 0
        max_page_count = len(self.eligible_events)/items_per_page
        for ev in self.eligible_events[range_start: range_start + items_per_page]:
            y = ev.draw_on_display(self.format_time, self._format_date, self.font_color, self.background_color, 2, y, flush=False)
        msg = "Page "+str(self.page + 1)+"/"+str(math.ceil(max_page_count))
        msg_w = display.getTextWidth(msg)
        display.drawText(display.width() - msg_w, 0, msg, self.font_color)
        display.flush()
        self.last_page_change = utime.time()

    def recent_click(self, key):
        got_recent = utime.time() - self.lastclick < 1
        last_key = self.lastclick_key
        self.lastclick_key = key
        self.lastclick = utime.time()
        return last_key == key and got_recent

    def set_page(self, diff, key):
        if self.recent_click(key):
            return
        if utime.time() - self.last_page_change < 3:
            print("Not changing page: update is very fresh")
            return
        print("Setting and drawing page, diff "+str(diff)+" current: "+str(self.page))
        self.page = max(0, self.page + diff)
        self.page = min(self.page, len(self.eligible_events) // 5)
        display.drawFill(self.background_color)
        self.draw_page()
        self.dirty = True

    @property
    def main(self):
        print("Booting the DeskClock")
        print("Setting active directory")
        appdir = "/lib/deskcalendar"
        os.chdir(appdir)
        display.drawFill(WHITE)
        self.log("Connecting to WiFi...")
        wifi.connect()
        wifi.wait()
        while not wifi.status():
            self.log("Wifi not connected, waiting a bit more")
            utime.sleep(1)
            wifi.connect()
            wifi.wait()
        self.log("Wifi connected! Syncing ntp")
        wifi.ntp()
        self.log("Ntp synced!")
        display.drawFill(WHITE)
        self.draw_time()
        config = []
        try:
            with open("calendar_config.json", "r") as f:
                config = json.loads(f.read())
        except:
            print("ERROR: could not open 'calendar_config.json' - make sure the file exists and is valid JSON")
            
        for calconf in config:
            url = calconf["url"]
            name = calconf["name"]
            print("Loading calendar " + url)
            cal = None
            if "password" in calconf:
                cal = Calendar(name, url, appdir, calconf["username"], calconf["password"])
            else:
                cal = Calendar(name, url, appdir)
            self.calendars.append(cal)

        self.update_calendars()
        self.load_eligble_events()
        self.bigclock_mode = len(self.eligible_events) == 0
        if not self.bigclock_mode:
            display.drawFill(self.background_color)
            self.draw_display()

        def swap_mode(v, key):
            if self.recent_click(key):
                return
            if self.bigclock_mode == v:
                return
            self.bigclock_mode = v
            display.drawFill(self.background_color)
            display.flush()
            self.draw_display()


        buttons.attach(buttons.BTN_A, lambda b: swap_mode(True, b))
        buttons.attach(buttons.BTN_B, lambda b: swap_mode(False, b))

        buttons.attach(buttons.BTN_LEFT, lambda b: self.set_page(-1, b))
        buttons.attach(buttons.BTN_RIGHT, lambda b: self.set_page(1, b))

        print("Attached buttons")
        cal_update_frq = 60 * 60 * 6
        event_reload_frq = 15 * 60
        last_cal_update_time = utime.time() // cal_update_frq
        last_reload_time = utime.time() // event_reload_frq
        last_update_time = utime.time() // 60

        self.lastclick = utime.time()
        while True:
            if utime.time() - self.lastclick < 60:
                utime.sleep(0.1)
            else:
                utime.sleep(3)

            now_rounded = utime.time() // 60
            if self.dirty:
                display.drawFill(self.background_color)
                self.dirty = False
                
            # start_times = list(filter(lambda e: not e.whole_day(), self.eligible_events))
            # earliest = start_times[0]
            # current_time = utime.time()
            # earliest_tdif = 3600 + utime.mktime(earliest.start_time()) - current_time
             
            if last_update_time != now_rounded:
                if utime.time() - self.last_page_change < 60:
                    print("Not changing drawing clock: user is still watching their calendar")
                    continue
                print("Updating: clock has changed")
                last_update_time = now_rounded
                display.flush()
                self.draw_display(soft=not self.dirty)
                
            now_reload = utime.time() // event_reload_frq
            if now_reload != last_reload_time:
                last_reload_time = now_reload
                self.load_eligble_events()
                self.draw_display()
                
            now_cal_update = utime.time() // cal_update_frq
            if last_cal_update_time != now_cal_update:
                self.update_calendars()
                self.load_eligble_events()
                self.draw_display()
                last_cal_update_time = now_cal_update


Main().main
