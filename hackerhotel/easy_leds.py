import neopixel

class EasyLeds:

    led_status = []
    def __init__(self, number_of_leds = 6):
        neopixel.enable()
        self.led_status = [0]*6*4
        
        
    def _commit(self):
        neopixel.send(bytes(self.led_status))
        
    def set_led(self, i, r, g, b, w):
        self.led_status[i * 4] = g
        self.led_status[i * 4 + 1] = r
        self.led_status[i * 4 + 2] = b
        self.led_status[i * 4 + 3] = w
        self._commit()

j = 0
while(True):
    j = (j + 1) % 5
    
    for i in range(0, 5):
        el.set_led(i, (j % 5), ((j+1) % 4), ((j+2) % 4), (j+3) % 4)
    utime.sleep(1)
