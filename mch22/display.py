# Stub of the 'display'-module

def drawLine(x, y, x1, y1, color):
    print("Draw line between " + str(x) + "," + str(y) + " " + str(x1) + "," + str(y1) + " in " + str(color))


def flush():
    pass


def drawText(x, y, string, text_color=0x000000):
    print("Drawing text " + string + " at " + str(x) + "," + str(y))


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
