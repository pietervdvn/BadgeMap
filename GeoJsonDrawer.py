import math

import display

import json
import os


class Style:
    line = 0xaa0000

    def __init__(self, linecolor=0xaa0000, minzoom=0):
        self.minzoom = minzoom
        self.line = linecolor


class LabelStyle:

    def __init__(self, background_colour=0x000000, text_colour=0xffffff, minzoom=18, maxzoom=25):
        self.maxzoom = maxzoom
        self.minzoom = minzoom
        self.text_colour = text_colour
        self.background_colour = background_colour


class Label:
    lat = 0
    lon = 0
    label = ""

    def __init__(self, lon, lat, label, category=None):
        self.category = category
        self.label = label.replace("\n", " ")
        self.lat = lat
        self.lon = lon


class Location:
    # Lat/lon of the _upper left_corner. Keep in mind that 'lat' is reversed

    lat = 52.2839
    lon = 5.5254
    z = 15

    currently_selected = None

    callbacks = []

    def update(self, very_dirty=False):
        self.currently_selected = None
        self.call_callbacks()

    def call_callbacks(self):
        for f in self.callbacks:
            # try:
            f(self)
            # except Exception as e:
            #   print("Could not execute a callback of location", str(e))

    def zoom_in(self):
        if (self.z >= 20):
            return
        self.z = self.z + 1
        factor = math.exp(self.z - 3)
        self.lon = self.lon + (display.width() / factor)
        self.lat = self.lat - (display.height() / factor)
        self.call_callbacks()
        print("Zoom in: new location: " + str(self.lat) + "," + str(self.lon))

    def zoom_out(self):
        if (self.z <= 12):
            return
        factor = math.exp(self.z - 3)
        self.lon = self.lon - (display.width() / factor)
        self.lat = self.lat + (display.height() / factor)
        self.z = self.z - 1
        self.call_callbacks()

    def move(self, dir, trigger_callback=True):
        if dir == "a":
            self.zoom_in()
            return

        if dir == "b":
            self.zoom_out()
            return

        amount = 1 / math.exp(self.z - 8)
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

    def lonlat_to_xy(self, lon, lat):
        n = 2.0 ** self.z
        xtl = (self.lon + 180.0) / 360.0 * n
        self_lat_rad = math.radians(self.lat)
        ytl = (1.0 - math.asinh(math.tan(self_lat_rad)) / math.pi) / 2.0 * n
        xarg = (lon + 180.0) / 360.0 * n
        lat_rad = math.radians(lat)
        yarg = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
        x = (xarg - xtl) * 265
        y = (yarg - ytl) * 265
        return (x, y)


class MapDrawer:
    displayHeight = display.width()
    displayWidth = display.height()

    def __init__(self, location, features, labels, style, label_style=None):
        self.labelStyle = label_style
        self.labels = labels
        if label_style is not None:
            assert isinstance(label_style, LabelStyle)
        if style is not None:
            assert isinstance(style, Style)
        assert isinstance(location, Location)
        self.location = location
        location.callbacks.append(lambda _: self.drawAll())
        self.style = style
        self.features = features

    def drawCoordinates(self, coordinates, style):
        projected = []
        has_point_in_range = False
        for c in coordinates:
            lon, lat = self.location.lonlat_to_xy(c[0], c[1])
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
        (x, y) = self.location.lonlat_to_xy(label.lon, label.lat)
        if not (0 < x < self.displayWidth and 0 < y < self.displayHeight):
            return
        estimated_size = display.getTextWidth(label.label) + 4
        rx = int(x - 2 - estimated_size / 2)
        ry = int(y) - 8
        rw = 4 + estimated_size
        rh = 16
        if rx <= display.width() / 2 < rx + rw and (ry - rh) <= display.height() / 2 < ry + 2 * rh:
            self.location.currently_selected = label
            display.drawRect(rx - 1, ry - 1, rw + 2, rh + 2, True, self.labelStyle.text_colour)
        display.drawRect(rx, ry, rw, rh, True, self.labelStyle.background_colour)
        display.drawText(int(x - estimated_size / 2), int(y) - 8, label.label, self.labelStyle.text_colour)

    def drawAll(self):
        print("Redrawing map")
        if self.style.minzoom <= self.location.z:
            for f in self.features:
                self.drawCoordinates(f, self.style)
        if self.labelStyle is not None and self.labelStyle.minzoom <= self.location.z <= self.labelStyle.maxzoom:
            for l in self.labels:
                self.drawLabel(l)
        display.flush()


def searchPath(spec):
    if (spec in os.listdir(".")):
        return "./" + spec
    try:
        os.listdir("/sd/apps/python/badgemap")
        return "/sd/apps/python/badgemap/" + spec
    except:
        return "/apps/python/badgemap/" + spec


def load_fields(location: object, field_label_style) -> list[Label]:
    draw_banner(10, "Loading field names... Please be patient")
    try:
        with open(searchPath("fields.json"), "r") as geojson_file:
            field_labels = []
            field_names = json.load(geojson_file)
            for f in field_names["features"]:
                if f["geometry"]["type"] != "Point":
                    continue
                c = f["geometry"]["coordinates"]
                txt = f["properties"]["text"].replace("\n", " ")
                if txt.endswith(" field"):
                    txt = txt[0: len(txt) - len(" field")]
                l = Label(c[0], c[1], txt)
                l.minzoom = 10
                l.maxzoom = 14
                field_labels.append(l)
            MapDrawer(location, [], field_labels, Style(), field_label_style)
            return field_labels
    except Exception as e:
        draw_banner(25, "Loading field names failed")
        print("Loading fields failed due to " + str(e))
        return []


def load_buildings(location: Location, building_style: Style, label_style_stage, label_style_building) -> list[Label]:
    building_labels = []
    building_labels_important = []
    try:
        with open(searchPath("buildings.json"), "r") as buildings_file:
            buildings = json.load(buildings_file)
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

                if b["properties"]["text_size"] == 3.0:
                    building_labels.append(label)
                if b["properties"]["text_size"] == 4.0:
                    building_labels_important.append(label)
                if label.label == "heaven" or label.label == "info":
                    building_labels_important.append(label)
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

    MapDrawer(location, building_coordinates, building_labels, building_style, label_style_building)
    MapDrawer(location, [], building_labels_important, building_style, label_style_stage)
    all_labels = []
    all_labels.extend(building_labels)
    all_labels.extend(building_labels_important)
    return all_labels


def load_geojson(filename: str, location: Location, determine_color, determine_label=None) -> list[Label]:
    display.drawRect(0, 45, display.width(), 20, True, 0x000000)
    draw_banner(10, "Loading " + filename + "... Please be patient")
    per_color = {}
    per_label_type = {}
    total = 0
    try:
        with open(searchPath(filename), "r") as buildings_file:
            buildings = json.load(buildings_file)
        draw_banner(10, filename + " loaded")
        for b in buildings["features"]:
            total += 1
            color = determine_color(b["properties"])
            if color not in per_color:
                per_color[color] = []
            if b["geometry"]["type"] == "Point":
                if determine_label is None:
                    continue
                props = b["properties"]
                labelstyle = determine_label(props)
                if labelstyle is None:
                    return
                if labelstyle not in per_label_type:
                    per_label_type[labelstyle] = []
                c = b["geometry"]["coordinates"]
                txt = None
                if "text" in props:
                    txt = props["text"]
                if "name" in props:
                    txt = props["name"]
                if txt is None:
                    continue
                txt = txt.replace("\n", " ").strip()
                if txt == "":
                    continue
                per_label_type[labelstyle].append(Label(c[0], c[1], txt))
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
        MapDrawer(location, per_color[color], [], color)

    all_labels: list[Label] = []
    for labelstyle in per_label_type.keys():
        all_labels.extend(per_label_type[labelstyle])
        MapDrawer(location, [], per_label_type[labelstyle], Style(), labelstyle)
    draw_banner(10, filename + " loaded: " + str(total) + " features loaded")
    return all_labels
