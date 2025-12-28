import logging
from threading import Lock
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TimelineStore:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._events_by_patient: Dict[str, List[Dict[str, Any]]] = {}
                cls._instance._events_lock = Lock()
            return cls._instance

    def add_event(self, patient_key: str, event: Dict[str, Any]) -> None:
        try:
            with self._events_lock:
                self._events_by_patient.setdefault(patient_key, []).append(event)
        except Exception:
            logger.exception("Failed to add event to timeline store")

    def get_timeline(self, patient_key: str) -> List[Dict[str, Any]]:
        try:
            with self._events_lock:
                return list(self._events_by_patient.get(patient_key, []))
        except Exception:
            logger.exception("Failed to retrieve timeline from store")
            return []


def build_patient_key(first_name: str, last_name: str, dob: str) -> str:
    return f"{first_name.strip().lower()}|{last_name.strip().lower()}|{dob.strip()}"


def get_timeline_store() -> TimelineStore:
    return TimelineStore()
