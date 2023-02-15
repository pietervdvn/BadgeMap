import urequests as requests
import utime

epoch = utime.localtime(0)

def localtime():
    """
    Returns a _corrected_ localtime
    Turns out the RTC and utime think differently about the epoch...
    :return: 
    """
    (y, m, d, H, M, S, dow, doy) = utime.localtime()
    y = 1970 + (y - epoch[0])
    return (y, m, d, H, M, S, dow, doy)

def fromRgb(rgb):
    [r, g, b] = rgb
    return (r * 256 + g) * 256 + b

char_replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'é':'e', 'è':'e'}
def str_safe(str):
    return ''.join(char_replacements.get(c, c) for c in str)
    
def downloadToFile(url, filename):
    if url is None:
        raise "downloadToFile cannot work without an URL, it is NONE"
    r = requests.get(url)
    print("Attempting to save to " + filename)
    text = r.text
    r.close()
    print("Received Text is " + str(len(text))+" characters long")
    print("Writing to " + filename)
    with open(filename, "w") as f:
        f.write(text)
        print("Done")