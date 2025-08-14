import time
import logging
import serial

from .config import Config
from .utils import setup_logging
from .parser import SensorParser
from .aggregator import Aggregator
from .fhir import FHIRBuilder
from .client import FHIRClient

class SerialRunner:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.parser = SensorParser()
        self.agg = Aggregator()
        self.fhir_builder = FHIRBuilder()
        self.client = FHIRClient(cfg.url, cfg.headers)

        # Independent timers for each measurement type
        now = time.time()
        self.last_sent_hr = now
        self.last_sent_spo2 = now
        self.last_sent_env = now - (15 * 60)  # so first loop sends immediately

    def run(self) -> None:
        setup_logging(logging.INFO)
        logging.info("Opening serial %s @ %d …", self.cfg.serial_port, self.cfg.baud)

        with serial.Serial(self.cfg.serial_port, self.cfg.baud, timeout=1) as ser:
            time.sleep(2)
            logging.info("Listening to sensor device…")

            try:
                while True:
                    # Read one line from serial
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        reading = self.parser.parse(line)
                        if reading:
                            self.agg.add(reading)

                    now = time.time()

                    # 1️⃣ Send Heart Rate every 1s
                    if now - self.last_sent_hr >= 1:
                        avg_hr = self.agg.snapshot().get("hr")
                        if avg_hr is not None:
                            obs = self.fhir_builder.build_observations({"hr": avg_hr}, self.cfg.patient_id)
                            bundle = self.fhir_builder.bundle(obs)
                            if bundle:
                                self.client.post_bundle(bundle)
                        self.agg._hr.clear()
                        self.last_sent_hr = now

                    # 2️⃣ Send SpO₂ every 5s
                    if now - self.last_sent_spo2 >= 5:
                        avg_spo2 = self.agg.snapshot().get("spo2")
                        if avg_spo2 is not None:
                            obs = self.fhir_builder.build_observations({"spo2": avg_spo2}, self.cfg.patient_id)
                            bundle = self.fhir_builder.bundle(obs)
                            if bundle:
                                self.client.post_bundle(bundle)
                        self.agg._spo2.clear()
                        self.last_sent_spo2 = now

                    # 3️⃣ Send Temp + Humidity every 15 min (and at start)
                    if now - self.last_sent_env >= 15 * 60:
                        avg_temp = self.agg.snapshot().get("temp")
                        avg_hum = self.agg.snapshot().get("hum")
                        if avg_temp is not None or avg_hum is not None:
                            obs = self.fhir_builder.build_observations(
                                {"temp": avg_temp, "hum": avg_hum}, self.cfg.patient_id
                            )
                            bundle = self.fhir_builder.bundle(obs)
                            if bundle:
                                self.client.post_bundle(bundle)
                        self.agg._temp.clear()
                        self.agg._hum.clear()
                        self.last_sent_env = now

            except KeyboardInterrupt:
                logging.info("Stopped by user")
