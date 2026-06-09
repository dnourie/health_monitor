from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
import shutil

import pandas as pd


KETOMOJO_READINGS_PATH = Path("data") / "ketomojo_readings.csv"
KETOMOJO_IMPORT_HISTORY_PATH = Path("data") / "ketomojo_import_history.csv"
LOCAL_TZ = "America/Chicago"
SESSION_GAP_MINUTES = 10

KETOMOJO_COLUMNS = [
    "reading_id",
    "reading_timestamp",
    "local_time",
    "date",
    "reading_type",
    "reading_sample_type",
    "reading_value",
    "reading_unit",
    "source",
    "meter_type",
    "serial_number",
    "device_id",
    "tags",
    "notes",
    "reading_timezone",
    "metadata_key",
    "has_calculated_gki",
]

IMPORT_HISTORY_COLUMNS = [
    "imported_at",
    "file_name",
    "file_rows",
    "new_rows",
    "duplicate_rows",
    "first_reading",
    "last_reading",
]


@dataclass(frozen=True)
class KetoMojoImportResult:
    file_name: str
    file_rows: int
    new_rows: int
    duplicate_rows: int
    first_reading: str
    last_reading: str


def parse_ketomojo_export(file: str | bytes | BytesIO) -> pd.DataFrame:
    export = _read_export_csv(file)
    _validate_export(export)

    readings = export.copy()
    readings["reading_timestamp"] = pd.to_datetime(readings["reading_timestamp"], utc=True, errors="coerce")
    readings["reading_value"] = pd.to_numeric(readings["reading_value"], errors="coerce")
    readings = readings.dropna(subset=["reading_timestamp", "reading_type", "reading_value"])
    readings["local_time"] = readings["reading_timestamp"].dt.tz_convert(LOCAL_TZ)
    readings["date"] = readings["local_time"].dt.date.astype(str)
    readings["reading_timestamp"] = readings["reading_timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    readings["local_time"] = readings["local_time"].dt.strftime("%Y-%m-%d %H:%M:%S%z")

    for column in KETOMOJO_COLUMNS:
        if column not in readings.columns:
            readings[column] = ""

    readings = readings[KETOMOJO_COLUMNS]
    readings = readings.sort_values(["date", "local_time", "reading_type"]).reset_index(drop=True)
    return readings


def import_ketomojo_export(
    file: str | bytes | BytesIO,
    file_name: str = "ketomojo_export.csv",
    readings_path: Path = KETOMOJO_READINGS_PATH,
    history_path: Path = KETOMOJO_IMPORT_HISTORY_PATH,
) -> KetoMojoImportResult:
    new_readings = parse_ketomojo_export(file)
    existing_readings = load_ketomojo_readings(readings_path)

    existing_ids = set(existing_readings["reading_id"].dropna().astype(str))
    dedupe_keys = set(_dedupe_key(existing_readings))
    new_ids = new_readings["reading_id"].fillna("").astype(str)
    new_keys = _dedupe_key(new_readings)

    is_duplicate = [
        (reading_id and reading_id in existing_ids) or key in dedupe_keys
        for reading_id, key in zip(new_ids, new_keys, strict=False)
    ]
    rows_to_add = new_readings.loc[[not duplicate for duplicate in is_duplicate]].copy()

    if not rows_to_add.empty:
        readings_path.parent.mkdir(parents=True, exist_ok=True)
        backup_csv(readings_path)
        combined = pd.concat([existing_readings, rows_to_add], ignore_index=True)
        combined = prepare_ketomojo_readings(combined)
        combined.to_csv(readings_path, index=False)

    result = KetoMojoImportResult(
        file_name=file_name,
        file_rows=len(new_readings),
        new_rows=len(rows_to_add),
        duplicate_rows=int(sum(is_duplicate)),
        first_reading=_timestamp_range_value(new_readings, "min"),
        last_reading=_timestamp_range_value(new_readings, "max"),
    )
    append_import_history(result, history_path)
    return result


def load_ketomojo_readings(csv_path: Path = KETOMOJO_READINGS_PATH) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=KETOMOJO_COLUMNS)

    readings = pd.read_csv(csv_path)
    prepared = prepare_ketomojo_readings(readings)
    if list(readings.columns) != KETOMOJO_COLUMNS:
        prepared.to_csv(csv_path, index=False)
    return prepared


def load_import_history(csv_path: Path = KETOMOJO_IMPORT_HISTORY_PATH) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=IMPORT_HISTORY_COLUMNS)

    history = pd.read_csv(csv_path)
    for column in IMPORT_HISTORY_COLUMNS:
        if column not in history.columns:
            history[column] = ""
    return history[IMPORT_HISTORY_COLUMNS].sort_values("imported_at").reset_index(drop=True)


def build_ketomojo_sessions(readings: pd.DataFrame) -> pd.DataFrame:
    if readings.empty:
        return pd.DataFrame(
            columns=[
                "session_id",
                "session_time",
                "date",
                "hour",
                "time_of_day",
                "readings_in_session",
                "glucose",
                "ketone",
                "glucose_ketone_index",
            ]
        )

    session_readings = readings.copy()
    session_readings["local_time"] = pd.to_datetime(
        session_readings["local_time"], utc=True, errors="coerce"
    ).dt.tz_convert(LOCAL_TZ)
    session_readings["reading_value"] = pd.to_numeric(session_readings["reading_value"], errors="coerce")
    session_readings = session_readings.dropna(subset=["local_time", "reading_value"]).sort_values("local_time")
    session_readings["gap_minutes"] = session_readings["local_time"].diff().dt.total_seconds().div(60)
    session_readings["session_id"] = (
        session_readings["gap_minutes"].isna()
        | (session_readings["gap_minutes"] > SESSION_GAP_MINUTES)
    ).cumsum()

    session_values = session_readings.pivot_table(
        index="session_id",
        columns="reading_type",
        values="reading_value",
        aggfunc="mean",
    )
    session_meta = session_readings.groupby("session_id").agg(
        session_time=("local_time", "min"),
        readings_in_session=("reading_type", "count"),
    )

    sessions = session_meta.join(session_values).reset_index()
    sessions["date"] = sessions["session_time"].dt.date.astype(str)
    sessions["hour"] = sessions["session_time"].dt.hour
    sessions["time_of_day"] = pd.cut(
        sessions["hour"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["overnight", "morning", "afternoon", "evening", "night"],
    )
    return sessions.sort_values("session_time").reset_index(drop=True)


def prepare_ketomojo_readings(readings: pd.DataFrame) -> pd.DataFrame:
    if readings.empty:
        return pd.DataFrame(columns=KETOMOJO_COLUMNS)

    prepared = readings.copy()
    for column in KETOMOJO_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = ""

    prepared = prepared[KETOMOJO_COLUMNS]
    prepared["reading_value"] = pd.to_numeric(prepared["reading_value"], errors="coerce")
    prepared = prepared.dropna(subset=["reading_value"])
    prepared = prepared.sort_values(["date", "local_time", "reading_type"]).reset_index(drop=True)
    return prepared


def append_import_history(
    result: KetoMojoImportResult,
    csv_path: Path = KETOMOJO_IMPORT_HISTORY_PATH,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    history = load_import_history(csv_path)
    imported_at = datetime.now().isoformat(timespec="seconds")
    new_row = pd.DataFrame(
        [
            {
                "imported_at": imported_at,
                "file_name": result.file_name,
                "file_rows": result.file_rows,
                "new_rows": result.new_rows,
                "duplicate_rows": result.duplicate_rows,
                "first_reading": result.first_reading,
                "last_reading": result.last_reading,
            }
        ],
        columns=IMPORT_HISTORY_COLUMNS,
    )
    pd.concat([history, new_row], ignore_index=True).to_csv(csv_path, index=False)


def backup_csv(csv_path: Path) -> Path | None:
    if not csv_path.exists():
        return None

    backup_dir = csv_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{csv_path.stem}_{timestamp}{csv_path.suffix}"
    shutil.copy2(csv_path, backup_path)
    return backup_path


def _read_export_csv(file: str | bytes | BytesIO) -> pd.DataFrame:
    if isinstance(file, BytesIO):
        file.seek(0)
        text = file.read().decode("utf-8-sig")
        return pd.read_csv(StringIO(text), skiprows=3)

    if isinstance(file, bytes):
        return pd.read_csv(StringIO(file.decode("utf-8-sig")), skiprows=3)

    return pd.read_csv(file, skiprows=3)


def _validate_export(readings: pd.DataFrame) -> None:
    required_columns = {"reading_timestamp", "reading_type", "reading_value", "reading_id"}
    missing_columns = required_columns.difference(readings.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"This does not look like a Keto-Mojo export. Missing columns: {missing}.")


def _dedupe_key(readings: pd.DataFrame) -> pd.Series:
    if readings.empty:
        return pd.Series(dtype=str)

    return (
        readings["reading_timestamp"].fillna("").astype(str)
        + "|"
        + readings["reading_type"].fillna("").astype(str)
        + "|"
        + readings["reading_value"].fillna("").astype(str)
    )


def _timestamp_range_value(readings: pd.DataFrame, function_name: str) -> str:
    if readings.empty:
        return ""

    timestamps = pd.to_datetime(readings["local_time"], utc=True, errors="coerce").dt.tz_convert(LOCAL_TZ)
    value = getattr(timestamps, function_name)()
    if pd.isna(value):
        return ""
    return value.isoformat()
