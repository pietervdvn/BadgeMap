def drawLine(x, y, x1, y1, color):
    print("Draw line between " + str(x) + "," + str(y) + " " + str(x1) + "," + str(y1) + " in " + str(color))


def flush():
    pass


def drawText(x: int, y: int, string: str, text_color: int = 0x000000, font: str = None, scaling_x: int = 0,
             scaling_y: int = 0):
    print("Drawing text " + string + " at " + str(x) + "," + str(y) + " in " + font)


def drawFill(color):
    pass


def drawRect(x, y, width, height, is_filled, color):
    print("Drawing a rectangle")


def width():
    return 320


def height():
    return 240


def brightness(brightness):
    print("Changed brightness")


def getTextWidth(joined, font=None):
    return 42


def getTextHeight(chunk, font=None):
    return 12


def listFonts():
    return ["permanentmarker22", "7x5"]
