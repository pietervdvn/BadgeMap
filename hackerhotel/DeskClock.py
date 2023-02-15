import gc
import json
import os

import ubinascii

import buttons
import display
import mrequests
import utils
import utime
import wifi

EUROPE_LONDON = 'GMT+0BST-1,M3.5.0/01:00:00,M10.5.0/02:00:00'
EUROPE_BRUSSELS = 'CET-1CEST-2,M3.5.0/02:00:00,M10.5.0/03:00:00'

WHITE = 0xFFFFFF
BLACK = 0x000000

FONTS = {
    '7x5': '7x5',
    'Dejavu Sans': {
        20: 'dejavusans20',
    },
    'Ocra': {
        16: 'ocra16',
        22: 'ocra22',
    },
    'Permanent Marker': {
        22: 'permanentmarker22',
        36: 'permanentmarker36',
    },
    'Roboto Regular': {
        12: 'roboto_regular12',
        18: 'roboto_regular18',
        22: 'roboto_regular22',
    },
    'Roboto Black': {
        22: 'roboto_black22',
    },
    'Roboto Black Italic': {
        24: 'roboto_blackitalic24',
    },
}

WEEKDAYS = {
    1: 'Sun',
    2: 'Mon',
    3: 'Tue',
    4: 'Wed',
    5: 'Thu',
    6: 'Fri',
    7: 'Sat'
}

TOPIC_INFO = b'home/house/alert/info_string'


def sum_date(date0, date1):
    summed = tuple(
        map(lambda tpl: tpl[0] + tpl[1], zip(date0, date1)))
    _normalize_sum(summed)
    return summed


def _normalize_sum(date):
    if (date[5] >= 60):
        date[4] += date[5] // 60
        date[5] %= 60
    if (date[4] >= 60):
        date[3] += date[4] // 60
        date[4] %= 60
    if (date[3] >= 24):
        date[2] += date[3] // 24
        date[2] %= 24


def init_wifi():
    """Set up the WiFi."""
    if wifi.status():
        return True
    wifi.connect()
    return wifi.wait()


class VEvent:

    def __init__(self, properties):
        self.properties = properties

    @staticmethod
    def parse_date(datetime, isEndDate=False):
        year = int(datetime[0:4])
        month = int(datetime[4:6])
        day = int(datetime[6:8])
        if len(datetime) <= 8 and isEndDate:
            return year, month, day, 23, 59, 59
        if len(datetime) <= 8:
            return year, month, day, 0, 0, 0
        hour = int(datetime[9:11])
        min = int(datetime[11:13])
        sec = int(datetime[13:15])
        tpl = (year, month, day, hour, min, sec, 0, 0)
        return utime.gmtime(int(utime.mktime(tpl)))

    def whole_day(self):
        return not (self.properties["DTSTART"].find("T") > 0 and self.properties["DTEND"].find("T") > 0)

    def start_time(self):
        """Returns a six-tuple with the start-time"""
        if "DTSTART" not in self.properties:
            return None
        return VEvent.parse_date(self.properties["DTSTART"])

    def end_time(self):
        if "DTEND" not in self.properties:
            return None
        datetime = self.properties["DTEND"]
        return VEvent.parse_date(datetime)

    def activeDuring(self, start, end=None):
        """
        Indicates if the event _overlaps_ with the given time, i.e. the specified start-time falls before the end-time of the event
        and vice versa.
        :param start: 
        :param end: 
        :return: 
        """
        self_end_time = self.end_time()
        return (self_end_time is not None and start < self_end_time) and (end is None or self.start_time() < end)

    def summary(self):
        l = ""
        if "LOCATION" in self.properties:
            l = " location: " + self.properties["LOCATION"]
        return self.properties["SUMMARY"] + l

    def draw_on_display(self, format_time, fgcolor, bgcolor, x=0, y=0, flush = True):
        strt_tuple = self.start_time()

        today = utime.localtime()
        midnight = utime.mktime((today[0], today[1], today[2], 0, 0, 0, 0, 0))
        coming_midnight = utime.localtime(int(midnight) + 24 * 60 * 60)
        strt = format_time(strt_tuple)
        if self.whole_day():
            x += display.getTextWidth("00:00") + 5
        elif coming_midnight < self.start_time():
            # Not today - we show a day of week instead + starting hour
            display.drawText(x, y, WEEKDAYS[strt_tuple[6]])
            end = format_time(self.end_time())
            display.drawText(x, y + display.getTextHeight(strt) + 1, strt)
            x += display.getTextWidth("00:00") + 5
            pass
        else:
            display.drawText(x, y, strt)
            end = format_time(self.end_time())
            display.drawText(x, y + display.getTextHeight(strt) + 1, end)
            x += display.getTextWidth("00:00") + 5

        location_font = "org18"
        summary_font = "roboto_black22"
        if "LOCATION" in self.properties:
            loc = utils.str_safe(self.properties["LOCATION"])
            loc_w = display.getTextWidth(loc, location_font)
            display.drawText(display.width() - loc_w, y, loc, 0xcccccc, location_font)
        display.drawText(x, y, utils.str_safe(self.properties["SUMMARY"]), fgcolor, summary_font)
        line_y = y + 6 + display.getTextHeight("Abcdef", summary_font)
        display.drawLine(x, line_y, display.width() - 5, line_y, 0x888888)
        if flush:
            display.flush()
        return 4 + y + display.getTextHeight("Abcdef", summary_font)


class Calendar:
    def __init__(self,
                 calendar_name,
                 url,
                 username=None,
                 password=None,
                 ):
        print("Initing calendar with URL:" + url)
        self.name = calendar_name
        self.path_to_save = "calendardata/" + calendar_name
        self.password = password
        self.username = username
        self.url = url

    def update(self, allowed_difference=None):
        """
        Updates and saves to file
        :param allowed_difference: if version on disk is less then 'allowed_difference'-old, don't download
        :return: 
        """
        if "calendardata" not in os.listdir():
            os.mkdir("calendardata")

        if allowed_difference is not None:
            try:
                with open(self.path_to_save + ".meta", "r") as fmeta:
                    metainfo = float(fmeta.read())
                    print("metainfo is " + str(metainfo))
                    timediff = utime.time() - metainfo
                    if timediff < allowed_difference:
                        print("No need to update this calendar; still fresh enough")
                        return
            except Exception as e:
                print("Metafile does not exist or cannot be read: " + str(e))
        if not wifi.status():
            print("Connecting to wifi...")
            wifi.connect()
            wifi.wait()
            print("Connected!")
        headers = {"Authorization": None}
        if self.password is not None:
            headers["Authorization"] = "Basic " + ubinascii.b2a_base64(self.username + ":" + self.password).decode(
                "UTF8")

        # NOTE the stream=True parameter below
        print("Attempting to save to " + self.path_to_save)
        r = mrequests.get(self.url, headers=headers)
        r.save(self.path_to_save + ".temp")
        print("Got a response, written to " + self.path_to_save)

        with open(self.path_to_save + ".temp", 'r') as f:
            # we copy the 'temp'-file line by line, but only if the events are still going on or in the future
            with open(self.path_to_save, 'w') as target:
                lines = []
                should_save = False
                linecount = 0
                copied = 0
                while True:
                    if linecount % 500 == 0:
                        print("Skipping/copying lines, currently handled " + str(linecount) + " and found " + str(
                            copied) + " events")
                        gc.collect()
                    line = f.readline(500)
                    linecount += 1
                    if line is None or line == "":
                        break
                    line = line.rstrip("\n\r")
                    if line == "":
                        continue

                    lines.append(line)
                    if line.startswith("DTEND"):
                        [_, date] = line.split(":")
                        d = VEvent.parse_date(date)
                        current_date = utime.gmtime()
                        if d >= current_date:
                            should_save = True
                            print("Detected an dtend in the future at line " + str(linecount) + " " + line)
                    if line == "BEGIN:VEVENT":
                        lines = [line]
                        should_save = False
                        gc.collect()
                        continue
                    if line == "END:VEVENT":
                        if should_save:
                            should_save = False
                            copied += 1
                            for line in lines:
                                target.write(line + "\n")

            os.rmdir(self.path_to_save + ".temp")

            modification_time = utime.time()
            with open(self.path_to_save + ".meta", "w") as fmeta:
                fmeta.write(str(modification_time))

    def active_next(self, start, end, max_count=9999999):
        """
        Returns a list of all VEVENTs that are active between 'start' and 'end'
        :param ical_text: 
        :param start: (y, m, d, h, m, s)
        :param end: (y, m, d, h, m, s)
        :return: list of dicts
        """
        print("Determining active events between " + str(start) + " and " + str(end))
        matching_events = []

        def on_event(event: VEvent, index: int):
            if event.activeDuring(start, end):
                matching_events.append(event)
                return len(matching_events) <= max_count

        self.parse_ics_from_file(on_event)

        return matching_events

    __current_draw_y = 0

    def get_eligible_events(self, start_date, end_date):
        # events are _not_ sorted, we first create a list
        eligible_events = []
        print("Start date:" + str(start_date))

        def handle(event, index):
            """
            :type event: VEvent
            :type index: int
            """
            print("Handling event " + str(index) + event.summary())
            if event.properties is None:
                return True
            if event.activeDuring(utime.gmtime(int(start_date)), utime.gmtime(int(end_date))):
                # Yeah, this is ugly... But well, python doesn't properly support closures...
                eligible_events.append(event)
                print("Eligeble: " + event.summary())
            return True

        self.parse_ics_from_file(handle)
        print("Got " + str(len(eligible_events)) + " eligble events!")
        return eligible_events

    def parse_ics_from_file(self, on_event):
        """
        reads self.path_to_save, parses the events.
        The callback is called on every event
        This should be memory-friendly
        :param on_event: 
        :return: 
        """
        print("Parsing file")
        with open(self.path_to_save, 'r') as f:
            current_properties = None
            key = None
            skip_line = False
            total = 0
            while True:
                line = f.readline()
                if line is None or line == "":
                    break
                line = line.rstrip("\n\r")
                if line == "BEGIN:VEVENT":
                    total += 1
                    current_properties = {}
                    continue
                if line == "END:VEVENT":
                    should_continue = on_event(VEvent(current_properties), total)
                    current_properties = None
                    gc.collect()
                    if should_continue:
                        continue
                    else:
                        break
                if current_properties is None:
                    continue
                if skip_line:
                    skip_line = False
                    continue
                if line.startswith("ATTENDEE;"):
                    skip_line = True
                    continue
                if line.startswith(" "):
                    current_properties[key] = current_properties[key] + line[1:]
                    continue
                props = line.split(":")
                key = props[0].split(";")[0]
                current_properties[key] = props[1]


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
    eligible_events = []
    lastclick = 0

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
            datestr_y = display.height() - datestr_h - 4

        if (big_clock):
            display.drawText(12, 0, time_str, font_color, '7x5', 8, 8)
        else:
            display.drawRect(0, 0, 0, datestr_h, True, self.background_color)
            display.drawText(4, 0, time_str, font_color, '7x5', 4, 4)

        date_str_w = display.getTextWidth(date_str, date_font)

        display.drawText(display.width() - date_str_w - 6, datestr_y, date_str, font_color, date_font)

        weekday = WEEKDAYS[datetime[6]]
        weekday_font = date_font
        weekday_w = display.getTextWidth(weekday, weekday_font)
        weekday_h = display.getTextHeight(weekday, weekday_font)
        weekday_y = (datestr_h - weekday_h) + 4
        if big_clock:
            weekday_y = display.height() - weekday_h - 4
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
            cal.update(2 * 60 * 60)
        wifi.disconnect()

    def load_eligble_events(self):
        self.eligible_events.clear()
        for cal in self.calendars:
            for ev in cal.get_eligible_events(utime.time(), utime.time() + 7 * 24 * 60 * 60):
                self.eligible_events.append(ev)
        self.eligible_events.sort(key=lambda e: e.end_time())

    def draw_display(self):
        print("Drawing display, bigclock_mode is "+str(self.bigclock_mode))
        if self.bigclock_mode or len(self.eligible_events) == 0:
            if(len(self.eligible_events)) == 0:
                display.drawText(0, display.height()-12, "No events planned")
            self.draw_time()
            return

        display.drawFill(self.background_color)
        y = self.draw_time(flush=False)
        for event in self.eligible_events[0:3]:
            y = event.draw_on_display(self.format_time, self.font_color,self. background_color, 2, y, flush=False)
        display.flush()

    def draw_page(self):
        items_per_page = 5
        range_start = self.page * items_per_page
        y = 0
        for ev in self.eligible_events[range_start: range_start+items_per_page]:
            y = ev.draw_on_display(self.format_time, self.font_color, self.background_color, 2, y, flush=False)
        display.flush()

    def main(self):

        display.drawFill(WHITE)
        self.log("Connecting to WiFi...")
        wifi.wait()
        if not wifi.status():
            self.log("Wifi not connected, exiting")
            return
        self.log("Wifi connected! Syncing ntp")
        wifi.ntp()
        self.log("Ntp synced!")
        display.drawFill(WHITE)
        self.draw_time()
        config = []
        with open("calendar_config.json", "r") as f:
            config = json.loads(f.read())

        for calconf in config:
            url = calconf["url"]
            name = calconf["name"]
            print("Loading calendar " + url)
            cal = None
            if "password" in calconf:
                cal = Calendar(name, url, calconf["username"], calconf["password"])
            else:
                cal = Calendar(name, url)
            self.calendars.append(cal)
        self.update_calendars()
        self.load_eligble_events()
        self.bigclock_mode = False
        self.draw_display()


        self.quit = False
        
        def recent_click ():
            got_recent = utime.time() - self.lastclick
            self.lastclick = utime.time()
            return got_recent < 2
            

        def set_quit(button):
            self.quit = True

        def swap_mode(v):
            if recent_click():
                return
            self.bigclock_mode = v
            display.drawFill(self.background_color)
            self.draw_display()

        def set_page(diff):
            if recent_click():
                return
            self.page = max(0, self.page + diff)
            self.page = min(self.page, len(self.eligible_events) // 5)
            print("Drawing page "+str(self.page))
            display.drawFill(self.background_color)
            self.draw_page()
            display.flush()

        buttons.attach(buttons.BTN_START, set_quit)
        buttons.attach(buttons.BTN_A, lambda b: swap_mode(True))
        buttons.attach(buttons.BTN_B, lambda b: swap_mode(False))

        buttons.attach(buttons.BTN_LEFT, lambda b: set_page(-1))
        buttons.attach(buttons.BTN_RIGHT, lambda b: set_page(1))

        cycles_since_updated = 0
        current_seconds = utime.localtime()[5]
        dtime = 61 - current_seconds
        # We sleep till one second over the timeswitch - the ideal moment start a minutely loop
        utime.sleep(dtime)
        while not self.quit:
            self.draw_display()
            for i in range(0, 60):
                if self.quit:
                    break
                utime.sleep(1)

            cycles_since_updated += 1
            if cycles_since_updated >= 61:
                self.update_calendars()
                self.load_eligble_events()
                self.draw_display()
                cycles_since_updated = 0


Main().main()
