from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

DEFAULT_HEADERS = {
    "Content-Type": "application/fhir+json",
    "X-API-KEY": "ef0a30cf982749a38107d3f26c7ec8a7",
}

@dataclass(frozen=True)
class Config:
    serial_port: str = "/dev/ttyACM0"
    baud: int = 115200
    post_every_seconds: int = 10
    url: str = "https://httpbin.org/post" # URL = "http://127.0.0.1:8000/api/sensor/readings/"
    headers: Dict[str, str] = field(default_factory=lambda: DEFAULT_HEADERS.copy())
    patient_id: Optional[str] = "Patient/example"  # set to None to omit
