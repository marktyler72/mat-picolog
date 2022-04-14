# Sensor Display - Main code

from PiicoDev_BME280 import PiicoDev_BME280
from PiicoDev_VL53L1X import PiicoDev_VL53L1X
from PiicoDev_Unified import sleep_ms
import time
import mpy_utils
import sys
import os_path

class Display(object):

    BLACK = 0
    WHITE = 1

    TEMP_LINE = 1
    PRES_LINE = 15
    RH_LINE = 30
    DIST_LINE = 45

    def __init__(self):
        from PiicoDev_SSD1306 import create_PiicoDev_SSD1306
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


class DataLogger():
    _ATMOS_MEAS_INT = 20000 # ms
    _DIST_MEAS_INT = 2000 # ms

    def __init__(self, use_sd=False):
        self.sd = None
        self.led = None
        if use_sd:
            self.config_sd()
            self.errlog = self.create_errlog()
            self.datalog = self.create_datalog()
        else:
            self.errlog = sys.stderr
            self.datalog = sys.stdout

    def config_sd(self):
        import os
        self.sd = mpy_utils.SDVolume()
        self.sd.mount()

        root_dir = '/sd/dl'
        self.log_dir = root_dir + '/logs'
        self.data_dir = root_dir + '/data'
        if not os_path.isdir(root_dir):
            os.mkdir(root_dir)
        if not os_path.isdir(self.log_dir):
            os.mkdir(self.log_dir)
        if not os_path.isdir(self.data_dir):
            os.mkdir(self.data_dir)

    def create_errlog(self):
        log_file = self.log_dir + \
            '/dl_log_{0:4d}-{1:02d}-{2:02d}-{3:02d}{4:02d}{5:02d}.txt'.format(*time.localtime())
        return open(log_file, 'w')

    def create_datalog(self):
        log_file = self.data_dir + \
            '/data_{0:4d}-{1:02d}-{2:02d}.txt'.format(*time.localtime())
        return open(log_file, 'a')

    def log(self, logger, s):
        logger.write(mpy_utils.format_time(time.localtime()) + '| ' + s + '\n')
        try:
            logger.flush()
        except AttributeError:
            pass

    def config_hw(self):
        ready = False
        cnt = 0
        while not ready:
            try:
                self.log(self.errlog, " - Initialising hardware")
                self.led = mpy_utils.Led()
                self.led.on()
                self.atmos_sensor = PiicoDev_BME280()
                # self.dist_sensor = PiicoDev_VL53L1X()
                # self.dist_sensor.distance_mode = 2
                # self.dist_sensor.timing_budget = 200
                self.led.off()

                # self.display = Display()
                # sleep_ms(20)
                # self.display.update()

                ready = True
                self.led.on()

            except Exception as e:
                self.log(self.errlog, "  Error: ",e)
                self.sd = None
                cnt += 1
                if cnt < 5:
                    self.log(self.errlog, "?? Some hardware failed to initialise - will try again.")
                    sleep_ms(1000)
                else:
                    raise RuntimeError("Failed to initialise h/w.")

        if cnt >= 5:
            print("")

    def deinit(self, reason=None):
        msg = " - Shutting down"
        if reason is not None:
            msg = msg + ": " + reason
        self.log(self.errlog, msg)
        if self.sd is not None:
            self.sd.umount()
        if self.led is not None:
            self.led.off()

    def run(self):
        # import gc
        # gc.disable()

        self.log(self.errlog, " - Starting data acquisition.")
        tempC , pres_hPa, humRH, range_mm = (0.0, 0.0, 0.0, 0)

        sleep_time = self._DIST_MEAS_INT
        time_to_next_atmos_measurement = 0
        range_sum = 0
        num_range_samples = 0

        while (True):           

            # range_mm, status = self.dist_sensor.distance
            # if status["ok"]:
            #     range_sum += range_mm
            #     num_range_samples += 1
            # else:
            #     range_mm = None

            if time_to_next_atmos_measurement <= 0:
                self.led.on()

                tempC, presPa, humRH = self.atmos_sensor.values() # read all data from the sensor
                pres_hPa = presPa / 100 

                if num_range_samples > 0:
                    avg_range_str = " {0:5.0f} mm".format(range_sum / num_range_samples)
                else:
                    avg_range_str = " ***** mm"

                self.log(self.datalog, "{0:4.1f} C {1:6.1f} hPa, {2:4.1f} %, {3}".format( \
                        tempC, pres_hPa, humRH, avg_range_str))

                range_sum = 0
                num_range_samples = 0
                time_to_next_atmos_measurement = self._ATMOS_MEAS_INT

                # self.display.update(tempC, pres_hPa, humRH, range_mm)
                self.led.off()

            # gc.collect()
            sleep_ms(sleep_time)
            time_to_next_atmos_measurement -= sleep_time
