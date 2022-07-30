def drawLine(x, y, x1, y1, color):
    print("Draw line between " + str(x) + "," + str(y) + " " + str(x1) + "," + str(y1) + " in " + str(color))


def flush():
    pass


def drawText(x, y, string, text_color=0x000000, font=None, w=0, h=0):
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
