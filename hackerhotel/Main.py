import mch22
import navigatable
from menu import Menu, MenuItem
from drawmap import LineLayer, Location, PointLayer
import display
import json
import buttons

def fromRgb(rgb):
    [r,g,b] = rgb
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
    navigator = navigatable.Navigatable()
    maplocation = Location()
    """
    Shared with the point layer
    Set 'selected' with an element from PointLayer to trigger a line around it
    """
    state = State()
    
    def drawBanner(self, text):
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
    
    def init_map(self, config):
        maplocation = self.maplocation
        
        [maplocation.x, maplocation.y, maplocation.z] = config['start']
        [maplocation.max_x, maplocation.max_y] = config['max']

        # Draw a background....
        maplocation.callbacks.append(lambda l: display.drawFill(0x00aa77))

        pointlayers = []
        styles = config["style"]
        
        searchIndex = list()
        for layer in config["layers"]:
            self.drawBanner("Loading "+layer)
            if(layer.endswith(".points")):
                fg = fromRgb(styles[layer]["fg"])
                bg = fromRgb(styles[layer]["bg"])
                minzoom = int(styles[layer]["minzoom"])
                pl = PointLayer(maplocation, layer, fg, bg, minzoom, self.state)
                pointlayers.append(pl)
                pl._load_data(maplocation)
                searchIndex.append([layer, pl.createSearchIndex])
                
            elif (layer.endswith(".lines")):
                ll = LineLayer(maplocation, layer, fromRgb(styles[layer]), self.state)
                ll._load_data(maplocation)
            else:
                raise "Invalid extension, should be '.lines' or '.points': "+layer

        style = styles["selected.points"]
        fg = fromRgb(style["fg"])
        bg = fromRgb(style["bg"])
        minzoom = int(style["minzoom"])
        selected_element_layer = PointLayer(maplocation, None, fg, bg, minzoom, self.state)
        selected_element_layer.pointdata = list()
        
        
        def update_selected():
            selected_element_layer.pointdata.clear()
            selected_element_layer.pointdata.append(self.state.selected_element)
            selected_element_layer.update()
            self.navigator.set_navigator(maplocation)
        self.state.callbacks.append(update_selected)
        
        maplocation.callbacks.append(self.drawBeeLine)
        maplocation.callbacks.append(lambda l: self.drawBanner("        HOME                MENU                    FLOOR           SEARCH "))
        

        
        
        maplocation.callbacks.append(lambda l: display.flush())
        
        
        searchMenu = None
        returnToMap = lambda: self.navigator.set_navigator(maplocation)
        if len(searchIndex) == 1:
            [_, createMenu] = searchIndex[0]
            searchMenu = createMenu(returnToMap)
        else:
            items = list()
            searchMenu = Menu("Search", items, returnToMap )
            for labelCreate in searchIndex:
                items.append(self.createSearchMenuItem(labelCreate, searchMenu))
        buttons.attach(buttons.BTN_START, lambda btn :  self.navigator.set_navigator(searchMenu))
        
        
        floorSelectionMenu = Menu("Select floor", [
            MenuItem("Floor 0 (Ground floor)", lambda: self.state.setLevel(0)),
            MenuItem("Floor 1", lambda: self.state.setLevel(1)),
            MenuItem("Floor 2", lambda: self.state.setLevel(2)) 
        ], returnToMap)
        buttons.attach(buttons.BTN_SELECT, lambda btn :  self.navigator.set_navigator(floorSelectionMenu))

        self.drawBanner("Map data is loaded!")
        
        return [searchMenu]
        

    def main(self):
        
        configF = open("config.json", "r")
        config = json.loads(configF.read())
        configF.close()
        
        navigator = self.navigator
        maplocation = self.maplocation
        navigator.attachButtons()
        
        items =[
            MenuItem("Loading map...", lambda:  print("Not yet!")),
            MenuItem("Loading search index...", lambda: print("Not yet!")),
            MenuItem("Detach", lambda: self.navigator.set_navigator(None)),
            MenuItem("Exit", lambda: mch22.exit_python())
        ]
        
        mainmenu = Menu("HackerHotel Companion",items, lambda: mch22.exit_python())
        navigator.set_navigator(mainmenu)
        buttons.attach(buttons.BTN_MENU, lambda b: navigator.set_navigator(mainmenu))

        [searchMenu] = self.init_map(config)
        items[0] = MenuItem("Open Map", lambda: navigator.set_navigator(maplocation))
        items[1] = MenuItem("Search", lambda : navigator.set_navigator(searchMenu))
        
        mainmenu.update(True)

    # navigator.set_navigator(maplocation)


Main().main()
