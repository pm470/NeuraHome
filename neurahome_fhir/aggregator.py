from typing import List, Optional, Dict

class Aggregator:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._hr: List[float] = []
        self._spo2: List[float] = []
        self._temp: List[float] = []
        self._hum: List[float] = []

    def add(self, reading: Dict[str, float]) -> None:
        if "hr" in reading: self._hr.append(reading["hr"])
        if "spo2" in reading: self._spo2.append(reading["spo2"])
        if "temp" in reading: self._temp.append(reading["temp"])
        if "hum" in reading: self._hum.append(reading["hum"])

    def _avg(self, vals: List[float]) -> Optional[float]:
        return round(sum(vals) / len(vals), 2) if vals else None

    def snapshot(self) -> Dict[str, Optional[float]]:
        return {
            "hr": self._avg(self._hr),
            "spo2": self._avg(self._spo2),
            "temp": self._avg(self._temp),
            "hum": self._avg(self._hum),
        }
