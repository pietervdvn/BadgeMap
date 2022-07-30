import buttons
import display
import mch22
from GeoJsonDrawer import Location, Style, LabelStyle, Label, load_geojson, load_buildings, load_fields
from Menu import draw_banner, MenuItem, Menu
from Navigatable import Navigatable


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
    village_style = Style(0xffff00, 18)
    village_label_style = LabelStyle(0x000000, 0xaaaa00, 18)
    field_label_style = LabelStyle(0x88bb00, 0x000000, 13, 17)

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
        if self.selected_label is None:
            self.selected_label = self.location.currently_selected
        else:
            self.selected_label = None
        self.location.update()

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
