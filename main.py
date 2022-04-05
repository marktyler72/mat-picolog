# Sensor Display - Main code

from PiicoDev_BME280 import PiicoDev_BME280
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
from PiicoDev_SSD1306 import *
from PiicoDev_Unified import sleep_ms
from machine import SPI, Pin
import sdcard 
import uos
import time

_ATMOS_MEASUREMENT_INTERVAL = 20000 # ms
_DIST_MEASUREMENT_INTERVAL = 500 # ms

def format_time(time_tuple):
    return "{0:4d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}".format(*time_tuple)

class Display(object):
    BLACK = 0
    WHITE = 1

    TEMP_LINE = 1
    PRES_LINE = 15
    RH_LINE = 30
    DIST_LINE = 45

    def __init__(self):
        self.disp = create_PiicoDev_SSD1306() # initialise the display
        self.disp.setContrast(0x80)

    def update(self, tempC=0.0, pres_hPa=0.0, humRH=0.0, dist_mm=0):
        self.disp.fill(self.BLACK)
        self.disp.text("Temp: {0:04.1f} C".format(tempC), 1, self.TEMP_LINE, self.WHITE)
        self.disp.text("Pres: {0:4.0f} hPa".format(pres_hPa), 1, self.PRES_LINE, self.WHITE)
        self.disp.text("Hum:  {0:04.1f} %RH".format(humRH), 1, self.RH_LINE, self.WHITE)
        if dist_mm is None:
          self.disp.text("Dist: *****", 1, self.DIST_LINE, self.WHITE)
        else:
          self.disp.text("Dist: {0:5d} mm".format(dist_mm), 1, self.DIST_LINE, self.WHITE)
        self.disp.show()

    def off(self):
        self.disp.poweroff()

    def on(self):
        self.disp.poweron()

    def set_contrast(self, contrast=0x80):
        self.disp.setContrast(contrast)

class SDCARD():
    def __init__(self):
        spi = SPI(1,sck=Pin(14), mosi=Pin(15), miso=Pin(12))
        cs = Pin(13)
        self._sd = sdcard.SDCard(spi, cs)
        self.mount_point = None

    def mount(self, mount_point='/sd'):
        self.mount_point = mount_point
        uos.mount(self._sd, self.mount_point, readonly=False)

    def umount(self):
        uos.umount(self.mount_point)

def main_loop():

#    atmos_sensor = PiicoDev_BME280(temp_oversamp=1, pres_oversamp=1, hum_oversamp=1, iir=0) # initialise the sensor
    atmos_sensor = PiicoDev_BME280() # initialise the sensor
    dist_sensor = PiicoDev_VL53L1X()
    dist_sensor.distance_mode = 2
    dist_sensor.timing_budget = 200

    display = Display()
    sleep_ms(20)
    display.update()

    tempC , pres_hPa, humRH, range_mm = (0.0, 0.0, 0.0, 0)

    sleep_time = _DIST_MEASUREMENT_INTERVAL
    time_to_next_atmos_measurement = 0
    range_sum = 0
    num_range_samples = 0

    with open('/sd/recorded_data.txt', "a") as data_file:
        while (True):           
            range_mm, status = dist_sensor.distance
            #print("Dist ", range_mm, "mm (", status, ")")
            if not status["ok"]:
                range_mm = None
            else:
                range_sum += range_mm
                num_range_samples += 1

            if time_to_next_atmos_measurement <= 0:
                tempC, presPa, humRH = atmos_sensor.values() # read all data from the sensor
                pres_hPa = presPa / 100 # convert air pressure Pascals -> hPa (or mbar, if you prefer)
                #print(str(tempC)+" °C  " + str(pres_hPa)+" hPa  " + str(humRH)+" %RH")

                if num_range_samples > 0:
                    avg_range = range_sum / num_range_samples
                    avg_range_str = " {0:5.0f} mm".format(avg_range)
                else:
                    avg_range_str = " ***** mm"

                data_file.write("{0:s}| {1:4.1f} C {2:6.1f} hPa, {3:4.1f} %, {4}\n".format(format_time(time.localtime()), tempC, pres_hPa, humRH, avg_range_str))
                data_file.flush()

                range_sum = 0
                num_range_samples = 0
                time_to_next_atmos_measurement = _ATMOS_MEASUREMENT_INTERVAL

            display.update(tempC, pres_hPa, humRH, range_mm)

            sleep_ms(sleep_time)
            time_to_next_atmos_measurement -= sleep_time

print("Started at " + format_time(time.localtime()))
sd = SDCARD()
sd.mount()

try:
    main_loop()
except KeyboardInterrupt:
    sd.umount()
except BaseException as e:
    print("Exception ", e)
    sd.umount()
