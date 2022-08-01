import display
import utime
from CalendarDisplay import VEvent

def test_fonts():
    fonts = display.listFonts()
    for i in range(len(fonts)):
        f = fonts[i]
        display.drawFill(0)
        display.drawText(0, 0, f, 0xffffff, f)
        display.drawText(0, 50, f, 0xffffff, f, 2, 2)
        display.drawText(0, 100, f, 0xffffff, f, 3, 3)
        display.drawText(0, 150, f, 0xffffff, f, 4, 4)

        display.drawText(0, 200, f, 0xff00ff)
        display.flush()
        utime.sleep(1)


def test_weather42():
    x = 0
    y = 0
    i = 0
    fnt = 'weather42'
    display.drawFill(0)
    while i < 255:
        print("Drawing " + str(i))
        c = chr(i)
        w = display.getTextWidth(c, fnt) + 10
        h = display.getTextHeight(c, fnt) + 10
        x += w
        if x + w > display.width():
            x = 0
            y += h
        if y + h > display.height():
            display.flush()
            utime.sleep(5)
            x = 0
            y = 0
            display.drawFill(0)
            print("Sleeping!")
        try:
            display.drawText(x, y, str(i), 0xff0000)
            display.drawText(x, y, c, 0xffffff, fnt)
        except Exception:
            print("Exception for "+str(i))
        i += 1
    display.flush()

def dummy_event():
    p = {
        "SUMMARY": "Party",
        "LOCATION": "Elf-julistraat 9",
        "DTSTART": "20221107T190000",
        "DTEND": "20221107T220000"
    }
    return VEvent(p)

def dummy_day_event():
    p = {
        "SUMMARY": "Whole day stuff",
        "DTSTART": "20221107",
        "DTEND": "20221107"
    }
    return VEvent(p)

