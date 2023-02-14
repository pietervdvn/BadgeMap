import json
import math
import os

import buttons
import display
import mch22
import utils
import utime
import wifi
from drawmap import LineLayer, Location, PointLayer
from menu import Menu, MenuItem
from navigatable import Navigatable


def fromRgb(rgb):
    [r, g, b] = rgb
    return (r * 256 + g) * 256 + b


class State:
    selected_element = None
    level = 0
    callbacks = list()

    def __init__(self):
        pass

    def run_callbacks(self):
        for f in self.callbacks:
            f()

    def setSelectedElement(self, element):
        self.selected_element = element
        self.run_callbacks()

    def setLevel(self, level):
        self.level = level
        self.run_callbacks()


class Main:
    navigator = Navigatable()
    maplocation = Location()
    """
    Shared with the point layer
    Set 'selected' with an element from PointLayer to trigger a line around it
    """
    state = State()

    """
    Has NTP been requested from wifi?
    """
    ntp_req = False

    """
    screen brightness
    """
    brightness = 255

    map_update_path = None
    update_running = False
    draw_coordinates = True

    def drawBanner(self, text, printToConsole = True):
        if printToConsole:
            print("Banner: " + text)
        display.drawRect(0, display.height() - 16, display.width(), 16, True, 0x000000)
        display.drawText(0, display.height() - 16, text, 0xffffff)
        display.flush()

    def drawBeeLine(self, location):
        """
        Draw a line to the currently selected element (if any)
        :return: 
        """
        selected = self.state.selected_element
        if selected is None:
            return
        [x, y] = selected
        [x, y] = location.map([x, y])
        display.drawLine(display.width() / 2, display.height() / 2, x, y, 0xffffff)

    def createSearchMenuItem(self, labelCreate, searchMenu):
        [label, createMenu] = labelCreate
        submenu = createMenu(lambda: self.navigator.set_navigator(searchMenu))
        return MenuItem(label, lambda: self.navigator.set_navigator(submenu))

    def _update_map_data(self, url):
        try:
            os.mkdir("mapdata")
        except:
            pass  # already exists

        print("Wifi status: " + str(wifi.status()))
        wifi.wait()
        utils.downloadToFile(url + "/all.txt", "mapdata/all.txt")
        self.drawBanner("Map update: fetched metadata")
        known_files = list(os.listdir("mapdata"))
        with open("mapdata/all.txt", "r") as f:
            c = 1
            s = 0
            l = f.readline()
            total = int(l)
            while True:
                l = f.readline()
                if l is None:
                    break
                l = l.strip()
                if l == "":
                    break
                if l in known_files:
                    print("Skipped already existing file: "+l)
                    c += 1
                    s += 1
                    if c % 25 == 0:
                        self.drawBanner(str(c) + "/" + str(total) + "(cached: "+str(s)+")...")
                    continue
                self.drawBanner(str(c) + "/" + str(total) + "(cached: "+str(s)+") " + ": " + str(l))
                c += 1
                utils.downloadToFile(url + "/" + l, "mapdata/" + l)
                
                
            self.drawBanner("Update completed!")

    def update_map_data(self, config):
        url = config["map_data_source"]

        if self.update_running:
            self.drawBanner("Update is already running!")
            return
        self.update_running = True
        self.navigator.force_update()
        self.drawBanner("Map data update started")
        try:
            self._update_map_data(url)
            self.maplocation = Location()
            self.init_map(config)
        except Exception as e:
            print(e)
            self.update_running = False
            self.navigator.force_update()
            self.drawBanner("Updating failed!")
            return
        self.update_running = False
        self.navigator.force_update()
        self.drawBanner("Map update complete!")

    def remove_map_data(self):
        removed_count = 0
        for f in os.listdir("mapdata"):
            self.drawBanner("Removing "+f)
            os.remove("mapdata/"+f)
            removed_count += 1
        self.drawBanner("Removed "+str(removed_count)+" files")

    def toggle_coordinates(self, value = None):
        new_value = value
        if value is None:
            new_value = not self.draw_coordinates
        if new_value != self.draw_coordinates:
            self.draw_coordinates = new_value
            self.navigator.force_update()
        
    def draw_coordinate_debug(self, location):
        if not self.draw_coordinates:
            return
        print("Drawing debug info: "+str(math.floor(location.x))+" "+str(math.floor(location.y))+" "+str(location.z))
        display.drawText(0,0, str(location.x)+" "+str(location.y)+" "+str(location.z), 0xffffff)
        
    def init_map(self, config):
        maplocation = self.maplocation

        [maplocation.x, maplocation.y, maplocation.z] = config['start']
        [maplocation.max_x, maplocation.max_y] = config['max']

        # Draw a background....
        maplocation.callbacks.append(lambda l: display.drawFill(0x00aa77))

        styles = config["style"]

        searchIndex = list()

        max_x = 0
        max_y = 0
        generated_at_z = 14
        # every tile has a size of generated_at_z
        # How much pixels does this cover on maplocation.default_zoom?

        total = len(os.listdir("mapdata"))
        i = 0
        for f in os.listdir("mapdata"):
            if i % 50 == 0:
                self.drawBanner("Preparing map tiles: " + str(i)+"/"+str(total))

            i += 1
            if(i > 50):
                break
            if not f.endswith(".points") and not f.endswith(".lines"):
                continue
            path = "mapdata/"+f
            

            [x, y, layer] = f.split("_")
            x = int(x)
            y = int(y)
            max_x = max(x, max_x)
            max_y = max(y, max_y)

            # x,y depicts the upper-left coordinate of a tile 

            style = styles[layer]
            minzoom = int(styles[layer]["minzoom"])
            range = [x, y, x + 265, y + 265]

            if (layer.endswith(".points")):
                fg = fromRgb(style["fg"])
                bg = fromRgb(style["bg"])
                print("Initing map layer with: "+path+" "+",".join(map(str,range))+" "+str(fg)+" "+str(bg)+" "+str(minzoom))
                pl = PointLayer(maplocation, path, range, fg, bg, minzoom, self.state)
                # searchIndex.append([layer, pl.createSearchIndex])
            elif (layer.endswith(".lines")):
                ll = LineLayer(maplocation, path, range, fromRgb(style["color"]), minzoom, self.state)
            else:
                raise "Invalid extension, should be '.lines' or '.points': " + layer

        style = styles["selected.points"]
        fg = fromRgb(style["fg"])
        bg = fromRgb(style["bg"])
        minzoom = int(style["minzoom"])
        selected_element_layer = PointLayer(maplocation, None, [0,0,999999999,999999999], fg, bg, minzoom, self.state)
        selected_element_layer.pointdata = list()

        def update_selected():
            selected_element_layer.pointdata.clear()
            selected_element_layer.pointdata.append(self.state.selected_element)
            selected_element_layer.update()
            self.navigator.set_navigator(maplocation)

        self.state.callbacks.append(update_selected)

        maplocation.callbacks.append(self.drawBeeLine)
        maplocation.callbacks.append(lambda l: self.draw_coordinate_debug(l) )
        maplocation.callbacks.append(
            lambda l: self.drawBanner("        HOME                MENU                    FLOOR           SEARCH ", False))

        maplocation.callbacks.append(lambda l: display.flush())

        searchMenu = None
        returnToMap = lambda: self.navigator.set_navigator(maplocation)
        if len(searchIndex) == 1:
            [_, createMenu] = searchIndex[0]
            searchMenu = createMenu(returnToMap)
        else:
            items = list()
            searchMenu = Menu("Search", items, returnToMap)
            for labelCreate in searchIndex:
                items.append(self.createSearchMenuItem(labelCreate, searchMenu))
        buttons.attach(buttons.BTN_START, lambda btn: self.navigator.set_navigator(searchMenu))

        floorSelectionMenu = Menu("Select floor", [
            MenuItem("Floor 0 (Ground floor)", lambda: self.state.setLevel(0)),
            MenuItem("Floor 1", lambda: self.state.setLevel(1)),
            MenuItem("Floor 2", lambda: self.state.setLevel(2))
        ], returnToMap)
        buttons.attach(buttons.BTN_SELECT, lambda btn: self.navigator.set_navigator(floorSelectionMenu))

        self.drawBanner("Map data is loaded!")

        return [searchMenu]

    def ntp(self):
        if self.ntp_req:
            return
        self.ntp_req = True
        print("Requesting NTP")
        try:
            wifi.ntp()
        except:
            pass

    def drawUtilsTime(self):
        y = display.height() - 12
        (year, m, d, h, min, secs, wday, dayinyear) = utime.localtime()
        if wifi.status():
            display.drawRect(0, y, 10, 12, True, 0xffffff)
            display.drawText(0, y, "W", 0x888888, "exo2_bold12")
            self.ntp()

        if year < 2023:
            return
        if h < 10:
            h = "0" + str(h)
        else:
            h = str(h)
        if min < 10:
            min = "0" + str(min)
        else:
            min = str(min)

        msg = h + ":" + min
        display.drawRect(20, y, display.getTextWidth(msg, "exo2_bold12"), 12, True, 0xfffffff)
        display.drawText(20, y, msg, 0x888888, "exo2_bold12")
        display.flush()

    def ch_brightness(self, i):
        self.brightness += i
        self.brightness %= 256
        print("Brightness is now " + str(self.brightness))
        display.brightness(self.brightness)
        display.flush()
        self.navigator.current_navigator.update(True)

    def main(self):
        try:
            wifi.connect()
        except Exception as e:
            print("Connecting to wifi failed: " + str(e))
        configF = open("config.json", "r")
        config = json.loads(configF.read())
        configF.close()
        
        navigator = self.navigator
        maplocation = self.maplocation
        navigator.attachButtons()

        items = [
            MenuItem("Loading map...", lambda: print("Not yet!")),
            MenuItem("Loading search index...", lambda: print("Not yet!")),
            MenuItem(lambda: "Updating..." if self.update_running else "Update map data",
                     lambda: self.update_map_data(config)),
            MenuItem("Remove map data", lambda: self.remove_map_data()),
            MenuItem(lambda: "Brightness: " + str(self.brightness) + " (use L & R)", lambda: self.ch_brightness(10),
                     on_left=lambda: self.ch_brightness(-10), on_right=lambda: self.ch_brightness(10)),
            MenuItem(lambda: "Write coordinates on the map: "+str(self.draw_coordinates), self.toggle_coordinates,
                     on_left=lambda: self.toggle_coordinates(False), on_right=lambda: self.toggle_coordinates(True)),
            MenuItem("Exit", lambda: mch22.exit_python())
        ]

        mainmenu = Menu(config["title"], items, lambda: mch22.exit_python())
        mainmenu.postdraw.append(lambda: self.drawUtilsTime())
        navigator.set_navigator(mainmenu)
        buttons.attach(buttons.BTN_MENU, lambda b: navigator.set_navigator(mainmenu))

        [searchMenu] = self.init_map(config)
        items[0] = MenuItem("Open Map", lambda: navigator.set_navigator(maplocation))
        items[1] = MenuItem("Search", lambda: navigator.set_navigator(searchMenu))

        mainmenu.update(True)


Main().main()
