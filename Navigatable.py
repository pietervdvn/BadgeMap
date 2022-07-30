import buttons


class Navigatable:
    """
    The 'navigatble' handles most of the buttons (Up, down, left, right, A, B) and will pass them onto the 'current_navigator',
    which should implement 'move("some string indicating movement")' and 'update(bool)'
    """
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
