import struct
from PiicoDev_Unified import *
from micropython import const

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

# Constants and register addresses
_DEFAULT_I2C_ADDR = const(0x29)
_VL53L1X_CHIPID = const(0xEACC)

_REG_RESET = const(0x0000)
_REG_I2C_ADDRESS = const(0x0001)
_REG_VHV_TIMEOUT_MACROP_LOOP_BOUND = const(0x0008)
_REG_CONFIGURE = const(0x002D)
_REG_GPIO_HV_MUX_CTRL = const(0x0030)
_REG_GPIO_TIO_HV_STATUS = const(0x0031)

_REG_PHASECAL_CONFIG__TIMEOUT_MACROP = const(0x004B)
_REG_RANGE_CONFIG__TIMEOUT_MACROP_A_HI = const(0x005E)
_REG_RANGE_CONFIG__VCSEL_PERIOD_A = const(0x0060)
_REG_RANGE_CONFIG__TIMEOUT_MACROP_B_HI = const(0x0061)
_REG_RANGE_CONFIG__VCSEL_PERIOD_B = const(0x0063)
_REG_RANGE_CONFIG__VALID_PHASE_HIGH = const(0x0069)
_REG_SD_CONFIG__WOI_SD0 = const(0x0078)
_REG_SD_CONFIG__INITIAL_PHASE_SD0 = const(0x007A)

_REG_SYSTEM_INTERRUPT_CLEAR = const(0x0086)
_REG_RANGE_START = const(0x0087)
_REG_RANGE_STATUS = const(0x0089)
_REG_SYSTEM_STATUS = const(0x00E5)
_REG_CHIPID = const(0x010F)

# Timing budget values for short and long distance ranging
TB_SHORT_DIST = {
    # ms: (MACROP_A_HI, MACROP_B_HI)
    15: (0x001D, 0x0027),
    20: (0x0051, 0x006E),
    33: (0x00D6, 0x006E),
    50: (0x01AE, 0x01E8),
    100: (0x02E1, 0x0388),
    200: (0x03E1, 0x0496),
    500: (0x0591, 0x05C1),
}

TB_LONG_DIST = {
    # ms: (MACROP_A_HI, MACROP_B_HI)
    20: (0x001E, 0x0022),
    33: (0x0060, 0x006E),
    50: (0x00AD, 0x00C6),
    100: (0x01CC, 0x01EA),
    200: (0x02D9, 0x02F8),
    500: (0x048F, 0x04A4),
}

VL51L1X_DEFAULT_CONFIGURATION = bytes([
0x00, # 0x2d : set bit 2 and 5 to 1 for fast plus mode (1MHz I2C), else don't touch
0x00, # 0x2e : bit 0 if I2C pulled up at 1.8V, else set bit 0 to 1 (pull up at AVDD)
0x00, # 0x2f : bit 0 if GPIO pulled up at 1.8V, else set bit 0 to 1 (pull up at AVDD)
0x01, # 0x30 : GPIO_HV_MUX_CTRL: set bit 4 to 0 for active high interrupt and 1 for active low (bits 3:0 must be 0x1), use SetInterruptPolarity()
0x02, # 0x31 : GPIO_TIO_HV_STATUS: bit 1 = interrupt depending on the polarity, use self._data_ready()
0x00, # 0x32 : not user-modifiable (NUM)
0x02, # 0x33 : NUM
0x08, # 0x34 : NUM
0x00, # 0x35 : NUM
0x08, # 0x36 : NUM
0x10, # 0x37 : NUM
0x01, # 0x38 : NUM
0x01, # 0x39 : NUM
0x00, # 0x3a : NUM
0x00, # 0x3b : NUM
0x00, # 0x3c : NUM
0x00, # 0x3d : NUM
0xff, # 0x3e : NUM
0x00, # 0x3f : NUM
0x0f, # 0x40 : NUM
0x00, # 0x41 : NUM
0x00, # 0x42 : NUM
0x00, # 0x43 : NUM
0x00, # 0x44 : NUM
0x00, # 0x45 : NUM
0x20, # 0x46 : interrupt configuration 0->level low detection, 1-> level high, 2-> Out of window, 3->In window, 0x20-> New sample ready , TBC
0x0b, # 0x47 : NUM
0x00, # 0x48 : NUM
0x00, # 0x49 : NUM
0x02, # 0x4a : NUM
0x0a, # 0x4b : PHASECAL_TIMEOUT_MACROP
0x21, # 0x4c : NUM
0x00, # 0x4d : NUM
0x00, # 0x4e : NUM
0x05, # 0x4f : NUM
0x00, # 0x50 : NUM
0x00, # 0x51 : NUM
0x00, # 0x52 : NUM
0x00, # 0x53 : NUM
0xc8, # 0x54 : NUM
0x00, # 0x55 : NUM
0x00, # 0x56 : NUM
0x38, # 0x57 : NUM
0xff, # 0x58 : NUM
0x01, # 0x59 : NUM
0x00, # 0x5a : NUM
0x08, # 0x5b : NUM
0x00, # 0x5c : NUM
0x00, # 0x5d : NUM
0x01, # 0x5e : TIMEOUT_MACROP_A_HI
0xcc, # 0x5f : 
0x0f, # 0x60 : VCSEL_PERIOD_A
0x01, # 0x61 : TIMEOUT_MACROP_B_HI
0xf1, # 0x62 : 
0x0d, # 0x63 : VCSEL_PERIOD_B
0x01, # 0x64 : Sigma threshold MSB (mm in 14.2 format for MSB+LSB), use SetSigmaThreshold(), default value 90 mm 
0x68, # 0x65 : Sigma threshold LSB
0x00, # 0x66 : Min count Rate MSB (MCPS in 9.7 format for MSB+LSB), use SetSignalThreshold()
0x80, # 0x67 : Min count Rate LSB
0x08, # 0x68 : NUM
0xb8, # 0x69 : NUM
0x00, # 0x6a : NUM
0x00, # 0x6b : NUM
0x00, # 0x6c : Intermeasurement period MSB, 32 bits register, use SetIntermeasurementInMs()
0x00, # 0x6d : Intermeasurement period
0x0f, # 0x6e : Intermeasurement period
0x89, # 0x6f : Intermeasurement period LSB
0x00, # 0x70 : NUM
0x00, # 0x71 : NUM
0x00, # 0x72 : distance threshold high MSB (in mm, MSB+LSB), use SetD:tanceThreshold()
0x00, # 0x73 : distance threshold high LSB
0x00, # 0x74 : distance threshold low MSB ( in mm, MSB+LSB), use SetD:tanceThreshold()
0x00, # 0x75 : distance threshold low LSB
0x00, # 0x76 : NUM
0x01, # 0x77 : NUM
0x0f, # 0x78 : NUM
0x0d, # 0x79 : NUM
0x0e, # 0x7a : NUM
0x0e, # 0x7b : NUM
0x00, # 0x7c : NUM
0x00, # 0x7d : NUM
0x02, # 0x7e : NUM
0xc7, # 0x7f : ROI center, use SetROI()
0xff, # 0x80 : XY ROI (X=Width, Y=Height), use SetROI()
0x9b, # 0x81 : NUM
0x00, # 0x82 : NUM
0x00, # 0x83 : NUM
0x00, # 0x84 : NUM
0x01, # 0x85 : NUM
0x01, # 0x86 : clear interrupt, use ClearInterrupt()
0x00  # 0x87 : start ranging, use StartRanging() or StopRanging(), If you want an automatic start after VL53L1X_init() call, put 0x40 in location 0x87
])


class PiicoDev_VL53L1X:
    def __init__(self, bus=None, freq=None, sda=None, scl=None, address=_DEFAULT_I2C_ADDR):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)
        self.addr = address
        self._timing_budget = 200

        self._reset()
        if self._read_model_id() != _VL53L1X_CHIPID:
            raise RuntimeError('Failed to find expected ID register values. Check wiring!')

        # Wait for the chip to boot
        while self._boot_state() == 0:
            sleep_ms(2)

        # Initialise the sensor and set default ranging parameters
        self._sensor_init()
        self.distance_mode = 2
        self.timing_budget = 100
        self._start_ranging()

    def _reset(self):
        """Perform a soft reset"""
        self.writeReg(_REG_RESET, 0x00)
        sleep_ms(100)
        self.writeReg(_REG_RESET, 0x01)
        sleep_ms(1)

    def _boot_state(self):
        return self.readReg(_REG_SYSTEM_STATUS)

    def _sensor_init(self):
        """Initialise the sensor and make the first measurement"""
        # write default configuration
        self.i2c.writeto_mem(self.addr, _REG_CONFIGURE, VL51L1X_DEFAULT_CONFIGURATION, addrsize=16)

        self._start_ranging()
        while not self._data_ready():
            sleep_ms(100)
        self._clear_interrupt()
        self._stop_ranging()
        self.writeReg(_REG_VHV_TIMEOUT_MACROP_LOOP_BOUND, 0x09)
        self.writeReg(0x0B, 0x00)

    @property
    def distance_mode(self):
        '''Distance mode. 1=short, 2=long.'''
        reg_val = self.readReg(_REG_PHASECAL_CONFIG__TIMEOUT_MACROP)
        if reg_val == 0x14:
            mode = 1    # short
        elif reg_val == 0x0A:
            mode = 2    # long
        else:
            mode = None
        return mode

    @distance_mode.setter
    def distance_mode(self, mode):
        if mode == 1:   
            # short distance
            self.writeReg(_REG_PHASECAL_CONFIG__TIMEOUT_MACROP, 0x14)
            self.writeReg(_REG_RANGE_CONFIG__VCSEL_PERIOD_A, 0x07)
            self.writeReg(_REG_RANGE_CONFIG__VCSEL_PERIOD_B, 0x05)
            self.writeReg(_REG_RANGE_CONFIG__VALID_PHASE_HIGH, 0x38)
            self.writeReg16Bit(_REG_SD_CONFIG__WOI_SD0, 0x0705)
            self.writeReg16Bit(_REG_SD_CONFIG__INITIAL_PHASE_SD0, 0x0606)
        elif mode == 2:
            # long distance
            self.writeReg(_REG_PHASECAL_CONFIG__TIMEOUT_MACROP, 0x0A)
            self.writeReg(_REG_RANGE_CONFIG__VCSEL_PERIOD_A, 0x0F)
            self.writeReg(_REG_RANGE_CONFIG__VCSEL_PERIOD_B, 0x0D)
            self.writeReg(_REG_RANGE_CONFIG__VALID_PHASE_HIGH, 0xB8)
            self.writeReg16Bit(_REG_SD_CONFIG__WOI_SD0, 0x0F0D)
            self.writeReg16Bit(_REG_SD_CONFIG__INITIAL_PHASE_SD0, 0x0E0E)
        else:
            raise ValueError("Unsupported distance mode")
        self.timing_budget = self._timing_budget

    @property
    def timing_budget(self):
        '''Timing budget in milliseconds. Values can be ms = 15 (short mode only), 20, 33, 50, 100, 200, 500.'''
        return self._timing_budget

    @timing_budget.setter
    def timing_budget(self, budget_ms):
        dist_mode = self.distance_mode
        if dist_mode is not None:
            if dist_mode == 1:
                reg_vals = TB_SHORT_DIST
            else:
                reg_vals = TB_LONG_DIST
        else:
            raise RuntimeError("Unknown distance mode.")

        if budget_ms not in reg_vals.keys():
            raise ValueError("Invalid timing budget.")
        self.writeReg16Bit(_REG_RANGE_CONFIG__TIMEOUT_MACROP_A_HI, reg_vals[budget_ms][0])
        self.writeReg16Bit(_REG_RANGE_CONFIG__TIMEOUT_MACROP_B_HI, reg_vals[budget_ms][1])
        self._timing_budget = budget_ms

    def _start_ranging(self):
        """Starts ranging operation."""
        self.writeReg(_REG_RANGE_START, 0x40)

    def _stop_ranging(self):
        """Stops ranging operation."""
        self.writeReg(_REG_RANGE_START, 0x00)

    def _clear_interrupt(self):
        """Clears new data interrupt."""
        self.writeReg(_REG_SYSTEM_INTERRUPT_CLEAR, 0x01)

    def _data_ready(self):
        """Returns true if new data is ready, otherwise false."""
        if (self.readReg(_REG_GPIO_TIO_HV_STATUS) & 0x01
                == self._interrupt_polarity):
            return True
        return False

    @property
    def _interrupt_polarity(self):
        int_pol = self.readReg(_REG_GPIO_HV_MUX_CTRL) & 0x10
        int_pol = (int_pol >> 4) & 0x01
        return 0 if int_pol else 1

    def writeReg(self, reg, value):
        return self.i2c.writeto_mem(self.addr, reg, bytes([value]), addrsize=16)
    def writeReg16Bit(self, reg, value):
        return self.i2c.writeto_mem(self.addr, reg, bytes([(value >> 8) & 0xFF, value & 0xFF]), addrsize=16)
    def readReg(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1, addrsize=16)[0]
    def readReg16Bit(self, reg):
        data = self.i2c.readfrom_mem(self.addr, reg, 2, addrsize=16)
        return (data[0]<<8) + data[1]

    def _read_model_id(self):
        return self.readReg16Bit(_REG_CHIPID) 

    @property
    def distance(self):
        '''Reads the distance (in mm) from the sensor and returns the value and status.'''
        while not self._data_ready():
            sleep_ms(1)

        status = {"ok": False, "reason": ""}

        try:
            data = self.i2c.readfrom_mem(self.addr, _REG_RANGE_STATUS, 17, addrsize=16)

            range_status, report_status, stream_count, num_SPADs, \
                peak_count, ambient_count, t2, t3, range_mm, corr_signal = \
                struct.unpack(">BBBHHHHHHH", data)

            if range_status in (17, 2, 1, 3):
                status["reason"] = "HardwareFail"
            elif range_status == 13:
                status["reason"] = "MinRangeFail"
            elif range_status == 18:
                status["reason"] = "SynchronizationInt"
            elif range_status == 5:
                status["reason"] = "OutOfBoundsFail"
            elif range_status == 4:
                status["reason"] = "SignalFail"
            elif range_status == 6:
                status["reason"] = "SignalFail"
            elif range_status == 7:
                status["reason"] = "WrapTargetFail"
            elif range_status == 12:
                status["reason"] = "XtalkSignalFail"
            elif range_status == 8:
                status["reason"] = "RangeValidMinRangeClipped"
            elif range_status == 9:
                status["ok"] = True
                if stream_count == 0:
                    status["reason"] = "RangeValidNoWrapCheckFail"
                else:
                    status["reason"] = "OK"

        except:
            status["reason"] = i2c_err_str.format(self.addr)
            range_mm = -1

        self._clear_interrupt()

        return range_mm, status

    def change_id(self, new_id):
        self.writeReg(_REG_I2C_ADDRESS, new_id & 0x7F)
        sleep_ms(50)
        self.addr = new_id
