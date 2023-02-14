import math

import display
from menu import Menu, MenuItem


class RangedLayer:

    def __init__(self, range):
        """
        :param range: [minx, miny, maxx, maxy]: bbox of the file
        """
        self.range = range

    def partially_in_view(self, location):
        """
        :type location: Location
        :param location: 
        :return: 
        """
        l = location
        [minx, miny] = l.unmap([0, 0])
        [maxx, maxy] = l.unmap([display.width(), display.height()])

        [layer_minx, layer_miny, layer_maxx, layer_maxy] = self.range
        if (layer_maxx < minx or
                layer_maxy < miny or
                layer_miny > maxy or
                layer_minx > maxx):
            return False
        return True

def draw_loading(text):
    display.drawRect(0,0, display.width(), 16, True, 0x880000)
    display.drawText(1,1, text)
    display.flush() 

class PointLayer(RangedLayer):
    pointdata = None

    def __init__(self, location, file, range, fg, bg, minzoom=17, state=None):
        """
        :type location: Location
        :type state: State
        :type minzoom: int
        :type fg: int
        :type bg: int
        :type range: [int, int, int, int]
        :type file: string
        """
        super().__init__(range)
        self.location = location
        self.file = file
        self.fg = fg
        self.bg = bg
        self.minzoom = int(minzoom)
        if file is not None:
            self.name = file[0: len(file) - len(".points")]
        self.state = state
        location.callbacks.append(self._update)

    def _load_data(self, location):
        if (self.pointdata is not None):
            return
        self.pointdata = list()
        print("Attempting to read " + self.file)

        with open(self.file, "r") as f:
            meta = f.readline().split(",")
            total = int(meta[1])
            loaded = 0
            draw_loading("LOADING "+self.file)
            while True:
                line = f.readline()
                loaded += 1
                if not line:
                    break
                if line.strip() == "":
                    continue
                if loaded % 10 == 0:
                    draw_loading("LOADING "+self.file+" "+str(loaded)+"/"+str(total))
                [xstr, ystr, levelstr, label] = line.split(",")
                level = None
                try:
                    level = int(levelstr)
                except:
                    pass

                if label == "":
                    continue

                self.pointdata.append([int(xstr), int(ystr), level, label])

        print("Loaded " + str(len(self.pointdata)) + " features from " + self.file)

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

        if not self.partially_in_view(location):
            return

        if self.pointdata is None:
            self._load_data(location)

        [minx, miny] = l.unmap([0, 0])
        [maxx, maxy] = l.unmap([display.width(), display.height()])

        for entry in self.pointdata:
            if entry is None:
                continue
            [x, y, level, label] = entry
            if (x < minx or
                    y < miny or
                    y > maxy or
                    x > maxx):
                continue
            if level is not None and self.state.level != level:
                continue
            self.drawEntry(entry)

        display.flush()

    def update(self):
        self._update(self.location)

    def buildSelect(self, entry):
        [x, y, level, label] = entry
        return MenuItem(label, lambda: self.state.setSelectedElement([x, y, level, label]))

    def createSearchIndex(self, fallback):
        state = self.state
        items = list()
        for entry in self.pointdata:
            items.append(self.buildSelect(entry))
        return Menu("Search " + self.name + " by name", items, fallback)


class LineLayer(RangedLayer):
    linedata = None

    def __init__(self, location, file, range, color, minzoom, state):
        """
        :type location: Location
        :type state: State
        :param file: location of the file to load
        :param color: color to draw the lines with
        :param state: state for e.g. selected element
        :param range: [minx, miny, maxx, maxy]: bbox of the file
        
        """
        super().__init__(range)
        print("Loaded line layer " + file + " with range " + str(range))
        self.location = location
        self.file = file
        self.color = color
        self.state = state
        self.minzoom = minzoom
        location.callbacks.append(self._update)

    def parseCoord(self, s):
        [lonStr, latStr] = s.split(",")
        return [int(lonStr), int(latStr)]

    def bbox(self, coords):
        lons = list(map(lambda c: c[0], coords))
        lats = list(map(lambda c: c[1], coords))
        return [min(lons), min(lats), max(lons), max(lats)]

    def _load_data(self, location):
        if self.linedata is not None:
            return
        self.linedata = list()
        print("Attempting to read " + self.file+" (minzoom needed: "+str(self.minzoom)+", current zoom: "+str(self.location.z)+")")
        with open(self.file, "r") as f:
            meta = f.readline().split(",")
            loaded = 0
            total = int(meta[1])
            draw_loading("LOADING "+self.file)
            while True:
                line = f.readline()
                loaded += 1
                if not line:
                    break
                if loaded % 10 == 0:
                    draw_loading("LOADING "+self.file+" "+str(loaded)+"/"+str(total))
                endOfCoordinates = line.index(" ")
                coordsStr = line[0:endOfCoordinates]
                coords = list(map(self.parseCoord, coordsStr.split(";")))
                properties = line[endOfCoordinates + 1:].split(",")
                try:
                    properties[0] = int(properties[0])
                except:
                    properties[0] = None
                self.linedata.append([coords, properties, self.bbox(coords)])
            draw_loading("     Done!")
        print("Loaded " + str(len(self.linedata)) + " features from " + self.file)

    def _update(self, location):
        l = self.location

        if l.z < self.minzoom:
            return

        [minx, miny] = l.unmap([0, 0])
        [maxx, maxy] = l.unmap([display.width(), display.height()])

        if not self.partially_in_view(location):
            return

        self._load_data(location)

        for entry in self.linedata:
            [coords, properties, [f_minlon, f_minlat, f_maxlon, f_maxlat]] = entry
            if (f_maxlon < minx or
                    f_maxlat < miny or
                    f_minlat > maxy or
                    f_minlon > maxx):
                continue

            level = properties[0]
            if level is not None and level != self.state.level:
                # continue
                pass
            for i in range(1, len(coords)):
                [x, y] = l.map(coords[i - 1])
                [x0, y0] = l.map(coords[i])
                display.drawLine(x, y, x0, y0, self.color)


class Location:
    # Lat/lon of the _upper left_corner. Keep in mind that 'lat' is reversed

    x = 1226
    y = 40
    z = 18
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
        converts an xy of the zoomlevel the data is defined at into an xy on the screen, keeping track of current zoom and current offset
        :param xy: 
        :return: 
        """
        [x, y] = xy
        zdiff = self.default_zoom - self.z
        factor = 2 ** (zdiff - 1)
        x = (x - self.x) / factor
        y = (y - self.y) / factor
        return [x, y]

    def unmap(self, xy, z=None):
        """
        Converts an x,y-location on the screen (for the current zoom level) into an x,y-location that the data is defined at.
        Allows to override the current zoom level
        :param xy: 
        :return: 
        """
        [x, y] = xy
        zdiff = self.default_zoom - (z if z is not None else self.z)
        factor = 2 ** (zdiff - 1)
        x = (x * factor) + self.x
        y = (y * factor) + self.y
        return [x, y]

    def zoom_in(self):
        if (self.z >= 20):
            return
        self.z = self.z + 1
        upperleft = self.unmap([0, 0])
        bottomright = self.unmap([display.width(), display.height()])
        dx = bottomright[0] - upperleft[0]
        dy = bottomright[1] - upperleft[1]
        self.y = self.y + (dy / 2)
        self.x = self.x + (dx / 2)
        self.call_callbacks()

    def zoom_out(self):
        if (self.z <= 12):
            return
        upperleft = self.unmap([0, 0])
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

        factor = (2 ** (self.default_zoom - self.z - 1))
        dy = math.floor(factor * display.height() / 4)
        dx = math.floor(factor * display.width() / 4)
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
