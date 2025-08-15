# NeuraHome FHIR Serial Bridge

**NeuraHome FHIR Serial Bridge** is a Python application that reads sensor data (Heart Rate, SpO₂, Ambient Temperature, and Humidity) from a serial-connected device (e.g., Arduino/embedded board) and sends them to a server in **FHIR Observation** format.

## Features

- **Serial data parsing** for:
  - Heart Rate (HR) — sent every **1 second**
  - Oxygen Saturation (SpO₂) — sent every **5 seconds**
  - Ambient Temperature — sent **once at startup** and then every **15 minutes**
  - Relative Humidity — sent **once at startup** and then every **15 minutes**
- **FHIR-compliant JSON** output
- Configurable **server URL**, **API key**, and **patient ID**
- Modular code structure for easy maintenance
- Detailed logging with adjustable verbosity

---

## Project Structure

```
neurahome_fhir/
├─ neurahome_fhir/
│  ├─ __init__.py
│  ├─ config.py         # Configuration dataclass
│  ├─ utils.py          # Helper functions (logging, timestamps)
│  ├─ parser.py         # Serial line → measurement parsing
│  ├─ aggregator.py     # Buffers and averages values
│  ├─ fhir.py           # Builds FHIR Observations and Bundles
│  ├─ client.py         # Sends HTTP POST requests
│  ├─ runner.py         # Main loop logic & scheduling
├─ main.py              # Entry point
├─ requirements.txt     # Python dependencies
└─ README.md            # This file
```
## Configuration

Edit `main.py` to set your desired **serial port**, **baud rate**, **server URL**, and **patient ID**:

```python
from neurahome_fhir.config import Config
from neurahome_fhir.runner import SerialRunner

def main():
    cfg = Config(
        serial_port="/dev/ttyACM0",  # Change to your device
        baud=115200,
        post_every_seconds=10,       # Not used for individual sensors, see runner
        url="https://your-fhir-server.com/api",
        patient_id="Patient/example"
    )
    SerialRunner(cfg).run()

if __name__ == "__main__":
    main()
```

## Running

```bash
python3 main.py
```

The script will:
- Continuously read from the serial device
- Post HR every **1s**
- Post SpO₂ every **5s**
- Post Ambient Temp & Humidity every **15min** (and once at start)
- Send all measurements in **FHIR Observation** format to your configured server

---

## Requirements

- Python **3.8+**
- A serial-connected device sending lines like:
  ```
  Heartrate: 72
  Oxygen: 98
  Temperature: 24.3 °C
  Humidity: 43.1 %
  ```
- Network access to send HTTP POST requests

---

## Sample JSON post:
```bash
{
  "resourceType": "Bundle",
  "type": "collection",
  "timestamp": "2025-08-15T22:41:05+00:00",
  "entry": [
    {
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "8867-4",
              "display": "Heart rate"
            }
          ],
          "text": "Heart rate"
        },
        "effectiveDateTime": "2025-08-15T22:41:05+00:00",
        "valueQuantity": {
          "value": 72,
          "unit": "beats/minute",
          "system": "http://unitsofmeasure.org",
          "code": "/min"
        },
        "subject": {
          "reference": "Patient/example"
        }
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "59408-5",
              "display": "Oxygen saturation in Arterial blood by Pulse oximetry"
            }
          ],
          "text": "Oxygen saturation in Arterial blood by Pulse oximetry"
        },
        "effectiveDateTime": "2025-08-15T22:41:05+00:00",
        "valueQuantity": {
          "value": 98,
          "unit": "percent",
          "system": "http://unitsofmeasure.org",
          "code": "%"
        },
        "subject": {
          "reference": "Patient/example"
        }
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "environment",
                "display": "Environment"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://example.org/CodeSystem/sensor",
              "code": "ambient-temperature",
              "display": "Ambient temperature"
            }
          ],
          "text": "Ambient temperature"
        },
        "effectiveDateTime": "2025-08-15T22:41:05+00:00",
        "valueQuantity": {
          "value": 24.3,
          "unit": "°C",
          "system": "http://unitsofmeasure.org",
          "code": "Cel"
        },
        "subject": {
          "reference": "Patient/example"
        }
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "status": "final",
        "category": [
          {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "environment",
                "display": "Environment"
              }
            ]
          }
        ],
        "code": {
          "coding": [
            {
              "system": "http://example.org/CodeSystem/sensor",
              "code": "humidity",
              "display": "Relative humidity"
            }
          ],
          "text": "Relative humidity"
        },
        "effectiveDateTime": "2025-08-15T22:41:05+00:00",
        "valueQuantity": {
          "value": 43.1,
          "unit": "percent",
          "system": "http://unitsofmeasure.org",
          "code": "%"
        },
        "subject": {
          "reference": "Patient/example"
        }
      }
    }
  ]
}
```
