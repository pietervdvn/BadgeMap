import math
import os
import mch22
import display
import buttons
import json


def draw_banner(h, text, background_colour=0x000000, text_colour=0xffffff):
    display.drawRect(0, h, display.width(), 20, True, background_colour)
    display.drawText(10, h + 2, text, text_colour)
    display.flush()


class MenuItem:

    def __init__(self, title, on_selected, on_left=None, on_right=None):
        self.on_right = on_right
        self.on_left = on_left
        self.on_selected = on_selected
        self.title = title


class Menu:
    selected = 0
    dirty = True
    previous_offset = 0

    def __init__(self, title, menuitems, fallback):
        """

        :type title: string
        """
        self.fallback = fallback
        self.menuitems = menuitems
        self.title = title

    def update(self, very_dirty = False):
        self.dirty = self.dirty or very_dirty
        if self.dirty:
            display.drawFill(0xcccccc)
            draw_banner(0, self.title, 0xffffff, 0x000000)
        offset = (self.selected // 10) * 10
        if self.previous_offset != offset:
            self.dirty = True
        l = len(self.menuitems)
        if self.dirty:
            for i in range(offset, min(offset + 11, l)):
                item = self.menuitems[i]
                title = item.title
                if callable(title):
                    title = title()
                j = i - offset
                draw_banner(20 + j * 20, title)
        display.drawRect(0, 20, 10, min(display.height(), len(self.menuitems) * 20) - 20, True, 0x000000)
        display.drawRect(2, 27 + (self.selected - offset) * 20, 6, 6, True, 0xffffff)
        if l > 10:
            rh = 25
            display.drawRect(display.width() - 10, 20, 6, display.height(), True, 0x000000)
            display.drawRect(display.width() - 10, 20 + self.selected * (display.height() - rh - 20) / l, 6, rh, False,
                             0xffffff)
        display.flush()
        self.dirty = False

    def move(self, direction):
        if direction == "a":
            self.menuitems[self.selected].on_selected()
            return

        if direction == "b":
            self.fallback()
            return

        if direction == "up":
            self.selected = self.selected - 1
            if self.selected < 0:
                self.selected = len(self.menuitems) - 1
        if direction == "down":
            self.selected = (self.selected + 1) % len(self.menuitems)
        item: MenuItem = self.menuitems[self.selected]
        if direction == "left":
            if item.on_left is not None:
                item.on_left()
            elif len(self.menuitems) > 10:
                self.selected = self.selected - 10
                if self.selected < 0:
                    self.selected = 0
        if direction == "right":
            if item.on_right is not None:
                item.on_right()
            elif len(self.menuitems) > 10:
                self.selected = self.selected + 10
                if self.selected > len(self.menuitems):
                    self.selected = len(self.menuitems)
        self.update()


class Style:
    line = 0xaa0000

    def __init__(self, linecolor=0xaa0000, minzoom=0):
        self.minzoom = minzoom
        self.line = linecolor


class LabelStyle:

    def __init__(self, background_colour=0x000000, text_colour=0xffffff, minzoom=16, maxzoom=25):
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
    z = 18

    currently_selected = None

    callbacks = []

    def update(self, very_dirty = False):
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
        self.call_callbacks()
        print("Zoom in: new location: " + str(self.lat) + "," + str(self.lon))

    def zoom_out(self):
        if (self.z <= 12):
            return
        self.z = self.z - 1
        self.call_callbacks()

    def move(self, dir, trigger_callback=True):
        if dir == "a":
            self.zoom_in()
            return

        if dir == "b":
            self.zoom_out()
            return

        amount = 1 / math.exp(self.z - 10)
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
      x = (xarg - xtl)*265 + display.width()/2
      y = (yarg - ytl)*265 + display.height()/2
      return (x, y)

    def xy_to_lonlat(self, x, y):
      n = 2.0 ** self.z
      xtl = (self.lon + 180.0) / 360.0 * n
      self_lat_rad = math.radians(self.lat)
      ytl = (1.0 - math.asinh(math.tan(self_lat_rad)) / math.pi) / 2.0 * n
      xtile = xtl + x
      ytile = ytl + y
      lon_deg = xtile / n * 360.0 - 180.0
      lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
      lat_deg = math.degrees(lat_rad)
      return (lat_deg, lon_deg)


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
        lower_case_count = sum(map(str.islower, label.label))
        estimated_size = lower_case_count * 7 + (len(label.label) - lower_case_count) * 9
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


class Navigatable:
    current_navigator = None

    def move(self, pressed, movement):
        if not pressed:
            return
        if self.current_navigator is None:
            return
        self.current_navigator.move(movement)

    def attachButtons(self):
        buttons.attach(buttons.BTN_A, lambda pressed: self.move(pressed, "a"))
        buttons.attach(buttons.BTN_B, lambda pressed: self.move(pressed, "b"))
        buttons.attach(buttons.BTN_UP, lambda pressed: self.move(pressed, "up"))
        buttons.attach(buttons.BTN_DOWN, lambda pressed: self.move(pressed, "down"))
        buttons.attach(buttons.BTN_LEFT, lambda pressed: self.move(pressed, "left"))
        buttons.attach(buttons.BTN_RIGHT, lambda pressed: self.move(pressed, "right"))

    def set_navigator(self, n):
        self.current_navigator = n
        n.update(True)


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


def print_copyright():
    display.drawFill(0x00000000)
    draw_banner(100, "Made by Pietervdvn")
    draw_banner(120, "Roads and water: (c) OpenStreetMap.org")
    draw_banner(160, "Interested in maps?")
    draw_banner(180, "Come to 'OpenStreetMap for Beginners' on monday")
    draw_banner(200, "11:00, Envelope (NL)  -- 21:00, DNA (EN)")
    display.flush()


class Main:
    location = Location()
    navigator = Navigatable()
    version = "0.2.0 (MCH)"
    background_color = 0x406000
    show_overlays = True
    brightness = 255

    water_style = Style(0x0000ff)
    grass_path_style = Style(0x00ff00)
    road_style = Style(0xffffff)
    building_style = Style(0xff0000)
    village_style = Style(0xffff00, 16)
    village_label_style = LabelStyle(0x000000, 0xaaaa00, 15)
    field_label_style = LabelStyle(0x88bb00, 0x000000, 10, 14)

    all_labels: list[Label] = []

    selected_label: Label = None

    def __init__(self):
        self.navigator.attachButtons()
        self.main_menu = Menu("MapBadge options", [
            MenuItem("Browse location index...", lambda: self.search_index(), None, lambda: self.search_index()),
            MenuItem("Copyright", lambda: print_copyright()),
            MenuItem(lambda: "Toggle button labels (currently " + ("shown" if self.show_overlays else "hidden") + ")",
                     lambda: self.toggle_overlays(),
                     lambda: self.toggle_overlays(),
                     lambda: self.toggle_overlays()),
            MenuItem(lambda: "Toggle background color (currently: " + (
                "black" if self.background_color == 0 else "green") + ")",
                     lambda: self.toggle_background(),
                     lambda: self.toggle_background(),
                     lambda: self.toggle_background()),
            MenuItem(lambda: "Change brigtness (currently " + str(self.brightness) + ")",
                     lambda: self.change_brightness_selected(), lambda: self.change_brightness(-15),
                     lambda: self.change_brightness(15)),
            MenuItem("Exit menu", lambda: self.toggle_menu(True))
        ], lambda: self.toggle_menu(True))
        buttons.attach(buttons.BTN_SELECT, lambda p: self.select_item(p))
        pass

    def select_item(self, pressed):
        if (not pressed):
            return
        self.selected_label = self.location.currently_selected

    def toggle_background(self):
        if self.background_color == 0x000000:
            self.background_color = 0x406000
        else:
            self.background_color = 0x000000
        self.navigator.current_navigator.update(True)

    def toggle_overlays(self):
        self.show_overlays = not self.show_overlays
        self.navigator.current_navigator.update(True)

    def change_brightness_selected(self):
        draw_banner(100, "Use left and right to change the brightness", 0xff0000, 0x000000)

    def change_brightness(self, diff):
        if self.brightness < 15 or (self.brightness == 15 and diff < 0):
            diff = (diff // abs(diff))
        self.brightness += diff
        if self.brightness <= 0 or self.brightness > 255:
            self.brightness -= diff
            return
        display.brightness(self.brightness)
        self.navigator.current_navigator.update(True)

    def toggle_menu(self, pressed):
        if not pressed:
            return
        if self.navigator.current_navigator == self.location:
            self.navigator.set_navigator(self.main_menu)
        else:
            self.navigator.set_navigator(self.location)

    def map_overlay(self):

        display.width() / 2

        display.drawLine(display.width() // 2 - 5, display.height() // 2, display.width() // 2 + 5,
                         display.height() // 2, 0xffffff)
        display.drawLine(display.width() // 2, display.height() // 2 - 5, display.width() // 2,
                         display.height() // 2 + 5, 0xfffff)

        if self.selected_label is not None:
            x, y = self.location.lonlat_to_xy(self.selected_label.lon, self.selected_label.lat)
            display.drawLine(x, y,
                             display.width() // 2, display.height() // 2, 0xfffff)

        if self.show_overlays:
            # Elements shown above the map
            display.drawRect(27, display.height() - 20, 30, 20, True, 0x000000)
            display.drawText(32, display.height() - 20, "exit")

            display.drawRect(106, display.height() - 20, 40, 20, True, 0x000000)
            display.drawText(111, display.height() - 20, "menu")

            display.drawRect(205, display.height() - 20, 40, 20, True, 0x000000)
            display.drawText(210, display.height() - 20, "slct")

            display.drawRect(display.width() - 20, display.height() - 20, 30, 20, True, 0x000000)
            display.drawText(display.width() - 15, display.height() - 20, str(self.location.z))

        display.flush()

    def select_road_color(self, properties):
        if "surface" in properties and properties["surface"] == "grass":
            return self.grass_path_style
        return self.road_style

    def select(self, l):
        self.selected_label = l
        self.navigator.set_navigator(self.location)

    def init_search_index(self):
        def open_menu():
            self.navigator.set_navigator(self.main_menu)

        filtered_labels = []
        for i in range(len(self.all_labels)):
            l = self.all_labels[
                i]  # This seems to be a very roundabout way to get the labels, as we might just use a for loop too
            # However, not using this will pass 'l' as closure, always selecting the last value
            if l.label.strip() == "":
                continue
            filtered_labels.append(l)
        menu_items: list[MenuItem] = list(map(lambda l: MenuItem(l.label, lambda: self.select(l)), filtered_labels))
        self.search_menu = Menu("Locations index (< and > to skip 20)", menu_items, lambda: open_menu())

    def search_index(self):
        self.navigator.set_navigator(self.search_menu)

    def main(self):
        version = self.version
        print("Starting BadgeMap " + self.version)

        buttons.attach(buttons.BTN_HOME, lambda _: mch22.exit_python())
        print_copyright()
        draw_banner(80, "Starting badgemap! This is " + version)

        location = self.location

        buttons.attach(buttons.BTN_MENU, lambda pressed: self.toggle_menu(pressed))

        self.navigator.current_navigator = location

        location.callbacks.append(lambda _: display.drawFill(self.background_color))

        all_labels: list[Label] = []
        all_labels.extend(load_geojson("water.json", location, lambda _: self.water_style))
        all_labels.extend(load_geojson("roads.json", location, lambda props: self.select_road_color(props)))
        all_labels.extend(
            load_geojson("villages.json", location, lambda _: self.village_style, lambda _: self.village_label_style))

        building_label_style = LabelStyle()
        building_label_style.minzoom = 14
        building_label_style_important = LabelStyle()
        building_label_style_important.minzoom = 13

        all_labels.extend(
            load_buildings(location, self.building_style, building_label_style, building_label_style_important))
        all_labels.extend(load_fields(location, self.field_label_style))
        location.callbacks.append(lambda _: self.map_overlay())
        location.call_callbacks()

        all_labels.sort(key=lambda l: l.label.lower())
        if len(all_labels) < 3:
            all_labels.append(Label(0, 0, "Testlabel"))
            all_labels.append(Label(0, 0, "Testlabel 0"))
        self.all_labels = all_labels
        self.init_search_index()


main = Main()
main.main()
