from __future__ import annotations

from dataclasses import asdict, dataclass


class ValidationError(ValueError):
    """Raised when a health entry has invalid values."""


@dataclass
class HealthEntry:
    date: str
    reading_time: str
    glucose_mg_dl: float
    ketones_mmol_l: float
    headache_severity_0_to_10: int
    migraine_yes_no: bool
    energy_1_to_10: int
    mood_stability_1_to_10: int
    sleep_quality: str
    sleep_hours: float
    rizatriptan_taken_yes_no: bool
    notes: str = ""

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.date:
            raise ValidationError("Date is required.")

        if not 0 <= self.glucose_mg_dl <= 500:
            raise ValidationError("Glucose must be between 0 and 500 mg/dL.")

        if not 0 <= self.ketones_mmol_l <= 10:
            raise ValidationError("Ketones must be between 0 and 10 mmol/L.")

        if not 0 <= self.headache_severity_0_to_10 <= 10:
            raise ValidationError("Headache severity must be between 0 and 10.")

        if not 1 <= self.energy_1_to_10 <= 10:
            raise ValidationError("Energy must be between 1 and 10.")

        if not 1 <= self.mood_stability_1_to_10 <= 10:
            raise ValidationError("Mood stability must be between 1 and 10.")

        if self.sleep_quality not in {"Good", "Disrupted", "Poor"}:
            raise ValidationError("Sleep quality must be Good, Disrupted, or Poor.")

        if not 0 <= self.sleep_hours <= 14:
            raise ValidationError("Sleep hours must be between 0 and 14.")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
