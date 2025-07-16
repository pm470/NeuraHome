import time
from BioSensorHub import BioSensorHub, MODE_ONE, MODE_TWO, SFE_BIO_SUCCESS

def main():
    print("Initializing I2C and BioSensorHub...")

    # Initialize sensor with specified I2C bus and GPIO pins
    bio_hub = BioSensorHub(bus_id=1, reset_pin=4, mfio_pin=13)

    # Start communication with sensor
    result = bio_hub.begin()
    if result == 0:
        print("Sensor started!")
    else:
        print("❌ Could not communicate with the sensor. Exiting.")
        return

    print("Configuring sensor for BPM mode...")
    error = bio_hub.config_bpm(MODE_ONE)
    if error == SFE_BIO_SUCCESS:
        print("✅ Sensor configured.")
    else:
        print("❌ Error configuring sensor.")
        print("Error code:", error)
        return

    print("Waiting for data to become available...")
    time.sleep(2)

    output_mode = bio_hub.read_byte(0x10, 0x00)
    print("Output mode is:", hex(output_mode))

    max30101_enabled = bio_hub.read_byte(0x44, 0x03)
    print("MAX30101 enabled?:", hex(max30101_enabled))

    whrm_mode = bio_hub.read_byte(0x52, 0x02)
    print("WHRM mode is:", hex(whrm_mode))

    print("\nStarting continuous read loop:\n")
    while True:
        body = bio_hub.read_bpm()

        print(f"Heart Rate  : {body.heart_rate} bpm")
        print(f"Confidence  : {body.confidence} %")
        print(f"SpO₂        : {body.oxygen} %")
        print(f"Status      : {body.status}")
        print("-" * 30)

        time.sleep(1.5)

if __name__ == "__main__":
    main()
