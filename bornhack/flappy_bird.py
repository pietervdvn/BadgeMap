import display
import buttons
import time
import random

display.drawFill(0)
display.drawText(0, 0, "Press (and hold)")
display.drawText(0, 12, "A to fly")
time.sleep(4)

while True:
    y = display.height() // 2
    speed = 0

    display.drawFill(0)
    obstacle_x = display.width()
    obstacle_y = random.randint(20, display.height() - 20)
    obstacle_y_opening = random.randint(14, 28)
    score = 0
    while 0 < y < display.height() - 12:
        display.drawRect(25, y, 12, 12, True, 0)
        display.drawRect(obstacle_x, 0, 12, obstacle_y - obstacle_y_opening, True, 0)
        display.drawRect(obstacle_x, obstacle_y + obstacle_y_opening, 12,
                         display.height() - obstacle_y - obstacle_y_opening, True, 0)

        y = y - speed
        obstacle_x = obstacle_x - 3
        display.drawRect(25, y, 12, 12, True, 0xff0000)
        display.drawRect(obstacle_x, 0, 12, obstacle_y - obstacle_y_opening, True, 0xffffff)
        display.drawRect(obstacle_x, obstacle_y + obstacle_y_opening, 12,
                         display.height() - obstacle_y - obstacle_y_opening, True, 0xffffff)

        if 13 < obstacle_x < 37:
            # We are going through the obstacle
            if not (obstacle_y - obstacle_y_opening < y < obstacle_y + obstacle_y_opening - 12):
                # and we are colliding...
                break
        if (obstacle_x < -12):
            score += 1
            obstacle_x = display.width()
            obstacle_y = random.randint(20, display.height() - 20)
            obstacle_y_opening = random.randint(14, 28)

        if not buttons.BTN_A.value:
            # Buttons are reversed!
            if speed < 5:
                speed += 1
        elif speed > -5:
            speed -= 1
        display.drawText(0, 0, "Score: " + str(score))
        time.sleep(0.1)
        display.flush()

    display.drawFill(0)
    display.drawText(0, 0, "Game over.", 2, 2)
    display.drawText(2, 20, "You scored " + str(score), 0xffffff, "")

    time.sleep(2)
