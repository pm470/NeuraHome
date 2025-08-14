from neurahome_fhir.config import Config
from neurahome_fhir.runner import SerialRunner

def main():
    cfg = Config(
        serial_port="/dev/ttyACM0",
        baud=115200,
        post_every_seconds=10,
        url="https://httpbin.org/post",
        patient_id="Patient/example"  # or None
    )
    SerialRunner(cfg).run()

if __name__ == "__main__":
    main()
