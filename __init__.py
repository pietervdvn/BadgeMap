import math
import os
import mch22
import display
import buttons
import json

version = "0.0.25 (for MCH)"
print("Starting BadgeMap " + version)


def draw_banner(h, text, background_colour=0x000000, text_colour=0xffffff):
    display.drawRect(0, h, 320, 20, True, background_colour)
    display.drawText(10, h+2, text, text_colour)
    display.flush()


class MenuItem:

    def __init__(self, title, on_selected):
        self.on_selected = on_selected
        self.title = title


class Menu:

    selected = 0

    def __init__(self, title, menuitems):
        """

        :type title: string
        """
        self.menuitems = menuitems
        self.title = title

    def update(self):
        draw_banner(0, self.title, 0xffffff, 0x000000)
        for i in range(len(self.menuitems)):
            item = self.menuitems[i]
            draw_banner(25 + i * 20, item.title)
        display.drawRect(2, 32 + self.selected * 20, 6, 6, True, 0xffffff)
        display.flush()
        
    def move(self, direction):
        if direction == "a":
            self.menuitems[self.selected].on_selected()
            return
        
        if direction == "up":
            self.selected = self.selected - 1
            if self.selected < 0:
                self.selected = len(self.menuitems) - 1
        if direction == "down":
            self.selected = (self.selected + 1) % len(self.menuitems)
        self.update()


class Style:
    line = 0xaa0000

    def __init__(self, linecolor=0xaa0000):
        self.line = linecolor


class Label:
    lat = 0
    lon = 0
    label = ""
    minzoom = 16

    def __init__(self, lon, lat, label):
        self.label = label
        self.lat = lat
        self.lon = lon


class Location:
    # Lat/lon of the _upper left_corner. Keep in mind that 'lat' is reversed

    lat = 52.2839
    lon = 5.5254
    z = 15

    callbacks = []

    def update(self):
        self.call_callbacks()

    def call_callbacks(self):
        for f in self.callbacks:
            try:
                f(self)
            except Exception as e:
                print("Could not execute a callback of location", str(e))

    def zoom_in(self):
        self.z = self.z + 1
        factor = math.exp(self.z - 3)
        self.lon = self.lon + (320 / factor)
        self.lat = self.lat - (240 / factor)
        self.call_callbacks()
        print("Zoom in: new location: " + str(self.lat) + "," + str(self.lon))

    def zoom_out(self):
        factor = math.exp(self.z - 3)
        self.lon = self.lon - (320 / factor)
        self.lat = self.lat + (240 / factor)
        self.z = self.z - 1
        self.call_callbacks()

    def move(self, dir, trigger_callback=True):
        if dir is "a":
            self.zoom_in()
            return

        if dir is "b":
            self.zoom_out()
            return

        amount = 1 / math.exp(self.z - 7)
        if dir == "up":
            self.lat += amount
        if dir == "down":
            self.lat -= amount
        if dir == "left":
            self.lon -= amount
        if dir == "right":
            self.lon += amount

        print("New location: " + str(self.lon) + ", " + str(self.lat) + ", shifted by " + str(amount))
        if trigger_callback:
            self.call_callbacks()


class MapDrawer:
    displayHeight = 240
    displayWidth = 320

    def __init__(self, location, features, labels, style, displayHeight=240, displayWith=320):
        self.labels = labels
        assert isinstance(style, Style)
        assert isinstance(location, Location)
        self.location = location
        location.callbacks.append(lambda location: self.drawAll())
        self.style = style
        self.features = features
        self.displayWith = displayWith
        self.displayHeight = displayHeight

    def drawCoordinates(self, coordinates, style):
        factor = math.exp(self.location.z - 3)
        projected = []
        has_point_in_range = False
        for c in coordinates:
            lon = (c[0] - self.location.lon) * factor
            lat = 0 - (c[1] - self.location.lat) * factor
            projected.append([lon, lat])
            if 0 < lon < self.displayWidth and 0 < lat < self.displayHeight:
                has_point_in_range = True

        if not has_point_in_range:
            # No use drawing this, nothing in range
            return

        for i in range(0, len(projected) - 1):
            c0 = projected[i]
            c1 = projected[i + 1]
            display.drawLine(int(c0[0]), int(c0[1]), int(c1[0]), int(c1[1]), style.line)

    def drawLabel(self, label):
        if label.minzoom > self.location.z:
            return
        factor = math.exp(self.location.z - 3)
        lon = (label.lon - self.location.lon) * factor
        lat = 0 - (label.lat - self.location.lat) * factor
        if not (0 < lon < self.displayWidth and 0 < lat < self.displayHeight):
            return
        lower_case_count = sum(map(str.islower, label.label))
        estimated_size = lower_case_count * 7 + (len(label.label) - lower_case_count) * 9
        display.drawRect(int(lon - 2 - estimated_size / 2), int(lat) - 8, 4 + estimated_size, 16, True, 0x000000)
        display.drawText(int(lon - estimated_size / 2), int(lat) - 8, label.label)

    def drawAll(self):
        print("Redrawing map")
        for f in self.features:
            self.drawCoordinates(f, self.style)
        for l in self.labels:
            self.drawLabel(l)


class Navigatable:
    current_navigator = None

    def move(self, pressed, movement):
        if not pressed:
            return
        if (self.current_navigator is None):
            return
        self.current_navigator.move(movement)

    def attachButtons(self):
        buttons.attach(buttons.BTN_A, lambda pressed: self.move(pressed, "a"))
        buttons.attach(buttons.BTN_B, lambda pressed: self.move(pressed, "b"))
        buttons.attach(buttons.BTN_UP, lambda pressed: self.move(pressed, "up"))
        buttons.attach(buttons.BTN_DOWN, lambda pressed: self.move(pressed, "down"))
        buttons.attach(buttons.BTN_LEFT, lambda pressed: self.move(pressed, "left"))
        buttons.attach(buttons.BTN_RIGHT, lambda pressed: self.move(pressed, "right"))


def searchPath(spec):
    if (spec in os.listdir(".")):
        return "./" + spec
    try:
        os.listdir("/sd/apps/python/badgemap")
        return "/sd/apps/python/badgemap/" + spec
    except:
        return "/apps/python/badgemap/" + spec


def load_buildings(location):
    building_labels = []
    draw_banner(10, "Loading buildings... Please be patient")
    try:
        with open(searchPath("buildings.json"), "r") as buildings_file:
            buildings = json.load(buildings_file)
        draw_banner(10, "Buildings loaded")
        display.flush()
        building_coordinates = []
        for b in buildings["features"]:
            if b["geometry"]["type"] == "Point":
                c = b["geometry"]["coordinates"]
                txt = b["properties"]["text"]
                if txt is None:
                    continue
                txt = txt.replace("\n", " ")
                label = Label(c[0], c[1], txt)
                if (b["properties"]["text_size"] == 3.0):
                    label.minzoom = 15
                if (b["properties"]["text_size"] == 4.0):
                    label.minzoom = 14
                if label.label == "heaven" or label.label == "info":
                    label.minzoom = 12
                building_labels.append(label)
            if b["geometry"]["type"] == "LineString":
                building_coordinates.append(b["geometry"]["coordinates"])
            if b["geometry"]["type"] == "Polygon":
                building_coordinates.append(b["geometry"]["coordinates"][0])
    except:
        draw_banner(10, "Loading buildings failed! Continuing with testdata")
        print("Loading buildings failed")
        building_coordinates = [[
            [
                5.5254927277565,
                52.28380557517109
            ],
            [
                5.525519549846649,
                52.284022165932726
            ],
            [
                5.525224506855011,
                52.28403201094217
            ],
            [
                5.525195002555847,
                52.28382034275664
            ],
            [
                5.5254927277565,
                52.28380557517109
            ]
        ]]
        building_labels = [
            Label(5.5254, 52.2839, "heaven")
        ]

    tentStyle = Style()
    MapDrawer(location, building_coordinates, building_labels, tentStyle)


def load_geojson(filename, location, determine_color):
    display.drawRect(0, 45, 320, 20, True, 0x000000)
    draw_banner(10, "Loading " + filename + "... Please be patient")
    per_color = {}
    try:
        with open(searchPath(filename), "r") as buildings_file:
            buildings = json.load(buildings_file)
        draw_banner(10, filename + " loaded")
        for b in buildings["features"]:
            color = determine_color(b["properties"])
            if color not in per_color:
                per_color[color] = []
            if b["geometry"]["type"] == "Point":
                continue
            if b["geometry"]["type"] == "LineString":
                per_color[color].append(b["geometry"]["coordinates"])
            if b["geometry"]["type"] == "Polygon":
                per_color[color].append(b["geometry"]["coordinates"][0])
            if b["geometry"]["type"] == "MultiPolygon":
                per_color[color].append(b["geometry"]["coordinates"][0][0])
    except Exception as e:
        draw_banner(10, "Loading " + filename + " failed!")
        display.flush()
        print("Loading " + filename + " failed due to " + str(e))
        print(e)
        per_color[0xff0000] = [[
            [
                5.525232553482056,
                52.284081235956684
            ],
            [
                5.5251118540763855,
                52.283716969554376
            ],
            [
                5.52487850189209,
                52.28385808211962
            ],
            [
                5.525058209896088,
                52.28409272178551
            ]
        ]]

    for color in per_color.keys():
        MapDrawer(location, per_color[color], [], Style(color))


buttons.attach(buttons.BTN_HOME, lambda _: mch22.exit_python())
draw_banner(80, "Starting badgemap! This is " + version)

def print_copyright():
    display.drawFill(0x00000000)
    draw_banner(100, "Made by Pietervdvn")
    draw_banner(120, "Roads and water: (c) OpenStreetMap.org")
    draw_banner(160, "Interested in maps?")
    draw_banner(180, "Come to 'OpenStreetMap for Beginners' on monday")
    draw_banner(200, "11:00, Envelope (NL)  -- 21:00, DNA (EN)")
    display.flush()

print_copyright()

location = Location()

displayHeight = 240
displayWidth = 320

navigator = Navigatable()
navigator.attachButtons()



main_menu = Menu("MapBadge options", [
    MenuItem("Copyright", lambda: print_copyright()),
    MenuItem("Foo world", lambda: display.drawFill(0x00000)),
    MenuItem("Exit menu", lambda: toggle_menu(True))
])


def toggle_menu(pressed):
    if not pressed:
        return
    if navigator.current_navigator == location:
        navigator.current_navigator = main_menu
    else:
        navigator.current_navigator = location
    navigator.current_navigator.update()


buttons.attach(buttons.BTN_MENU, lambda pressed: toggle_menu(pressed))

navigator.current_navigator = location


def map_overlay():
    # Elements shown above the map
    display.drawRect(27, displayHeight - 20, 30, 20, True, 0x000000)
    display.drawText(32, displayHeight - 20, "exit")
    display.flush()


location.callbacks.append(lambda _: display.drawFill(0x406000))


def road_color(properties):
    if "surface" in properties and properties["surface"] == "grass":
        return 0x00ff00
    return 0xffffff


load_geojson("water.json", location, lambda _: 0x0000ff)
load_geojson("roads.json", location, road_color)
load_buildings(location)
location.callbacks.append(lambda _: map_overlay())
location.call_callbacks()
