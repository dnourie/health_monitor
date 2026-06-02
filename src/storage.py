from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd

from src.data_model import HealthEntry


DATA_DIR = Path("data")
DEFAULT_CSV_PATH = DATA_DIR / "health_log.csv"

CSV_COLUMNS = [
    "date",
    "reading_time",
    "glucose_mg_dl",
    "ketones_mmol_l",
    "headache_severity_0_to_10",
    "migraine_yes_no",
    "energy_1_to_10",
    "mood_stability_1_to_10",
    "sleep_quality",
    "sleep_hours",
    "rizatriptan_taken_yes_no",
    "carbs_g",
    "protein_g",
    "fats_g",
    "fasting_yes_no",
    "electrolyte_notes",
    "notes",
]


def load_entries(csv_path: Path = DEFAULT_CSV_PATH) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)

    entries = pd.read_csv(csv_path)
    prepared_entries = prepare_entries(entries)
    if list(entries.columns) != CSV_COLUMNS:
        prepared_entries.to_csv(csv_path, index=False)
    return prepared_entries


def save_entry(entry: HealthEntry, overwrite: bool = False, csv_path: Path = DEFAULT_CSV_PATH) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entries = load_entries(csv_path)
    new_entry = pd.DataFrame([entry.to_dict()], columns=CSV_COLUMNS)

    if overwrite:
        backup_csv(csv_path)
        entries = entries[entries["date"].astype(str) != entry.date]

    entries = pd.concat([entries, new_entry], ignore_index=True)
    entries = prepare_entries(entries)
    entries.to_csv(csv_path, index=False)


def backup_csv(csv_path: Path = DEFAULT_CSV_PATH) -> Path | None:
    if not csv_path.exists():
        return None

    backup_dir = csv_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{csv_path.stem}_{timestamp}{csv_path.suffix}"
    shutil.copy2(csv_path, backup_path)
    return backup_path


def prepare_entries(entries: pd.DataFrame) -> pd.DataFrame:
    if entries.empty:
        return pd.DataFrame(columns=CSV_COLUMNS)

    prepared = entries.copy()
    for column in CSV_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = None

    prepared = prepared[CSV_COLUMNS]
    prepared["date"] = pd.to_datetime(prepared["date"]).dt.date.astype(str)
    prepared["glucose_mg_dl"] = pd.to_numeric(prepared["glucose_mg_dl"], errors="coerce")
    prepared["ketones_mmol_l"] = pd.to_numeric(prepared["ketones_mmol_l"], errors="coerce")
    prepared["headache_severity_0_to_10"] = pd.to_numeric(
        prepared["headache_severity_0_to_10"], errors="coerce"
    )
    prepared["energy_1_to_10"] = pd.to_numeric(prepared["energy_1_to_10"], errors="coerce")
    prepared["mood_stability_1_to_10"] = pd.to_numeric(
        prepared["mood_stability_1_to_10"], errors="coerce"
    ).fillna(5)
    prepared["sleep_quality"] = prepared["sleep_quality"].map(_to_sleep_quality)
    prepared["sleep_hours"] = pd.to_numeric(prepared["sleep_hours"], errors="coerce").fillna(8.0)
    prepared["migraine_yes_no"] = prepared["migraine_yes_no"].map(_to_bool)
    prepared["rizatriptan_taken_yes_no"] = prepared["rizatriptan_taken_yes_no"].map(_to_bool)
    prepared["carbs_g"] = pd.to_numeric(prepared["carbs_g"], errors="coerce").fillna(0.0)
    prepared["protein_g"] = pd.to_numeric(prepared["protein_g"], errors="coerce").fillna(0.0)
    prepared["fats_g"] = pd.to_numeric(prepared["fats_g"], errors="coerce").fillna(0.0)
    prepared["fasting_yes_no"] = prepared["fasting_yes_no"].map(_to_bool)
    prepared["electrolyte_notes"] = prepared["electrolyte_notes"].fillna("")
    prepared = prepared.sort_values("date").reset_index(drop=True)
    return prepared


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _to_sleep_quality(value: object) -> str:
    if pd.isna(value):
        return "Good"

    normalized = str(value).strip().lower()
    sleep_quality_options = {
        "good": "Good",
        "disrupted": "Disrupted",
        "distrupted": "Disrupted",
        "poor": "Poor",
    }
    return sleep_quality_options.get(normalized, "Good")
