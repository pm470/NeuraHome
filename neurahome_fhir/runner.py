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

    def run(self) -> None:
        setup_logging(logging.INFO)
        logging.info("Opening serial %s @ %d …", self.cfg.serial_port, self.cfg.baud)

        with serial.Serial(self.cfg.serial_port, self.cfg.baud, timeout=1) as ser:
            time.sleep(2)  # let the port settle
            logging.info("Listening to sensor device…")
            window_start = time.time()

            try:
                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        reading = self.parser.parse(line)
                        if reading:
                            self.agg.add(reading)

                    if time.time() - window_start >= self.cfg.post_every_seconds:
                        snapshot = self.agg.snapshot()
                        observations = self.fhir_builder.build_observations(snapshot, self.cfg.patient_id)
                        if observations:
                            bundle = self.fhir_builder.bundle(observations)
                            if bundle:
                                try:
                                    self.client.post_bundle(bundle)
                                except Exception as e:
                                    logging.error("Post failed: %s", e)
                        else:
                            logging.info("No valid averages this interval.")
                        self.agg.reset()
                        window_start = time.time()
            except KeyboardInterrupt:
                logging.info("Stopped by user")
