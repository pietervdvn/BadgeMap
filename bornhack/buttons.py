import board
from digitalio import DigitalInOut, Direction, Pull

BTN_A = DigitalInOut(board.BTN_A)
BTN_A.direction = Direction.INPUT
BTN_A.pull = Pull.UP

BTN_B = DigitalInOut(board.BTN_B)
BTN_B.direction = Direction.INPUT
BTN_B.pull = Pull.UP

BTN_X = DigitalInOut(board.BTN_X)
BTN_X.direction = Direction.INPUT
BTN_X.pull = Pull.UP

BTN_Y = DigitalInOut(board.BTN_Y)
BTN_Y.direction = Direction.INPUT
BTN_Y.pull = Pull.UP



BTN_UP = BTN_A
BTN_DOWN = BTN_B
BTN_LEFT = BTN_X
BTN_RIGHT = BTN_Y