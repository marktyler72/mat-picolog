import os
import rp2

def format_time(t_tuple):
    return "{0:4d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*t_tuple)

def format_human(vals):
    '''Formats a size value in kB, MB, GB etc.'''
    results = []
    units = ["", "k", "M", "G", "T"]
    for val in vals:
        temp = val
        divisor = 0
        while temp >= 2000:
            divisor += 1
            temp = temp // 1000    
        results.append(str(temp) + units[divisor])
    return results


class SDVolume():
    def __init__(self):
        from machine import SPI, Pin
        import sdcard 
        spi = SPI(1,sck=Pin(14), mosi=Pin(15), miso=Pin(12))
        cs = Pin(13)
        self._sd = sdcard.SDCard(spi, cs, baudrate=5_280_000)
        self._mount_point = None

    def mount(self, mount_point='/sd'):
        os.mount(self._sd, mount_point, readonly=False)
        self._mount_point = mount_point

    def umount(self):
        if self._mount_point is not None:
            os.umount(self._mount_point)


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink_1hz():
    # Cycles: 1 + 7 + 32 * (30 + 1) = 1000
    set(pins, 1)
    set(x, 31)                  [6]
    label("delay_high")
    nop()                       [29]
    jmp(x_dec, "delay_high")

    # Cycles: 1 + 7 + 32 * (30 + 1) = 1000
    set(pins, 0)
    set(x, 31)                  [6]
    label("delay_low")
    nop()                       [29]
    jmp(x_dec, "delay_low")

class Led():
    def __init__(self):
        from machine import Pin
        self._led = Pin(25, Pin.OUT)
        self._led.off()
        self.sm = None

    def on(self):
        self._led.on()

    def off(self):
        self._led.off()
        
    def toggle(self):
        self._led.toggle()

    def auto_flash(self, start=False):
        if start:
            if self.sm is None:
                self.sm = rp2.StateMachine(0, blink_1hz, freq=2000, set_base=self._led)
            self.sm.active(1)
        else:
            if self.sm is not None:
                self.sm.active(0)
