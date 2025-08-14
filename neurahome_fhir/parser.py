from typing import Dict
import logging

class SensorParser:
    """
    Converts a raw serial line → structured reading dict.
    """

    @staticmethod
    def parse(line: str) -> Dict[str, float]:
        s = line.strip()
        if not s:
            return {}

        try:
            if s.startswith("Heartrate:"):
                v = int(s.split(":", 1)[1])
                return {"hr": v} if v > 0 else {}
            if s.startswith("Oxygen:"):
                v = int(s.split(":", 1)[1])
                return {"spo2": v} if v > 0 else {}
            if s.startswith("Temperature:"):
                raw = s.split(":", 1)[1].replace("°C", "").strip()
                return {"temp": float(raw)}  # ambient temperature
            if s.startswith("Humidity:"):
                raw = s.split(":", 1)[1].replace("%", "").strip()
                return {"hum": float(raw)}
        except Exception:
            logging.debug("Failed to parse: %r", s)
            return {}

        return {}
