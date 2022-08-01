"""Displays the time and also alerts."""

# pylint: disable=bare-except
# pylint: disable=import-error
# pylint: disable=no-self-use
# pylint: disable=too-few-public-methods

import display
import easydraw
import machine
import utime
import wifi
import urequests as requests
import ubinascii

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


class Clock:
    """Manages the Real Time Clock and NTP."""

    def __init__(self, default_timezone=EUROPE_LONDON):
        if utime.time() < 1585235437:
            # RTC is unset.
            wifi.ntp()

        self._rtc = machine.RTC()
        timezone = default_timezone
        try:
            timezone = machine.nvs_getstr('system', 'timezone')
        except AttributeError:
            easydraw.msg("Could not read timezone")
        if not timezone:
            timezone = default_timezone
        try:
            self._rtc.timezone(timezone)
        except AttributeError:
            easydraw.msg("Could not set timezone")

    def get(self):
        """Returns a datetime tuple of (y, m, d, h, m, s, wd, yd)."""
        try:
            return self._rtc.now()
        except AttributeError:
            (y, m, d, wd, h, m, s, subs) = self._rtc.datetime()
            return y, m, d, h, m, s, wd


class VEvent:

    def __init__(self, properties):
        self.properties = properties

    def parse_date(self, datetime, isEndDate=False):
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
        return year, month, day, hour, min, sec

    def whole_day(self):
        return not (self.properties["DTSTART"].find("T") > 0 and self.properties["DTEND"].find("T") > 0)

    def start_time(self):
        """Returns a six-tuple with the start-time"""
        if "DTSTART" not in self.properties:
            return None
        return self.parse_date(self.properties["DTSTART"])

    def end_time(self):
        if "DTEND" not in self.properties:
            return None
        datetime = self.properties["DTEND"]
        return self.parse_date(datetime)

    def activeDuring(self, start, end):
        """
        Indicates if the event _overlaps_ with the given time, i.e. the specified start-time falls before the end-time of the event
        and vice versa.
        :param start: 
        :param end: 
        :return: 
        """
        return start < self.end_time() and self.start_time() < end

    def summary(self):
        l = ""
        if "LOCATION" in self.properties:
            l = " location: " + self.properties["LOCATION"]
        return self.properties["SUMMARY"] + l

    def draw_on_display(self, x=0, y=0):
        strt = format_time(self.start_time())
        if self.whole_day():
            x += display.getTextWidth("00:00") + 5
        else:
            display.drawText(x, y, strt)
            end = format_time(self.end_time())
            display.drawText(x, y + display.getTextHeight(strt) + 1, end)
            x += display.getTextWidth(strt) + 5

        location_font = "exo2_thin22"
        summary_font = "roboto_black22"
        if "LOCATION" in self.properties:
            loc = self.properties["LOCATION"]
            loc_w = display.getTextWidth(loc, location_font)
            display.drawText(display.width() - loc_w, y, loc, 0xcccccc, location_font)
        display.drawText(x, y, self.properties["SUMMARY"], 0xffffff, summary_font)
        line_y = y + 6 + display.getTextHeight("Abcdef", summary_font)
        display.drawLine(x, line_y, display.width() - 5, line_y, 0x888888)
        display.flush()
        return y + 6 + display.getTextHeight("Abcdef", summary_font)


class Calendar:
    def __init__(self, clock, path_to_save, password=None,
                 url="https://caldav.sphinxpinastri.duckdns.org/pietervdvn/4e2a22bf-a05f-3325-1c3e-67b7dff894cd",
                 username="pietervdvn"):
        self.clock = clock
        self.path_to_save = path_to_save
        self.password = password
        self.username = username
        self.url = url

    def update(self, allowed_difference=None):
        """
        Updates and saves to file
        :return: 
        """
        if allowed_difference is not None:
            try:
                fmeta = open(self.path_to_save + ".meta", "r")
                metainfo = fmeta.read()[1:-1].split(",")
                print("metainfo is " + str(metainfo))
                modification_time = tuple(map(int, metainfo))
                latest_allowed_time = sum_date(modification_time, allowed_difference)
                if latest_allowed_time > self.clock.get():
                    print("No need to update this calendar; still fresh enough")
                    easydraw.msg("No need to update this calendar; still fresh enough")
                    return
            except Exception as e:
                print("File does not exist or cannot be read")
        if not wifi.status():
            print("Connecting to wifi...")
            easydraw.msg("Connecting to wifi...")
            wifi.connect()
            wifi.wait()
            easydraw.msg("Connected!")
            print("Connected!")
        headers = {"Authorization": None}
        if self.password is not None:
            headers["Authorization"] = "Basic " + ubinascii.b2a_base64(self.username + ":" + self.password).decode(
                "UTF8")
        r = requests.request("GET", self.url, None, None, headers)
        print("Attempting to save to " + self.path_to_save)
        f = open(self.path_to_save, "w")
        f.write(r.text)
        r.close()
        f.close()
        print("Got a response, written to " + self.path_to_save)
        modification_time = self.clock.get()[0:6]
        fmeta = open(self.path_to_save + ".meta", "w")
        fmeta.write(str(modification_time))
        fmeta.close()

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
                if len(matching_events) > max_count:
                    raise StopIteration()

        try:
            self.parse_ics_from_file(on_event)
        except StopIteration:
            pass

        return matching_events

    __current_draw_y = 0

    def draw_events_from_file(self, start_date, end_date, x=0, y=0):
        display.drawText(0, display.height() - 7, "Parsing calendar...", 0x888888, "7x5")
        display.flush()
        self.__current_draw_y = y

        def handle(event: VEvent, index: int):
            if index % 20 == 0:
                xmsg = display.width() - display.getTextWidth(str(index), "7x5")
                ymsg = display.height() - 7
                display.drawRect(xmsg, ymsg, display.width(), display.height(), True, 0)
                display.drawText(xmsg, ymsg, str(index), 0x888888, "7x5")
                display.flush()
                pass
            if event.activeDuring(start_date, end_date):
                # Yeah, this is ugly... BUt well, python doesn't properly support closurs...
                self.__current_draw_y = self.__current_draw_y + event.draw_on_display(x, self.__current_draw_y)

        self.parse_ics_from_file(handle)
        display.drawRect(0, display.height() - 7, display.width(), display.height(), True, 0)

    def parse_ics_from_file(self, on_event):
        """
        reads self.path_to_save, parses the events.
        The callback is called on every event
        This should be memory-friendly
        :param on_event: 
        :return: 
        """
        print("Parsing file")
        f = open(self.path_to_save, 'r')
        current_properties = None
        key = None
        skip_line = False
        total = 0
        try:
            for line in f.readlines():
                line = line.rstrip("\n\r")
                if line == "BEGIN:VEVENT":
                    total += 1
                    current_properties = {}
                    continue
                if line == "END:VEVENT":
                    on_event(VEvent(current_properties), total)
                    current_properties = None
                    continue
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
        except Exception as e:
            f.close()
            raise e


def format_time(datetime):
    hours = datetime[3]
    minutes = datetime[4]
    return '%02d:%02d' % (hours, minutes)


def _format_date(datetime):
    return str(datetime[2]) + "/" + str(datetime[1])


def draw_time(datetime, font_color=0xffffff):
    """Draw the date & time.
    Returns the first free Y-height

    Clear the screen to prevent ghosting:
        - When the date changes.
        - When entering an alert.
        - When leaving an alert.
    """
    time_str = format_time(datetime)
    display.drawText(0, 0, time_str, font_color, '7x5', 4, 4)
    date_str = _format_date(datetime)
    date_font = "permanentmarker22"
    date_str_w = display.getTextWidth(date_str, date_font)
    datestr_h = display.getTextHeight(date_str, date_font)
    display.drawText(display.width() - date_str_w - 5, 4, date_str, font_color, date_font)

    weekday = WEEKDAYS[datetime[6]]
    weekday_font = date_font
    weekday_w = display.getTextWidth(weekday, weekday_font)
    weekday_h = display.getTextHeight(weekday, weekday_font)
    display.drawText(display.width() - date_str_w - weekday_w - 9, (datestr_h - weekday_h) + 4, weekday, font_color,
                     weekday_font)

    line_y = datestr_h + 11
    display.drawLine(0, line_y, display.width(), line_y, 0x888888)
    display.drawLine(0, line_y + 1, display.width(), line_y + 1, 0xffffff)
    display.drawLine(0, line_y + 2, display.width(), line_y + 2, 0x888888)

    display.flush()
    return line_y + 3
