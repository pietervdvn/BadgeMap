import gc
import os
import time
import utils
import display
import utime
import wifi
import mrequests
import ubinascii

WEEKDAYS = {
    1: 'Sun',
    2: 'Mon',
    3: 'Tue',
    4: 'Wed',
    5: 'Thu',
    6: 'Fri',
    7: 'Sat'
}

WEEKDAYS_ICS = {
    0: 'MO',
    1: 'TU',
    2: 'WE',
    3: 'TH',
    4: 'FR',
    5: 'SA',
    6: 'SU'
}

def normalize_date(tpl):
    """
    Makes sure a date is well-formatted and the weekday-indicator is correct
    """
    while tpl[1] <= 0:
        tpl = (tpl[0] - 1, tpl[1] + 12, tpl[2], tpl[3], tpl[4], tpl[5], tpl[6], tpl[7])
    while tpl[1] >= 13:
        tpl = (tpl[0] + 1, tpl[1] - 12, tpl[2], tpl[3], tpl[4], tpl[5], tpl[6], tpl[7])

    if type(tpl) == int or type(tpl) == float:
        return utime.gmtime(int(tpl))
    return utime.gmtime(int(utime.mktime(tpl)))

def add_days(tpl, day_diff):
    time_stamp = int(utime.mktime(tpl))
    return utime.gmtime(time_stamp + 24 * 60 * 60 * day_diff)


def add_year(tpl, year_diff):
    return normalize_date((tpl[0] + year_diff, tpl[1], tpl[2], tpl[3], tpl[4], tpl[5], tpl[6], tpl[7]))

class RepeatedVEvent:
    frequences = {
        "DAILY": 24 * 60 * 60,
        "WEEKLY": 7 * 24 * 60 * 60,
    }

    def __init__(self, properties):
        self.properties = properties

    def generate_events(self, start_date_seconds, end_date_seconds):
        """
        Generates a list of 'normal' events which overlaps between the specified timestamps
        :param start_date_seconds: 
        :param end_date_seconds: 
        :return: 
        """
        parts = self.properties["RRULE"].split(";")
        exception_dates = set()
        if "EXDATE" in self.properties:
            exception_dates = set(map(VEvent.parse_date , self.properties["EXDATE"].split(",")))
        print("Exception dates for "+self.properties["SUMMARY"]+" are " +str(exception_dates))
        rrule_props = {}
        for part in parts:
            [k, v] = part.split("=")
            rrule_props[k] = v

        if "UNTIL" in rrule_props:
            until_date = utime.mktime(VEvent.parse_date(rrule_props["UNTIL"]))
            if until_date < start_date_seconds:
                return []

        interval = 1
        if "INTERVAL" in rrule_props:
            interval = int(rrule_props["INTERVAL"])

        start_date_ev0_tuple = VEvent.parse_date(self.properties["DTSTART"])
        start_date_ev0 = int(utime.mktime(start_date_ev0_tuple))
        end_date_ev0_tuple = VEvent.parse_date(self.properties["DTEND"])
        end_date_ev0 = int(utime.mktime(end_date_ev0_tuple))

        start_date_seconds = int(start_date_seconds)
        end_date_seconds = int(end_date_seconds)
        start_date_tpl = time.gmtime(start_date_seconds)
        end_date_tpl = time.gmtime(end_date_seconds)
        if end_date_ev0 < end_date_seconds:
            print("Not generating events for ",self.properties,"end date falls before expected time")
            return []
        

        freq = rrule_props["FREQ"]

        count = 999999
        if "COUNT" in rrule_props:
            count = int(rrule_props["COUNT"])

        if freq == "MONTHLY":
            c = 0
            events = []
            while True:
                c += 1
                if c > count:
                    break
                # take the start of the next month where this event happens:
                month_start = normalize_date(
                    (start_date_ev0_tuple[0], start_date_ev0_tuple[1] + interval * c, 1, 0, 0, 0,0 ,0))
                # end of the month:VEvent.form take the next month at day 'zero'
                month_end_timestamp = int(utime.mktime(normalize_date(
                    (start_date_ev0_tuple[0], start_date_ev0_tuple[1] + interval * c + 1, 1, 0, 0, 0, 0, 0))))
                month_end = utime.gmtime(month_end_timestamp - 24 * 60 * 60)
                if("BYDAY" not in rrule_props):
                    print("ERROR: rrule_props does not contain a BYDAY-field, skipping")
                    print(rrule_props)
                    print(self.properties)
                    return []
                
                bydays = rrule_props["BYDAY"].split(",")

                if utime.mktime(month_start) > end_date_seconds:
                    print("Not generating more events, "+str(month_start)+" falls after "+str(utime.gmtime(end_date_seconds)))
                    break
                for byday in bydays:
                    week_index = int(byday[0:-2])
                    weekday = byday[-2:]

                    week_start = normalize_date((month_start[0], month_start[1], 1 + 7 * (week_index - 1), 0, 0, 0, 0 ,0))
                    if week_index < 0:
                        week_start = normalize_date(
                            (month_end[0], month_end[1], month_end[2] + 7 * week_index, 0, 0, 0, 0, 0))
                    day = week_start
                    while WEEKDAYS_ICS[day[6] % 7] != weekday:
                        day = normalize_date((day[0], day[1], day[2] + 1, day[3], day[4], day[5], (day[6] + 1) % 7, day[7] + 1))

                    event_start = (
                        day[0], day[1], day[2], start_date_ev0_tuple[3], start_date_ev0_tuple[4], start_date_ev0_tuple[5],
                        day[6], day[7])
                    event_end = (
                        day[0], day[1], day[2], end_date_ev0_tuple[3], end_date_ev0_tuple[4], end_date_ev0_tuple[5], day[6],
                        day[7])
                    if utime.mktime(event_end) < start_date_seconds or end_date_seconds < utime.mktime(event_start):
                        continue
                    # The event is in range - we pass it on
                    properties = dict(self.properties)
                    del properties["RRULE"]
                    properties["DTSTART"] = VEvent.format_date(event_start)
                    properties["DTEND"] = VEvent.format_date(event_end)
                    if properties["DTSTART"] in exception_dates:
                        continue
                    ve = VEvent(properties)
                    events.append(ve)
            return events

        if freq == "YEARLY":
            print("   YRLY:" + str(rrule_props))
            print("   YRLY:" + str(self.properties))
            ev_strt = VEvent.parse_date(self.properties["DTSTART"])
            ev_end = VEvent.parse_date(self.properties["DTEND"])

            c = 0
            found_events = []
            while c < 999:
                start_date_ev_i = add_year(ev_strt, c)
                end_date_ev_i = add_year(ev_end, c)
                c+=1
                if(time.mktime(start_date_ev_i) > end_date_seconds):
                    break
                if time.mktime(end_date_ev_i) < start_date_seconds:
                    continue
                properties = dict(self.properties)
                properties["DTSTART"] = VEvent.format_date(start_date_ev_i)
                properties["DTEND"] = VEvent.format_date(end_date_ev_i)
                if properties["DTSTART"] in exception_dates:
                    continue
                found_events.append(VEvent(properties))
            return found_events



        in_between_time = self.frequences[rrule_props["FREQ"]]

        count = 999999
        if "COUNT" in rrule_props:
            count = int(rrule_props["COUNT"])
            last_date = end_date_ev0 + in_between_time * interval * count
            if last_date < start_date_seconds:
                return []

        until_time = time.gmtime(end_date_seconds)
        if "UNTIL" in rrule_props:
            until_time = VEvent.parse_date(rrule_props["UNTIL"])

        if freq == "WEEKLY":
            found_events = []
            for i in range(0, count):
                end_date_ev_i = add_days(end_date_ev0_tuple, i * 7 * interval)
                if end_date_ev_i < start_date_tpl:
                    continue
                start_date_ev_i = add_days(start_date_ev0_tuple, i * 7 * interval)
                if start_date_ev_i > until_time:
                    break
                properties = dict(self.properties)
                properties["DTSTART"] = VEvent.format_date(start_date_ev_i)
                properties["DTEND"] = VEvent.format_date(end_date_ev_i)
                if properties["DTSTART"] in exception_dates:
                    continue
                found_events.append(VEvent(properties))
            return found_events


        print(rrule_props)
        print(str(self.properties))
        raise Exception("Loading vevent for " + self.properties["RRULE"])


class VEvent:

    def __init__(self, properties):
        self.properties = properties

    @staticmethod
    def format_date(datetime):
        if type(datetime) == int:
            datetime = time.gmtime(datetime)
        return "{0}{1:02}{2:02}T{3:02}{4:02}{5:02}".format(datetime[0], datetime[1], datetime[2], datetime[3],
                                                           datetime[4], datetime[5])
    @staticmethod
    def parse_date(datetime, isEndDate=False):
        try:
            year = int(datetime[0:4])
            month = int(datetime[4:6])
            day = int(datetime[6:8])
            if len(datetime) <= 8 and isEndDate:
                return year, month, day, 23, 59, 59, 0, 0
            if len(datetime) <= 8:
                return year, month, day, 0, 0, 0, 0, 0
            hour = int(datetime[9:11])
            min = int(datetime[11:13])
            sec = int(datetime[13:15])
            tpl = (year, month, day, hour, min, sec, 0, 0)
            return utime.gmtime(int(utime.mktime(tpl)))
        except Exception as e:
            print("Could not parse "+datetime+" due to "+str(e) )

    def whole_day(self):
        if "DTSTART" not in self.properties:
            return True
        return not (self.properties["DTSTART"].find("T") > 0 and self.properties["DTEND"].find("T") > 0)

    def start_time(self):
        """Returns a six-tuple with the start-time"""
        key = "DTSTART"
        if key not in self.properties:
            if "DTEND" not in self.properties:
                return None
            key = "DTEND"
        return VEvent.parse_date(self.properties[key])

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
        if self_end_time is None or start >= self_end_time:
            return False
        if end is None:
            return True
        self_start_time = self.start_time()
        if self_start_time is None:
            return False
        return self_start_time < end

    def summary(self):
        l = ""
        if "LOCATION" in self.properties:
            l = " location: " + self.properties["LOCATION"]
        if "SUMMARY" in self.properties:
            l = self.properties["SUMMARY"]
        return l

    def draw_on_display(self, format_time, format_date, fgcolor, bgcolor, x=0, y=0, flush=True):
        strt_tuple = normalize_date(self.start_time())

        today = utime.localtime()
        midnight = utime.mktime((today[0], today[1], today[2], 0, 0, 0, 0, 0))
        coming_midnight = utime.localtime(int(midnight) + 24 * 60 * 60)
        strt = format_time(strt_tuple)
        if self.whole_day():
            strt = format_date(strt_tuple)
            end = format_date(normalize_date( self.end_time()))
            print("Multiday, strt tupl:" + str(strt_tuple)+" end: " + end)
            
            if strt == end:
                display.drawText(x, y, WEEKDAYS[strt_tuple[6]])
                display.drawText(x, y + display.getTextHeight(strt) + 1, strt)
            else:
                display.drawText(x, y, strt)
                display.drawText(x, y + display.getTextHeight(strt) + 1, end)
            x += display.getTextWidth("00:00") + 5
        elif coming_midnight < self.start_time():
            # Not today - we show a day of week instead + starting hour
            display.drawText(x, y, WEEKDAYS[strt_tuple[6]])
            display.drawText(x, y + display.getTextHeight(strt) + 1, strt)
            x += display.getTextWidth("00:00") + 5
            pass
        else:
            display.drawText(x, y, strt)
            end = format_time(self.end_time())
            display.drawText(x, y + display.getTextHeight(strt) + 1, end)
            x += display.getTextWidth("00:00") + 5

        summary_font = "roboto_black22"
        if "LOCATION" in self.properties:
            loc = utils.str_safe(self.properties["LOCATION"])
            loc_w = display.getTextWidth(loc)
            display.drawText(display.width() - loc_w, y + 8, loc, fgcolor)
        display.drawText(x, y + 2, utils.str_safe(self.properties["SUMMARY"]), fgcolor, summary_font)
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
        headers = dict()
        if self.password is not None:
            headers["Authorization"] = "Basic " + ubinascii.b2a_base64(self.username + ":" + self.password).decode(
                "UTF8")

        print("Attempting to save to " + self.path_to_save, self.url, headers)
        r = mrequests.get(self.url, headers=headers)
        r.save(self.path_to_save + ".temp")
        print("Got a response, written to " + self.path_to_save)

        linecount = 0
        with open(self.path_to_save + ".temp", 'r') as f:
            # we copy the 'temp'-file line by line, but only if the events are still going on or in the future
            with open(self.path_to_save, 'w') as target:
                lines = []
                should_save = False
                include_multilines = False
                copied = 0
                while True:
                    if linecount % 1000 == 0:
                        print("Skipping/copying lines, currently handled " + str(linecount) + " and found " + str(
                            copied) + " events")
                        msg = "Updating "+self.name+": parsed "+str(linecount // 1000) + "K lines"
                        display.drawRect(0, display.height() - 12, display.getTextWidth(msg), 12, True, 0xffffff)
                        display.drawText(0, display.height() - 12, msg)
                        display.flush()
                        gc.collect()
                    line = f.readline(500)
                    linecount += 1
                    if line is None or line == "":
                        msg = "Updating "+self.name+": parsed full file"
                        display.drawRect(0, display.height() - 12, display.getTextWidth(msg), 12, True, 0xffffff)
                        display.drawText(0, display.height() - 12, msg)
                        display.flush()
                        break
                    if line.startswith(" "):
                        if not include_multilines:
                            # Multiline stuff is always to long to handle
                            continue
                    else:
                        include_multilines = False
                    line = line.rstrip("\n\r")
                    if line == "":
                        continue

                    lines.append(line)
                    if line.startswith("RRULE"):
                        should_save = True
                        continue
                    if line.startswith("EXDATE"):
                        # exception dates: dates not conforming the normal schedule
                        # we save it, including multilines
                        include_multilines = True
                        continue
                    if line.startswith("DTEND"):
                        [_, date] = line.split(":")
                        d = VEvent.parse_date(date)
                        current_date = utime.gmtime()
                        if d >= current_date:
                            should_save = True
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
                            target.flush()
            # os.rmdir(self.path_to_save + ".temp")
            print("Seen "+str(linecount)+" lines in "+self.path_to_save+".temp")
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

        self.parse_ics_from_file(on_event, utime.mktime(start), utime.mktime(end))

        return matching_events

    __current_draw_y = 0

    def get_eligible_events(self, start_date_sec, end_date_sec):
        # events are _not_ sorted, we first create a list
        eligible_events = []
        print("Start date:" + str(start_date_sec))

        def handle(event, index):
            """
            :type event: VEvent
            :type index: int
            """
            print("Handling event " + str(index) +" "+ event.summary()+" "+str(event.start_time()))
            if event.properties is None:
                return True
            if event.activeDuring(utime.gmtime(int(start_date_sec)), utime.gmtime(int(end_date_sec))):
                # Yeah, this is ugly... But well, python doesn't properly support closures...
                eligible_events.append(event)
            return True

        self.parse_ics_from_file(handle, start_date_sec, end_date_sec)
        print("Got " + str(len(eligible_events)) + " eligble events!")
        return eligible_events

    def parse_ics_from_file(self, on_event, start_timestamp, end_timestamp):
        """
        reads self.path_to_save, parses the events.
        The callback is called on every event
        This should be memory-friendly
        :param on_event: 
        :return: 
        """
        print("Parsing file")
        start_timestamp = int(start_timestamp)
        end_timestamp = int(end_timestamp)
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
                    print("Handling event "+str(total))
                    if "RRULE" in current_properties:
                        r_vevent = RepeatedVEvent(current_properties)
                        for ev in r_vevent.generate_events(start_timestamp, end_timestamp):
                            on_event(ev, total)
                    else:
                        vevent = VEvent(current_properties)
                        if not vevent.activeDuring(utime.gmtime(start_timestamp), utime.gmtime(end_timestamp)):
                            continue
                        should_continue = on_event(vevent, total)
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

