# Stub of the 'display'-module

def drawLine(x, y, x1, y1, color):
    print("Draw line between " + str(x) + "," + str(y) + " " + str(x1) + "," + str(y1) + " in " + str(color))


def flush():
    pass

def getTextWidth(string, font = None):
    return 42

def drawFill(color):
    pass


def drawText(x: int, y: int, string: str, text_color: int = 0x000000, font: str = None, scaling_x: int = 0,
             scaling_y: int = 0):
    print("Drawing text " + string + " at " + str(x) + "," + str(y) + " in " + font)



def drawRect(x, y, width, height, is_filled, color):
    print("Drawing a rectangle")


def width():
    return 320


def height():
    return 240



def getTextHeight(chunk, font=None):
    return 12


def listFonts():
    """
    Works on MCH22
    Not supported on SHA17
    
    List of fonts are the fonts as reported by MCH22
    :return: 
    """
    return ('org18', 'org01_8', 'fairlight8', 'fairlight12', 'dejavusans20', 'permanentmarker22', 'permanentmarker36', 'roboto_black22', 'roboto_blackitalic24', 'roboto_regular12', 'roboto_regular18', 'roboto_regular22', 'weather42', 'pixelade13', '7x5', 'ocra16', 'ocra22', 'exo2_regular22', 'exo2_thin22', 'exo2_bold22', 'exo2_regular18', 'exo2_thin18', 'exo2_bold18', 'exo2_regular12', 'exo2_thin12', 'exo2_bold12', 'press_start_2p6', 'press_start_2p8', 'press_start_2p9', 'press_start_2p12', 'press_start_2p18', 'press_start_2p22')



def brightness(brightness):
    """
    Value between 0 and 255
    :param brightness: 
    :return: 
    """
    print("Changed brightness to "+str(brightness))

def get_brightness():
    return 100 