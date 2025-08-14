from typing import Optional, List
from .utils import now_iso

class FHIRBuilder:
    OBS_CAT_URL = "http://terminology.hl7.org/CodeSystem/observation-category"
    UCUM = "http://unitsofmeasure.org"
    LOINC = "http://loinc.org"

    def observation(self, code_system: str, code: str, display: str,
                    value: Optional[float], unit: str, ucum_code: str,
                    patient_id: Optional[str],
                    category_code: str, category_display: str) -> Optional[dict]:
        if value is None:
            return None
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": self.OBS_CAT_URL,
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
                "value": value,
                "unit": unit,
                "system": self.UCUM,
                "code": ucum_code
            }
        }
        if patient_id:
            obs["subject"] = {"reference": patient_id}
        return obs

    def build_observations(self, agg: dict, patient_id: Optional[str]) -> List[dict]:
        out: List[dict] = []
        out.append(self.observation(
            self.LOINC, "8867-4", "Heart rate",
            agg.get("hr"), "beats/minute", "/min",
            patient_id, "vital-signs", "Vital Signs"
        ))
        out.append(self.observation(
            self.LOINC, "59408-5",
            "Oxygen saturation in Arterial blood by Pulse oximetry",
            agg.get("spo2"), "percent", "%",
            patient_id, "vital-signs", "Vital Signs"
        ))
        out.append(self.observation(
            "http://example.org/CodeSystem/sensor", "ambient-temperature",
            "Ambient temperature",
            agg.get("temp"), "°C", "Cel",
            patient_id, "environment", "Environment"
        ))
        out.append(self.observation(
            "http://example.org/CodeSystem/sensor", "humidity",
            "Relative humidity",
            agg.get("hum"), "percent", "%",
            patient_id, "environment", "Environment"
        ))
        return [o for o in out if o]

    def bundle(self, observations: List[dict]) -> Optional[dict]:
        if not observations:
            return None
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": now_iso(),
            "entry": [{"resource": r} for r in observations]
        }
