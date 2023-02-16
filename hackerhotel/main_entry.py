import json
import buttons
import display
import utime
import wifi
from drawmap import Location
import utils
from map_init import MapInitializator
from menu import Menu, MenuItem
from navigatable import Navigatable
# from map_init import MapInitializator
# import mch22

exit_python = lambda: print("Exit python called")
# exit_python = mch.exit_python

class Main:
    """
    Has NTP been requested from wifi?
    """
    ntp_req = False
    navigator = Navigatable()

    """
    screen brightness
    """
    brightness = 255

    def ntp(self):
        if self.ntp_req:
            return
        self.ntp_req = True
        print("Requesting NTP")
        try:
            wifi.ntp()
        except:
            pass
        print("Current time:"+ str(utime.time()))
        print("Epoch time:"+str(utime.gmtime(0)))
        
    def drawUtilsTime(self):
        y = display.height() - 12
        (year, m, d, h, min, secs, wday, dayinyear) = utils.localtime()
        print("Local time is "+str(utils.localtime()))
        
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

        if secs < 10:
            secs = "0" + str(secs)
        else:
            secs = str(secs)


        msg = h + ":" + min + ":" + secs
        textw = 3 + display.getTextWidth(msg, "exo2_bold12")
        xp = display.width() - textw
        display.drawRect(xp, y, textw , 12, True, 0xfffffff)
        display.drawText(xp, y, msg, 0x888888, "exo2_bold12")

        if wifi.status():
            display.drawRect(xp - 15, y, 15, 12, True, 0xffffff)
            display.drawText(xp - 15, y, "W", 0x888888, "exo2_bold12")
            self.ntp()
        
        display.flush()

    def ch_brightness(self, i):
        self.brightness += i
        self.brightness %= 256
        print("Brightness is now " + str(self.brightness))
        display.brightness(self.brightness)
        display.flush()
        self.navigator.current_navigator.update(True)

    def detach_buttons(self):
        buttons.detach(buttons.BTN_A)
        buttons.detach(buttons.BTN_B)
        buttons.detach(buttons.BTN_UP)
        buttons.detach(buttons.BTN_DOWN)
        buttons.detach(buttons.BTN_LEFT)
        buttons.detach(buttons.BTN_RIGHT)
        buttons.detach(buttons.BTN_HOME)
        buttons.detach(buttons.BTN_MENU)
        buttons.detach(buttons.BTN_SELECT)
        buttons.detach(buttons.BTN_START)

    def main(self):
        self.detach_buttons()
        try:
            wifi.connect()
        except Exception as e:
            print("Connecting to wifi failed: " + str(e))
        configF = open("config.json", "r")
        config = json.loads(configF.read())
        configF.close()

        navigator = self.navigator
        maplocation = Location()
        navigator.attachButtons()

        map_init = MapInitializator(navigator, maplocation)
        items = [
            MenuItem("Loading map...", lambda: print("Not yet!")),
            MenuItem("Loading search index...", lambda: print("Not yet!")),
            MenuItem(lambda: "Updating..." if map_init.update_running else "Update map data",
                     lambda: map_init.update_map_data(config)),
            MenuItem("Remove map data", lambda: map_init.remove_map_data()),
            MenuItem(lambda: "Brightness: " + str(self.brightness) + " (use L & R)", lambda: self.ch_brightness(10),
                     on_left=lambda: self.ch_brightness(-10), on_right=lambda: self.ch_brightness(10)),
            MenuItem(lambda: "Write coordinates on the map: " + str(map_init.draw_coordinates), map_init.toggle_coordinates,
                     on_left=lambda: map_init.toggle_coordinates(False), on_right=lambda: map_init.toggle_coordinates(True)),
            MenuItem(lambda: "Write help banner on the map: " + str(map_init.draw_banner), map_init.toggle_banner,
                     on_left=lambda: map_init.toggle_banner(False), on_right=lambda: map_init.toggle_banner(True)),
            MenuItem("Exit", lambda: exit_python())
        ]

        mainmenu = Menu(config["name"], items, lambda: exit_python())
        mainmenu.postdraw.append(lambda: self.drawUtilsTime())
        navigator.set_navigator(mainmenu)
        buttons.attach(buttons.BTN_MENU, lambda b: navigator.set_navigator(mainmenu))

        [searchMenu] = map_init.init_map(config["map"])
        items[0] = MenuItem("Open Map", lambda: navigator.set_navigator(maplocation))
        items[1] = MenuItem("Search", lambda: navigator.set_navigator(searchMenu))

        mainmenu.update(True)


Main().main()
