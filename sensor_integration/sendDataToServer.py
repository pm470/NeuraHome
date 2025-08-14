import serial
import time
import requests
from datetime import datetime, timezone

# ── Config ─────────────────────────────────────────────────────────────────────
SERIAL_PORT = '/dev/ttyACM0'
BAUD = 115200
POST_EVERY_SECONDS = 10  # you used 10 for testing
URL = "https://httpbin.org/post"
HEADERS = {
    "Content-Type": "application/fhir+json",
    "X-API-KEY": "ef0a30cf982749a38107d3f26c7ec8a7"
}

# Optional (comment out if you don’t track a patient yet)
PATIENT_ID = "Patient/example"  # e.g., "Patient/123". Or set to None to omit.

# ── Serial ─────────────────────────────────────────────────────────────────────
ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
time.sleep(2)

# ── Buffers ────────────────────────────────────────────────────────────────────
hr_vals, spo2_vals, temp_vals, hum_vals = [], [], [], []
start_time = time.time()

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def obs_resource(code_system, code, display, value, unit, ucum_code,
                 category_code="vital-signs", category_display="Vital Signs"):
    if value is None:
        return None

    res = {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": category_code,
                "display": category_display
            }]
        }],
        "code": {
            "coding": [{
                "system": code_system,
                "code": code,
                "display": display
            }],
            "text": display
        },
        "effectiveDateTime": now_iso(),
        "valueQuantity": {
            "value": round(value, 2),
            "unit": unit,
            "system": "http://unitsofmeasure.org",
            "code": ucum_code
        }
    }
    if PATIENT_ID:
        res["subject"] = {"reference": PATIENT_ID}
    return res

print("Starting…")
while True:
    try:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            if "Heartrate:" in line:
                try:
                    v = int(line.split(":")[1])
                    if v > 0:
                        hr_vals.append(v)
                except:
                    pass
            elif "Oxygen:" in line:
                try:
                    v = int(line.split(":")[1])
                    if v > 0:
                        spo2_vals.append(v)
                except:
                    pass
            elif "Temperature:" in line:
                try:
                    v = float(line.split(":")[1].replace("°C", "").strip())
                    temp_vals.append(v)  # ambient temperature
                except:
                    pass
            elif "Humidity:" in line:
                try:
                    v = float(line.split(":")[1].replace("%", "").strip())
                    hum_vals.append(v)
                except:
                    pass

        if time.time() - start_time >= POST_EVERY_SECONDS:
            have_any = any([hr_vals, spo2_vals, temp_vals, hum_vals])
            if have_any:
                # Averages (with simple validity checks)
                avg_hr = round(sum(hr_vals)/len(hr_vals), 2) if hr_vals else None
                avg_spo2 = round(sum(spo2_vals)/len(spo2_vals), 2) if spo2_vals else None
                avg_temp = round(sum(temp_vals)/len(temp_vals), 2) if temp_vals else None
                avg_hum = round(sum(hum_vals)/len(hum_vals), 2) if hum_vals else None

                # Build FHIR Observations
                observations = []

                # Heart Rate — LOINC 8867-4, vital sign
                if avg_hr is not None:
                    observations.append(
                        obs_resource(
                            "http://loinc.org", "8867-4", "Heart rate",
                            avg_hr, "beats/minute", "/min"
                        )
                    )

                # SpO2 — LOINC 59408-5, vital sign
                if avg_spo2 is not None:
                    observations.append(
                        obs_resource(
                            "http://loinc.org", "59408-5", "Oxygen saturation in Arterial blood by Pulse oximetry",
                            avg_spo2, "percent", "%"
                        )
                    )

                # Ambient Temperature — NOT a vital sign; send as environment
                if avg_temp is not None:
                    observations.append(
                        obs_resource(
                            "http://example.org/CodeSystem/sensor",  # use a local code system for now
                            "ambient-temperature",
                            "Ambient temperature",
                            avg_temp, "°C", "Cel",
                            category_code="environment",
                            category_display="Environment"
                        )
                    )

                # Humidity — environment
                if avg_hum is not None:
                    observations.append(
                        obs_resource(
                            "http://example.org/CodeSystem/sensor", "humidity", "Relative humidity",
                            avg_hum, "percent", "%", category_code="environment", category_display="Environment"
                        )
                    )

                # Remove Nones
                observations = [o for o in observations if o]

                if observations:
                    bundle = {
                        "resourceType": "Bundle",
                        "type": "collection",
                        "timestamp": now_iso(),
                        "entry": [{"resource": r} for r in observations]
                    }

                    resp = requests.post(URL, headers=HEADERS, json=bundle, timeout=10)
                    print(f"\nPosted FHIR Bundle with {len(observations)} Observations")
                    print(f"Status: {resp.status_code} | Body: {resp.text}\n")
                else:
                    print("No valid averages to send this interval.")
            else:
                print("No data collected in this interval.")

            # Reset window
            hr_vals.clear(); spo2_vals.clear(); temp_vals.clear(); hum_vals.clear()
            start_time = time.time()

    except KeyboardInterrupt:
        print("Stopped by user")
        break
    except Exception as e:
        print(f"Error: {e}")
