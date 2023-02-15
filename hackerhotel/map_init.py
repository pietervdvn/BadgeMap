import display
from menu import Menu, MenuItem
import os
import wifi
import utils
import buttons
import math
from drawmap import LineLayer, PointLayer, Location

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


class MapInitializator:

    map_update_path = None
    update_running = False
    draw_coordinates = True
    draw_banner = True
    
    beelineColor = 0xffffff

    """
    Shared with the point layer
    Set 'selected' with an element from PointLayer to trigger a line around it
    """
    state = State()
    
    def __init__(self, navigator, maplocation):
        """
        :param navigator: 
        """
        self.navigator = navigator
        self.maplocation = maplocation

    def drawBanner(self, text, printToConsole=True):
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
        x = selected[0]
        y = selected[1]
        [x, y] = location.map([x, y])
        display.drawLine(display.width() / 2, display.height() / 2, x, y, self.beelineColor)

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
                    print("Skipped already existing file: " + l)
                    c += 1
                    s += 1
                    if c % 25 == 0:
                        self.drawBanner(str(c) + "/" + str(total) + "(cached: " + str(s) + ")...")
                    continue
                self.drawBanner(str(c) + "/" + str(total) + "(cached: " + str(s) + ") " + ": " + str(l))
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
            self.drawBanner("Removing " + f)
            os.remove("mapdata/" + f)
            removed_count += 1
        self.drawBanner("Removed " + str(removed_count) + " files")

    def toggle_coordinates(self, value=None):
        new_value = value
        if value is None:
            new_value = not self.draw_coordinates
        if new_value != self.draw_coordinates:
            self.draw_coordinates = new_value
            self.navigator.force_update()

    def draw_coordinate_debug(self, location):
        if not self.draw_coordinates:
            return
        print("Drawing debug info: " + str(math.floor(location.x)) + " " + str(math.floor(location.y)) + " " + str(
            location.z))
        display.drawText(0, 0, str(location.x) + " " + str(location.y) + " " + str(location.z), 0xffffff)

    def draw_help_banner(self):
        if not self.draw_banner:
            return
        self.drawBanner("        HOME                MENU                    FLOOR           SEARCH ", False)

    def toggle_banner(self, value=None):
        new_value = value
        if value is None:
            new_value = not self.draw_banner
        if new_value != self.draw_banner:
            self.draw_banner = new_value
            self.navigator.force_update()

    def select_item_lambda(self, entry):
        return lambda: self.state.setSelectedElement(entry)

    def build_search_index_for(self, pertile, targetlayer):
        print("Loading all entries for layer "+targetlayer)
        seen_labels = set()
        items = list()
        total = len(pertile)
        c = 0
        for [layername, pointlayer] in pertile:
            c += 1
            if c % 25 == 0:
                self.drawBanner("Indexing "+layername+" "+str(c)+"/"+str(total))
            if layername != targetlayer:
                continue
            # list of ['label', entry]
            self.drawBanner("Indexing "+layername+" "+str(c)+"/"+str(total))
            pointlayer._load_data(None)
            for i in range(0, len(pointlayer.pointdata)):
                entry = pointlayer.pointdata[i]
                label = entry[3]
                if label in seen_labels:
                    continue
                seen_labels.add(label)
                itm = MenuItem(label, self.select_item_lambda(entry))
                items.append(itm)
        items.sort(key=lambda i: i.title)
        return items

    def init_search_for_layer(self, all_menu_items, layername, pertile, i, global_search_menu):
        self.drawBanner("Initing search index for " + layername)
        search_menu_items = self.build_search_index_for(pertile, layername)
        search_menu = Menu(layername, search_menu_items, lambda: self.navigator.set_navigator(global_search_menu))
        all_menu_items[i] = MenuItem(layername, lambda: self.navigator.set_navigator(search_menu))
        self.navigator.set_navigator(search_menu)

    def init_search_menu_for_layer_lambda(self, all_menu_items, layername, pertile, i, global_search_menu):
        return lambda : self.init_search_for_layer(all_menu_items, layername, pertile, i, global_search_menu)

    def build_search_index(self, pertile):
        """
        :param pertile: ['layer name, without x/y', create_search_index_function]
        :type pertile: list()
        :return: 
        """
        print("Building search menu")

        layernames = list(set(map(lambda t: t[0], pertile)))
        layernames.sort()
        menu_items = []
        search_menu = Menu("Search menu", menu_items, lambda: self.navigator.set_navigator(self.maplocation))

        for i in range(0, len(layernames)):
            layername = layernames[i]
            print("Preparing menu item for "+layername+" "+str(i))
            itm = MenuItem(layername + " (*)",
                           self.init_search_menu_for_layer_lambda(menu_items, ""+layername, pertile, int(str(i)), search_menu))
            menu_items.append(itm)
        menu_items.append(MenuItem("Clear selected element", lambda : self.state.setSelectedElement(None)))
        print("Search index built")
        return search_menu

    def init_map(self, config):
        maplocation = self.maplocation

        [maplocation.x, maplocation.y, maplocation.z] = config['start']

        # Draw a background....
        # maplocation.callbacks.append(lambda l: display.drawFill(0x00aa77))

        styles = config["style"]
        self.draw_coordinates = config["show_coordinates"]
        self.draw_banner = config["show_button_labels"]

        pointlayers = list()

        max_x = 0
        max_y = 0
        # every tile has a size of generated_at_z
        # How much pixels does this cover on maplocation.default_zoom?

        all_files = os.listdir("mapdata")
        total = len(all_files)
        all_files.sort()
        i = 0

        for f in all_files:
            if i % 50 == 0:
                self.drawBanner("Preparing map tiles: " + str(i) + "/" + str(total))

            i += 1
            if not f.endswith(".points") and not f.endswith(".lines"):
                continue
            path = "mapdata/" + f

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
                fg = utils.fromRgb(style["fg"])
                bg = utils.fromRgb(style["bg"])
                pl = PointLayer(maplocation, path, range, fg, bg, minzoom, self.state)
                pointlayers.append([layer, pl])
            elif (layer.endswith(".lines")):
                ll = LineLayer(maplocation, path, range, utils.fromRgb(style["color"]), minzoom, self.state)
            else:
                raise "Invalid extension, should be '.lines' or '.points': " + layer

        maplocation.max_x = max_x
        maplocation.max_y = max_y

        style = styles["selected.points"]
        fg = utils.fromRgb(style["fg"])
        bg = utils.fromRgb(style["bg"])
        minzoom = int(style["minzoom"])
        selected_element_layer = PointLayer(maplocation, None, [0, 0, 999999999, 999999999], fg, bg, minzoom,
                                            self.state)
        selected_element_layer.pointdata = list()

        def update_selected():
            selected_element_layer.pointdata.clear()
            selected_element_layer.pointdata.append(self.state.selected_element)
            selected_element_layer.update()
            self.navigator.set_navigator(maplocation)

        self.state.callbacks.append(update_selected)

        maplocation.callbacks.append(self.drawBeeLine)
        self.beelineColor = utils.fromRgb(styles["selected.lines"]["color"])
        maplocation.callbacks.append(lambda l: self.draw_coordinate_debug(l))
        maplocation.callbacks.append(
            lambda l: self.draw_help_banner())

        maplocation.callbacks.append(lambda l: display.flush())

        returnToMap = lambda: self.navigator.set_navigator(self.maplocation)
        searchMenu = self.build_search_index(pointlayers)
        buttons.attach(buttons.BTN_START, lambda btn: self.navigator.set_navigator(searchMenu))

        floorSelectionMenu = Menu("Select floor", [
            MenuItem("Floor 0 (Ground floor)", lambda: self.state.setLevel(0)),
            MenuItem("Floor 1", lambda: self.state.setLevel(1)),
            MenuItem("Floor 2", lambda: self.state.setLevel(2))
        ], returnToMap)
        buttons.attach(buttons.BTN_SELECT, lambda btn: self.navigator.set_navigator(floorSelectionMenu))

        self.drawBanner("Map data is loaded!")

        return [searchMenu]
