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
    1: 'Sunday',
    2: 'Monday',
    3: 'Tuesday',
    4: 'Wednesday',
    5: 'Thursday',
    6: 'Friday',
    7: 'Saturday'
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

    def start_time(self):
        for k in self.properties.keys():
            if k.startswith("DTSTART"):
                return self.parse_date(self.properties[k])
        print("Could not determine start-time for" + str(self.properties))

    def end_time(self):
        for k in self.properties.keys():
            if k.startswith("DTEND"):
                datetime = self.properties[k]
                return self.parse_date(datetime)
        print("Could not determine end-time for " + str(self.properties))

    def activeDuring(self, start, end):
        return start < self.start_time() and self.end_time() < end

    def summary(self):
        print(self.properties)
        l = ""
        if "LOCATION" in self.properties:
            l = " location: " + self.properties["LOCATION"]
        return self.properties["SUMMARY"] + l


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

    def active_next(self, start, end, max_count = 9999999):
        """
        Returns a list of all VEVENTs that are active between 'start' and 'end'
        :param ical_text: 
        :param start: (y, m, d, h, m, s)
        :param end: (y, m, d, h, m, s)
        :return: list of dicts
        """
        print("Determining active events between " + str(start) + " and " + str(end))
        matching_events = []

        def on_event(event: VEvent):
            if event.activeDuring(start, end):
                matching_events.append(event)
                if len(matching_events) > max_count:
                    raise StopIteration()
        try:
            self.parse_ics_from_file(on_event)
        except StopIteration:
            pass
        
        return matching_events

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
        for line in f.readlines():
            line = line.rstrip("\n\r")
            if line == "BEGIN:VEVENT":
                current_properties = {}
                continue
            if line == "END:VEVENT":
                on_event(VEvent(current_properties))
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
            key = props[0]
            current_properties[key] = props[1]


class Output:
    """Manages all formatting, display."""

    def __init__(self):
        self._old_date_str = ''
        self._old_time_str = ''

    def draw(self, datetime):
        """Draw the date & time.

        Clear the screen to prevent ghosting:
            - When the date changes.
            - When entering an alert.
            - When leaving an alert.
        """
        time_str = self._format_time(datetime)
        date_str = self._format_date(datetime)

        if time_str == self._old_time_str:
            return

        if date_str != self._old_date_str:
            # we've come out of an alert or the date changed,
            # so clear the screen to prevent ghosting.
            display.drawFill(BLACK)
            display.flush()

        self._old_date_str = date_str
        self._old_time_str = time_str

        display.drawFill(WHITE)
        display.drawText(0, 0, time_str, BLACK, FONTS['7x5'], 5, 5)

        bottom = display.height() - 2  # the bottom pixel seems to clip.
        date_y = bottom - (display.getTextHeight(date_str, FONTS['7x5']) * 3)
        display.drawText(0, date_y, date_str, BLACK, FONTS['7x5'], 3, 3)
        display.flush()

    def _format_time(self, datetime):
        hours = datetime[3]
        minutes = datetime[4]
        return '%02d:%02d' % (hours, minutes)

    def _format_date(self, datetime):
        weekday = datetime[6]
        return WEEKDAYS[weekday]



def main():
    easydraw.msg('setting up WiFi...')
    if not init_wifi():
        easydraw.msg('could not set up WiFi')
        return

    easydraw.msg('setting up RTC...')
    clock = Clock()
    output = Output()
    while True:
        output.draw(clock.get())
        utime.sleep(1)



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

c.active_next((2022, 7, 1, 0, 0, 0), (2022, 8, 1, 0, 0, 0))
