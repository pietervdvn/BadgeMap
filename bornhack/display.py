"""
Reimplements 'display' on the bornhack-badge
"""

import board
import terminalio
import displayio
import pwmio
from adafruit_display_text import label
from adafruit_st7735r import ST7735R

# Release any resources currently in use for the displays
displayio.release_displays()

spi = board.SPI()
tft_cs = board.CS
tft_dc = board.D1

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=board.D0
)

display = ST7735R(display_bus, width=128, height=160, rotation=0, bgr=True, colstart=2, rowstart=1)

# bl = digitalio.DigitalInOut(board.PWM0)
# bl.direction = digitalio.Direction.OUTPUT
# bl.value = True

bl = pwmio.PWMOut(board.PWM0, frequency=5000, duty_cycle=0)
bl.duty_cycle = 60000

# Make the display context
splash = displayio.Group()
can_be_cleaned = {"state": False}
display.show(splash)


def width():
    return 128


def height():
    return 160


def drawFill(colour):
    drawRect(0,0,width(),height(), True, colour)

def getTextHeight(text, font = "terminalio"):
    return 8

def getTextWidth(text, font = "terminalio"):
    return len(text) * 5

def drawRect(x, y, w, h, isFilled, colour):
    # Draw a smaller inner rectangle
    _clear_splash()
    inner_bitmap = displayio.Bitmap(w, h, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = colour
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=x, y=y)
    splash.append(inner_sprite)


def drawText(x, y, text, colour = 0xffffff, font="terminalio", scale_x = 1, scale_y = 1):
    # Draw a label
    _clear_splash()
    text_group = displayio.Group(scale=scale_x, x=x, y=y+(4*scale_x))
    text_area = label.Label(terminalio.FONT, text=text, color=colour)
    text_group.append(text_area)  # Subgroup for text scaling
    splash.append(text_group)

def listFonts():
    return ["terminalio"]

def _clear_splash():
    if not can_be_cleaned["state"]:
        return
    while len(splash) > 0:
        del splash[0]
    can_be_cleaned["state"] = False

def flush():
    """In other programs, this asks the buffer to be drawn to the screen. Not here: here we indicate that the next draw is allowed to GC"""
    can_be_cleaned["state"] = True
