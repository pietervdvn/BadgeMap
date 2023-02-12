import math
import display
from menu import Menu, MenuItem

class PointLayer:

    pointdata = None

    def __init__(self, location, file, fg, bg, minzoom = 17, state = None):
        """
        :type location: Location
        :type state: State
        """
        self.location = location
        self.file = file
        self.fg = fg
        self.bg = bg
        self.minzoom = minzoom
        if file is not None:
            self.name = file[0 : len(file) - len(".points")]
        self.state = state
        location.trigger_once.append(self._load_data)
        location.callbacks.append(self._update)

    def _load_data(self, location):
        if (self.pointdata is not None):
            return
        self.pointdata = list()
        print("Attempting to read " + self.file)
        with open(self.file, "r") as f:
            meta = f.readline()
            while True:
                line = f.readline()
                if not line:
                    break
                if line.strip() == "":
                    continue
                [xstr, ystr, levelstr, label] = line.split(",")
                level = None
                try:
                    level = int(levelstr)
                except:
                    pass
                
                self.pointdata.append([int(xstr), int(ystr), level, label])
                
        print("Loaded "+str(len(self.pointdata))+" features from "+self.file)

    def drawEntry(self, entry):
        [x, y, level, label] = entry
        [x, y] = self.location.map([x, y])
        estimated_size = display.getTextWidth(label) + 4
        rx = int(x - 2 - estimated_size / 2)
        ry = int(y) - 8
        rw = 4 + estimated_size
        rh = 16
        display.drawRect(rx, ry, rw, rh, True, self.bg)
        display.drawText(2 + rx, ry, label, self.fg)

    def _update(self, location):
        l = self.location
        if l.z < self.minzoom:
            return
        [minx, miny] = l.unmap([0,0])
        [maxx, maxy] = l.unmap([display.width(), display.height()])

        for entry in self.pointdata:
            if entry is None:
                continue
            [x, y, level, label] = entry
            if (x < minx or
                    y < miny or
                    y > maxy or
                    x > maxx ):
                continue
            if level is not None and self.state.level != level:
                continue
            self.drawEntry(entry)

        display.flush()

    def update(self):
        self._update(self.location)

    def buildSelect(self, entry):
        [x, y, level, label] = entry
        return MenuItem(label, lambda : self.state.setSelectedElement([x,y, level, label]))
    
    def createSearchIndex(self, fallback):
        state = self.state
        items = list()
        for entry in self.pointdata:
            items.append(self.buildSelect(entry))
        return Menu("Search "+self.name+" by name", items, fallback)
    
class LineLayer:
    linedata = None

    def __init__(self, location, file, color, state):
        """
        :type location: Location
        :type state: State
        :param file: 
        """
        self.location = location
        self.file = file
        self.color = color
        self.state = state
        location.trigger_once.append(self._load_data)
        location.callbacks.append(self._update)

    def parseCoord(self, s):
        [lonStr, latStr] = s.split(",")
        return [int(lonStr), int(latStr)]

    def bbox(self, coords):
        lons = list(map(lambda c: c[0], coords))
        lats = list(map(lambda c: c[1], coords))
        return [min(lons), min(lats), max(lons), max(lats)]

    def _load_data(self, location):
        if (self.linedata is not None):
            return
        self.linedata = list()
        print("Attempting to read " + self.file)
        with open(self.file, "r") as f:
            meta = f.readline()
            while True:
                line = f.readline()
                if not line:
                    break
                endOfCoordinates = line.index(" ")
                coordsStr = line[0:endOfCoordinates]
                coords = list(map(self.parseCoord, coordsStr.split(";")))
                properties = line[endOfCoordinates + 1:].split(",")
                try:
                    properties[0] = int(properties[0])
                except:
                    properties[0] = None
                self.linedata.append([coords, properties, self.bbox(coords)])
        print("Loaded "+str(len(self.linedata))+" features from "+self.file)

    def _update(self, location):
        l = self.location
        [minx, miny] = l.unmap([0,0])
        [maxx, maxy] = l.unmap([display.width(), display.height()])

        for entry in self.linedata:
            [coords, properties, [f_minlon, f_minlat, f_maxlon, f_maxlat]] = entry
            if (f_maxlon < minx or
                    f_maxlat < miny or
                    f_minlat > maxy or
                    f_minlon > maxx ):
                continue
                
            level = properties[0]
            if level is not None and level != self.state.level:
                continue

            for i in range(1, len(coords)):
                [x,y] = l.map(coords[i - 1])
                [x0, y0] = l.map(coords[i])
                display.drawLine(x, y, x0, y0, self.color)


class Location:
    # Lat/lon of the _upper left_corner. Keep in mind that 'lat' is reversed

    x = 1226
    y = 40
    z = 16
    default_zoom = 19

    max_x = 999999999
    max_y = 999999999

    currently_selected = None

    callbacks = []
    trigger_once = []

    def update(self, very_dirty=False):
        self.currently_selected = None
        self.call_callbacks()

    def call_callbacks(self):
        for f in self.trigger_once:
            f(self)
        self.trigger_once.clear()

        for f in self.callbacks:
            # try:
            f(self)
            # except Exception as e:
            #   print("Could not execute a callback of location", str(e))

    def map(self, xy):
        """
        converts an xy of the zoomlevel into an xy on the screen, keeping track of zoom and current offset
        :param xy: 
        :return: 
        """
        [x, y] = xy
        zdiff = self.default_zoom - self.z
        factor = 2 ** zdiff
        x = (x - self.x) / factor
        y = (y - self.y) / factor
        return [x, y]

    def unmap(self, xy):
        [x, y] = xy
        zdiff = self.default_zoom - self.z
        factor = 2 ** zdiff
        x = (x * factor) + self.x
        y = (y * factor) + self.y
        return [x, y]

    def zoom_in(self):
        if (self.z >= 20):
            return
        self.z = self.z + 1
        upperleft = self.unmap([0,0])
        bottomright = self.unmap([display.width(), display.height()])
        dx = bottomright[0] - upperleft[0]
        dy = bottomright[1] - upperleft[1]
        self.y = self.y + (dy / 2)
        self.x = self.x + (dx / 2)
        self.call_callbacks()

    def zoom_out(self):
        if (self.z <= 12):
            return
        upperleft = self.unmap([0,0])
        bottomright = self.unmap([display.width(), display.height()])
        dx = bottomright[0] - upperleft[0]
        dy = bottomright[1] - upperleft[1]
        self.x = self.x - (dx / 2)
        self.y = self.y - (dy / 2)
        self.z = self.z - 1
        self.call_callbacks()

    def move(self, dir, trigger_callback=True):
        if dir == "a":
            self.zoom_in()
            return

        if dir == "b":
            self.zoom_out()
            return

        dy = math.floor(display.height()) / 2
        dx = math.floor(display.width()) / 2
        if dir == "up":
            if self.y >= dy:
                self.y -= dy
        if dir == "down":
            if self.y <= self.max_y:
                self.y += dy
        if dir == "left":
            if self.x >= dx:
                self.x -= dx
        if dir == "right":
            if self.x <= self.max_x:
                self.x += dx

        if trigger_callback:
            self.call_callbacks()
