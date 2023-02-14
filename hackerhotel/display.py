# Stub of the 'display'-module

def drawLine(x, y, x1, y1, color):
    print("Draw line between " + str(x) + "," + str(y) + " " + str(x1) + "," + str(y1) + " in " + str(color))


def flush():
    pass

def getTextWidth(string, font):
    return 42

def drawText(x, y, string, text_color=0x000000, font=None, xscale=1, yscale=1):
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
    """
    Value between 0 and 255
    :param brightness: 
    :return: 
    """
    print("Changed brightness to "+str(brightness))

def get_brightness():
    return 100 