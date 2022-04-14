# A MicroPython class for the Core Electronics PiicoDev Atmospheric Sensor BME280
# Ported by Michael Ruppe at Core Electronics
# MAR 2021
# Original repo https://bit.ly/2yJwysL

import struct
from uctypes import INT8
from PiicoDev_Unified import *
from micropython import const

try:
    import typing  # pylint: disable=unused-import
except ImportError:
    pass

compat_str = '\nUnified PiicoDev library out of date.  Get the latest module: https://piico.dev/unified \n'

# Constants and register addresses
_DEFAULT_I2C_ADDR = const(0x77)
_BME_CHIPID = const(0x60)
_BME_RESET_FLAG = const(0xB6)

_REG_CHIPID = const(0xD0)
_REG_RESET = const(0xE0)
_REG_STATUS = const(0xF3)
_REG_CTRL_HUM = const(0xF2)
_REG_CTRL_MEAS = const(0xF4)
_REG_CONFIG = const(0xF5)
_REG_DATA_START = const(0xF7)

_OVERSAMPLING_OFF = const(0x00)
_OVERSAMPLING_x1 = const(0x01)
_OVERSAMPLING_x2 = const(0x02)
_OVERSAMPLING_x4 = const(0x03)
_OVERSAMPLING_x8 = const(0x04)
_OVERSAMPLING_x16 = const(0x05)

# Codes for measurement standby time. Each one is _STANDBY_millisecs_tenths
_STANDBY_0_5 = const(0)
_STANDBY_62_5 = const(1)
_STANDBY_125 = const(2)
_STANDBY_250 = const(3)
_STANDBY_500 = const(4)
_STANDBY_1000 = const(5)
_STANDBY_10 = const(6)
_STANDBY_20 = const(7)

# Codes for number of samples in IIR filter.
_IIR_FILTER_OFF = const(0)
_IIR_FILTER_2 = const(1)
_IIR_FILTER_4 = const(2)
_IIR_FILTER_8 = const(3)
_IIR_FILTER_16 = const(4)

_TEMP = const(0)
_PRES = const(1)
_HUM = const(2)

# Device modes
_DEV_SLEEP = const(0)
_DEV_FORCED = const(1)
_DEV_NORMAL = const(3)

class PiicoDev_BME280:
    def __init__(self, bus=None, freq=None, sda=None, scl=None, \
        temp_oversamp=_OVERSAMPLING_x1, pres_oversamp=_OVERSAMPLING_x1, \
            hum_oversamp=_OVERSAMPLING_x1, iir=_IIR_FILTER_OFF, \
                address=_DEFAULT_I2C_ADDR):
        try:
            if compat_ind >= 1:
                pass
            else:
                print(compat_str)
        except:
            print(compat_str)

        self.addr = address
        self.i2c = create_unified_i2c(bus=bus, freq=freq, sda=sda, scl=scl)

        # Read the ID of the BME280. It should return 0x60
        try:
            chip_ID = self._read8(_REG_CHIPID)
            if chip_ID != _BME_CHIPID:
                print("Chip_ID is 0x{0:2X}, expected 0x{1:2X}".format(chip_ID, _REG_CHIPID))
                raise RuntimeError("BME280 id wrong!")
        except Exception as e:
            print(i2c_err_str.format(self.addr))
            raise e

        # Check the range of values and set some defaults
        self.oversampling = bytearray(3)
        for i, value in enumerate((temp_oversamp, pres_oversamp, hum_oversamp)):
            if (value < _OVERSAMPLING_OFF or value > _OVERSAMPLING_x16):
                value = _OVERSAMPLING_OFF
            self.oversampling[i] = value

        self.iir_filter = iir  # IIR filter mode (0 = off, 1-4 are larger coeffs)
        if self.iir_filter > _IIR_FILTER_16:
            self.iir_filter = _IIR_FILTER_16

        self.sampling_mode = _DEV_FORCED
        self.standby_time = _STANDBY_125 << 5 # A value between 0 and 7 which are the top 3 bits of config. 7 = 20ms
        self._t_fine = 0

        # Configure the device.
        self._reset()
        self._read_coefficients()
        self._set_data_acqn_options()
        self._set_dev_config()
        
    def _reset(self) -> None:
        """Soft reset the sensor"""
        self._write8(_REG_RESET, _BME_RESET_FLAG)
        sleep_ms(3)

    def _read_coefficients(self) -> None:
        """Read & save the calibration coefficients"""
        coeff = self.i2c.readfrom_mem(self.addr, 0x88, 24)  # BME280_REGISTER_DIG_T1
        coeff = list(struct.unpack("<HhhHhhhhhhhh", bytes(coeff)))
        coeff = [int(i) for i in coeff]
        self._temp_calib = coeff[:3]
        self._pressure_calib = coeff[3:]

        self._humidity_calib = [0] * 6
        self._humidity_calib[0] = self._read8(0xA1)  # BME280_REGISTER_DIG_H1
        coeff = self.i2c.readfrom_mem(self.addr, 0xE1, 7)  # BME280_REGISTER_DIG_H2
        coeff = list(struct.unpack("<hBbBbb", bytes(coeff)))
        self._humidity_calib[1] = coeff[0]
        self._humidity_calib[2] = coeff[1]
        self._humidity_calib[3] = (coeff[2] << 4) | (coeff[3] & 0xF)
        self._humidity_calib[4] = (coeff[4] << 4) | (coeff[3] >> 4)
        self._humidity_calib[5] = coeff[5]
        
    def _set_data_acqn_options(self) -> None:
        self._write8(_REG_CTRL_HUM, self.oversampling[_HUM])
        self._write8(_REG_CTRL_MEAS, \
            (self.oversampling[_TEMP] << 5 | self.oversampling[_PRES] << 2 | self.sampling_mode))

    def _set_dev_config(self) -> None:
        if self.sampling_mode == _DEV_NORMAL:
            config_value = self.standby_time << 5
        else:
            config_value = 0
        config_value += self.iir_filter<<2
        self._write8(_REG_CONFIG, config_value)

    def _calc_measurement_time_ms(self) -> float:
        meas_time_ms = 1.25 + 2.3 * (1 << self.oversampling[_TEMP]) \
                            + 2.3 * (1 << self.oversampling[_PRES]) + 0.575 \
                            + 2.3 * (1 << self.oversampling[_HUM]) + 0.575
        return meas_time_ms

    def _is_dev_ready(self) -> bool:
        return bool((self._read8(_REG_STATUS) & 0x08))

    def _read8(self, reg) -> int:
        t = self.i2c.readfrom_mem(self.addr, reg, 1)
        return t[0]

    # def _read16(self, reg) -> int:
    #     t = self.i2c.readfrom_mem(self.addr, reg, 2)
    #     return t[0]+t[1]*256

    def _write8(self, reg: int, dat: int) -> None:
        self.i2c.write8(self.addr, bytes([reg]), bytes([dat]))

    # def _short(self, dat) -> int:
    #     if dat > 32767:
    #         return dat - 65536
    #     else:
    #         return dat

    def read_raw_data(self):
        '''Set data acquisition options and read the raw ADC values'''
        self._set_data_acqn_options()
        max_wait = self._calc_measurement_time_ms()
        spins = 0
        while not self._is_dev_ready():
            spins += 1
            sleep_ms(2)

        data = self.i2c.readfrom_mem(self.addr, _REG_DATA_START, 8)
        data = list(struct.unpack("<8B", bytes(data)))
          
        raw_p = ((data[0]<<16)|(data[1]<<8)|data[2])>>4
        raw_t = ((data[3]<<16)|(data[4]<<8)|data[5])>>4
        raw_h = (data[6] << 8)| data[7]

        return (raw_t, raw_p, raw_h)

    def read_compensated_data(self):
        '''Read the raw data and apply the compensation factors'''
        try:
            raw_t, raw_p, raw_h = self.read_raw_data()
        except:
            print(i2c_err_str.format(self.addr))
            return (float('NaN'), float('NaN'), float('NaN'))

        # Temperature calculation
        var1 = ((raw_t>>3)-(self._temp_calib[0]<<1))*(self._temp_calib[1]>>11)
        var2 = (raw_t >> 4)-self._temp_calib[0]
        var2 = var2*((raw_t>>4)-self._temp_calib[0])
        var2 = ((var2>>12)*self._temp_calib[2])>>14
        self._t_fine = var1+var2
        temp = (self._t_fine*5+128)>>8

        # Pressure calculation
        var1 = self._t_fine-128000
        var2 = var1*var1*self._pressure_calib[5]
        var2 = var2 + ((var1*self._pressure_calib[4])<<17)
        var2 = var2 + (self._pressure_calib[3]<<35)
        var1 = (((var1*var1*self._pressure_calib[2])>>8) 
                + ((var1*self._pressure_calib[1])<<12))
        var1 = (((1<<47) + var1)*self._pressure_calib[0])>>33
        if var1 == 0:
            pres = 0
        else:
            p = ((((1048576-raw_p)<<31)-var2)*3125)//var1
            var1 = (self._pressure_calib[8]*(p>>13)*(p>>13))>>25
            var2 = (self._pressure_calib[7]*p)>>19
            pres = ((p + var1 + var2)>>8) + (self._pressure_calib[6]<<4)

        # Humidity calculation
        h = self._t_fine-76800
        h1 = ((((raw_h<<14) - (self._humidity_calib[3]<<20)
                - (self._humidity_calib[4]*h)) + 16384)>>15)
              
        h2 = (((((((h*self._humidity_calib[5])>>10)
                * (((h*self._humidity_calib[2])>>11) + 32768))>>10)
                    + 2097152)*self._humidity_calib[1] + 8192)>>14)
        h = (h1 * h2)
        h = h - (((((h>>15)*(h>>15))>>7)*self._humidity_calib[0])>>4)
        h = 0 if h < 0 else h
        h = 419430400 if h>419430400 else h
        humi = h>>12

        return (temp, pres, humi)

    def values(self):
        '''Read the values from the BME280 and return the values in deg C, bars and %RH'''
        temp, pres, humi = self.read_compensated_data()
        return (temp/100, pres/256,  humi/1024)

    def pressure_precision(self):
        p = self.read_compensated_data()[1]
        pi = float(p // 256)
        pd = (p % 256)/256
        return (pi, pd)

    def altitude(self, pressure_sea_level=1013.25):
        pi, pd = self.pressure_precision()
        return 44330*(1-((float(pi+pd)/100)/pressure_sea_level)**(1/5.255))
