import display


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
    """
    A 'menu' will draw many menu-items on the screen
    """
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

    def update(self, very_dirty=False):
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
