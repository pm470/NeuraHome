import serial
import time
import requests
from datetime import datetime

# Serial port config
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Give Arduino time to reset

# API endpoint and headers
URL = "https://httpbin.org/post"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": "5538144ff69744518494080bff10fb86"
}

# Storage lists for 1-minute accumulation
heart_rate_values = []
oxygen_values = []
temperature_values = []
humidity_values = []

start_time = time.time()
print("Starting...")
while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line:            
            if "Heartrate:" in line:
                heart_rate_values.append(int(line.split(":")[1].strip()))
            elif "Oxygen:" in line:
                oxygen_values.append(int(line.split(":")[1].strip()))
            elif "Temperature:" in line:
                temp_str = line.split(":")[1].strip().replace("°C", "").strip()
                temperature_values.append(float(temp_str))
            elif "Humidity:" in line:
                hum_str = line.split(":")[1].strip().replace("%", "").strip()
                humidity_values.append(float(hum_str))


        # Check if 60 seconds passed
        if time.time() - start_time >= 10:
            if heart_rate_values or oxygen_values or temperature_values or humidity_values:
                # Calculate averages
                valid_heart_rates = [v for v in heart_rate_values if v > 0]
                avg_heart_rate = sum(valid_heart_rates) / len(valid_heart_rates) if valid_heart_rates else 0                
                valid_oxygen = [v for v in oxygen_values if v > 0]
                avg_oxygen = sum(valid_oxygen) / len(valid_oxygen) if valid_oxygen else 0
                avg_temperature = sum(temperature_values) / len(temperature_values)
                avg_humidity = sum(humidity_values) / len(humidity_values)

                # Prepare payload
                payload = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "values": [
                        {"sensory_name": "heart_rate", "sensory_value": round(avg_heart_rate, 2)},
                        {"sensory_name": "oxygen", "sensory_value": round(avg_oxygen, 2)},
                        {"sensory_name": "temperature", "sensory_value": round(avg_temperature, 2)},
                        {"sensory_name": "humidity", "sensory_value": round(avg_humidity, 2)}
                    ]
                }

                # Send to server
                response = requests.post(URL, headers=HEADERS, json=payload)
                print(f"\nPosted: {payload}")
                print(f"Response: {response.status_code} - {response.text}\n")

            else:
                print("No complete data collected in the last minute.")

            # Reset everything
            heart_rate_values.clear()
            oxygen_values.clear()
            temperature_values.clear()
            humidity_values.clear()
            start_time = time.time()

    except KeyboardInterrupt:
        print("Stopped by user")
        break
    except Exception as e:
        print(f"Error: {e}")
