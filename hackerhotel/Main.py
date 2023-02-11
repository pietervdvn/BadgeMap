import mch22
import navigatable
from menu import Menu, MenuItem
from drawmap import Location, LineLayer


class Main:

    def main(self):

        navigator = navigatable.Navigatable()
        navigator.attachButtons()
        maplocation = Location()
    
        buildings = LineLayer(maplocation, "buildings.txt")

        mainmenu = Menu("HackerHotel Companion",
                  [
                      MenuItem("Open Map", lambda: navigator.set_navigator(maplocation)),
                      MenuItem("Item1", lambda: print("Selected 1")),
                      MenuItem("Item2", lambda: print("Selected 2"))
                  ], lambda: mch22.exit_python())
        navigator.set_navigator(mainmenu)
        
        
        
    