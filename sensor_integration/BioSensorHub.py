import time
import smbus2
import lgpio
from smbus2 import i2c_msg

# Constants from header
BIO_ADDRESS = 0x55
READ_DEVICE_MODE = 0x02
READ_DATA_OUTPUT = 0x12
READ_DATA = 0x01
ALGO_DATA = 0x02
MODE_ONE = 0x01
MODE_TWO = 0x02
SFE_BIO_SUCCESS = 0x00
INCORR_PARAM = 0xEE
MAXFAST_ARRAY_SIZE = 6
MAXFAST_EXTENDED_DATA = 5
SENSOR_DATA = 0x01
SET_FORMAT = 0x00
WRITE_SET_THRESHOLD = 0x01
OUTPUT_MODE = 0x10
ENABLE_SENSOR = 0x44
ENABLE_MAX30101 = 0x03
ENABLE_ALGORITHM = 0x52
ENABLE_AGC_ALGO = 0x00
ENABLE_WHRM_ALGO = 0x02
NUM_SAMPLES = 0x00
CHANGE_ALGORITHM_CONFIG = 0x50
SET_PULSE_OX_COEF = 0x02
MAXIMFAST_COEF_ID = 0x0B
READ_ALGORITHM_CONFIG = 0x51
READ_AGC_NUM_SAMPLES = 0x00
READ_AGC_NUM_SAMPLES_ID = 0x03
ENABLE = 0x01
DISABLE = 0x00


# Dummy GPIO abstraction (replace with actual GPIO library in real usage)
class GPIO:
    OUT = 1
    IN = 0
    PUD_UP = 2
    HIGH = 1
    LOW = 0

    @staticmethod
    def setup(pin, mode, pull_up_down=None):
        lgpio.gpio_claim_output(pin)

    @staticmethod
    def output(pin, value):
        pass  # Replace with actual GPIO write

    @staticmethod
    def input(pin):
        return 0  # Stub


class BioData:
    def __init__(self):
        self.ir_led = 0
        self.red_led = 0
        self.heart_rate = 0
        self.confidence = 0
        self.oxygen = 0
        self.status = 0
        self.r_value = 0.0
        self.ext_status = 0


class BioSensorHub:
    def __init__(self, bus_id=1, reset_pin=4, mfio_pin=13):
        self.bus = smbus2.SMBus(bus_id)
        self.address = BIO_ADDRESS
        self.gpio = lgpio.gpiochip_open(0)

        self.reset_pin = reset_pin
        self.mfio_pin = mfio_pin

        self.user_selected_mode = None

        lgpio.gpio_claim_output(self.gpio, self.reset_pin)
        lgpio.gpio_claim_output(self.gpio, self.mfio_pin)

        self.bpm_arr = [0] * MAXFAST_ARRAY_SIZE
        self.bpm_arr_two = [0] * (MAXFAST_ARRAY_SIZE + MAXFAST_EXTENDED_DATA)

    def begin(self):
        print("begin")
        lgpio.gpio_write(self.gpio, self.mfio_pin, 0)
        lgpio.gpio_write(self.gpio, self.reset_pin, 0)
        time.sleep(0.1)
        lgpio.gpio_write(self.gpio, self.reset_pin, 1)
        time.sleep(0.5)

        time.sleep(1)

        mode = self.read_byte(READ_DEVICE_MODE, 0x00)
        print("Sensor mode after boot:", hex(mode))
        if mode == 0x02:
            self.write_bytes(0x01, 0x00, [0x00])
            time.sleep(1)
        return mode

    def read_byte(self, family, index, write_byte=None):
        write_data = [family, index] if write_byte is None else [family, index, write_byte]
        self.bus.write_i2c_block_data(self.address, family, write_data[1:])
        time.sleep(0.05)
        return self.bus.read_byte(self.address)

    def read_sensor_hub_status(self):
        return self.read_byte(0x00, 0x00)

    def read_fill_array(self, family, index, num_bytes, buffer):
        self.bus.write_i2c_block_data(self.address, 0x00, [family, index])
        print("writing on bus")
        time.sleep(1)
        data = self.bus.read_i2c_block_data(self.address, 0x00, num_bytes)
        print("reading from bus")
        for i in range(num_bytes):
            buffer[i] = data[i]

    def read_bpm(self):
        bpm = BioData()

        status = self.read_sensor_hub_status()
        print("Sensor hub status:", status)
        if status == 1:
            print("⚠️ Communication error detected in status.")
            return bpm

        samples = self.num_samples_out_fifo()
        print("🧪 Samples in FIFO:", samples)

        if samples == 0:
            print("No data available in FIFO yet.")
            return bpm  # Exit early!

        if self.user_selected_mode == MODE_ONE:
            self.read_fill_array(READ_DATA_OUTPUT, READ_DATA, MAXFAST_ARRAY_SIZE, self.bpm_arr)
            bpm.heart_rate = ((self.bpm_arr[0] << 8) | self.bpm_arr[1]) // 10
            bpm.confidence = self.bpm_arr[2]
            bpm.oxygen = ((self.bpm_arr[3] << 8) | self.bpm_arr[4]) // 10
            bpm.status = self.bpm_arr[5]
        elif self.user_selected_mode == MODE_TWO:
            print("Reading extended data...")
            self.read_fill_array(READ_DATA_OUTPUT, READ_DATA, MAXFAST_ARRAY_SIZE + MAXFAST_EXTENDED_DATA, self.bpm_arr_two)
            bpm.heart_rate = ((self.bpm_arr_two[0] << 8) | self.bpm_arr_two[1]) // 10
            bpm.confidence = self.bpm_arr_two[2]
            bpm.oxygen = ((self.bpm_arr_two[3] << 8) | self.bpm_arr_two[4]) / 10.0
            bpm.status = self.bpm_arr_two[5]
            bpm.r_value = ((self.bpm_arr_two[6] << 8) | self.bpm_arr_two[7]) / 10.0
            bpm.ext_status = self.bpm_arr_two[8]

            return bpm


    def config_bpm(self, mode):
        if mode not in [MODE_ONE, MODE_TWO]:
            print("❌ Invalid mode provided:", mode)
            return INCORR_PARAM

        print("🛠️ Setting output mode to ALGO_DATA...")
        result = self.set_output_mode(ALGO_DATA)
        print("➡️ set_output_mode() returned:", result)
        print("✅ Output mode now:", hex(self.read_byte(OUTPUT_MODE, SET_FORMAT)))
        if result != SFE_BIO_SUCCESS:
            return result

        print("🛠️ Setting FIFO threshold to 1...")
        result = self.set_fifo_threshold(0x01)
        print("➡️ set_fifo_threshold() returned:", result)
        if result != SFE_BIO_SUCCESS:
            return result

        print("🛠️ Enabling AGC algorithm...")
        result = self.agc_algo_control(ENABLE)
        print("➡️ agc_algo_control(ENABLE) returned:", result)
        if result != SFE_BIO_SUCCESS:
            return result

        print("🛠️ Enabling MAX30101 sensor...")
        result = self.max30101_control(ENABLE)
        print("➡️ max30101_control(ENABLE) returned:", result)
        print("✅ MAX30101 status:", hex(self.read_byte(ENABLE_SENSOR, ENABLE_MAX30101)))
        if result != SFE_BIO_SUCCESS:
            return result

        print("🛠️ Enabling WHRM (Maxim Fast) algorithm in mode", mode, "...")
        result = self.maxim_fast_algo_control(mode)
        print("➡️ maxim_fast_algo_control() returned:", result)
        if result != SFE_BIO_SUCCESS:
            return result

        self.user_selected_mode = mode

        print("📈 Reading algorithm sample rate...")
        self.sample_rate = self.read_algo_samples()
        print("✅ Algorithm sample rate:", self.sample_rate)

        time.sleep(5)
        print("✅ Sensor configuration complete.")
        return SFE_BIO_SUCCESS

    def config_sensor(self):
        status = self.set_output_mode(SENSOR_DATA)
        if status != SFE_BIO_SUCCESS:
            return status

        status = self.set_fifo_threshold(0x01)
        if status != SFE_BIO_SUCCESS:
            return status

        status = self.max30101_control(ENABLE)
        if status != SFE_BIO_SUCCESS:
            return status

        status = self.maxim_fast_algo_control(MODE_ONE)
        if status != SFE_BIO_SUCCESS:
            return status

        time.sleep(1.0)
        return SFE_BIO_SUCCESS

    def set_output_mode(self, mode):
        if mode > 0x07:
            return INCORR_PARAM
        return self.write_byte(OUTPUT_MODE, SET_FORMAT, mode)

    def set_fifo_threshold(self, threshold):
        return self.write_byte(OUTPUT_MODE, WRITE_SET_THRESHOLD, threshold)

    def agc_algo_control(self, enable):
        if enable not in [ENABLE, DISABLE]:
            return INCORR_PARAM
        return self.write_byte(ENABLE_ALGORITHM, ENABLE_AGC_ALGO, enable)

    def max30101_control(self, enable):
        if enable not in [ENABLE, DISABLE]:
            return INCORR_PARAM
        return self.write_byte(ENABLE_SENSOR, ENABLE_MAX30101, enable)

    def maxim_fast_algo_control(self, mode):
        if mode not in [MODE_ONE, MODE_TWO]:
            return INCORR_PARAM
        return self.write_byte(ENABLE_ALGORITHM, ENABLE_WHRM_ALGO, mode)

    def read_algo_samples(self):
        return self.read_byte(READ_ALGORITHM_CONFIG, READ_AGC_NUM_SAMPLES, READ_AGC_NUM_SAMPLES_ID)

    def num_samples_out_fifo(self):
        return self.read_byte(READ_DATA_OUTPUT, NUM_SAMPLES)

    from smbus2 import i2c_msg

    def write_byte(self, family, index, value):
        try:
            data = [family, index, value]
            write = i2c_msg.write(self.address, data)
            self.bus.i2c_rdwr(write)
            time.sleep(0.05)

            # Read back 1 byte
            read = i2c_msg.read(self.address, 1)
            self.bus.i2c_rdwr(read)
            data = list(read)
            print("write_byte read return val:", data)
            return list(read)[0]
        except Exception as e:
            print(f"Write error: {e}")
            return 0xFF

