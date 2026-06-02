from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

from src.analysis import build_observations
from src.charts import (
    energy_over_time_chart,
    glucose_over_time_chart,
    headache_over_time_chart,
    ketones_over_time_chart,
    mood_stability_over_time_chart,
    relationship_chart,
    sleep_hours_over_time_chart,
)
from src.data_model import HealthEntry, ValidationError
from src.storage import DEFAULT_CSV_PATH, load_entries, save_entry


st.set_page_config(page_title="Health Monitor", page_icon="HM", layout="wide")

st.title("Personal Health Monitor")
st.caption("Version 1.0.1")
st.caption(
    "Track glucose, ketones, sleep, headache, migraine status, energy, mood, medication use, and notes. "
    "For personal insight only, not medical advice."
)


def yes_no_label(value: bool) -> str:
    return "Yes" if value else "No"


def _parse_time(value: object) -> time:
    if not value:
        return datetime.now().time().replace(second=0, microsecond=0)
    try:
        return datetime.strptime(str(value), "%H:%M").time()
    except ValueError:
        return datetime.now().time().replace(second=0, microsecond=0)


def _float_or_default(value: object, default: float) -> float:
    if value != value:
        return default
    try:
        return default if value is None else float(value)
    except (TypeError, ValueError):
        return default


def _int_or_default(value: object, default: int) -> int:
    if value != value:
        return default
    try:
        return default if value is None else int(value)
    except (TypeError, ValueError):
        return default


def _init_form_state() -> None:
    defaults = {
        "entry_date": date.today(),
        "reading_time": datetime.now().time().replace(second=0, microsecond=0),
        "glucose_mg_dl": 90.0,
        "ketones_mmol_l": 0.5,
        "headache_severity": 0,
        "energy": 5,
        "mood_stability": 5,
        "sleep_quality": "Good",
        "sleep_hours": 8.0,
        "migraine": False,
        "rizatriptan": False,
        "overwrite_existing_date": False,
        "notes": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def load_entry_into_form(entries) -> None:
    if entries.empty:
        return

    st.subheader("Find Existing Entry")
    lookup_date = st.date_input("Entry date to edit", value=date.today(), key="lookup_date")
    lookup_date_string = lookup_date.isoformat()

    if not st.button("Load entry"):
        return

    matching_entries = entries[entries["date"].astype(str) == lookup_date_string]
    if matching_entries.empty:
        st.warning(f"No entry found for {lookup_date_string}.")
        return

    entry = matching_entries.iloc[-1]
    st.session_state.entry_date = datetime.strptime(str(entry["date"]), "%Y-%m-%d").date()
    st.session_state.reading_time = _parse_time(entry["reading_time"])
    st.session_state.glucose_mg_dl = float(entry["glucose_mg_dl"])
    st.session_state.ketones_mmol_l = float(entry["ketones_mmol_l"])
    st.session_state.headache_severity = int(entry["headache_severity_0_to_10"])
    st.session_state.energy = int(entry["energy_1_to_10"])
    st.session_state.mood_stability = _int_or_default(entry.get("mood_stability_1_to_10"), 5)
    st.session_state.sleep_quality = str(entry.get("sleep_quality", "Good"))
    st.session_state.sleep_hours = _float_or_default(entry.get("sleep_hours"), 8.0)
    st.session_state.migraine = bool(entry["migraine_yes_no"])
    st.session_state.rizatriptan = bool(entry["rizatriptan_taken_yes_no"])
    st.session_state.overwrite_existing_date = True
    notes_value = entry["notes"]
    st.session_state.notes = "" if notes_value is None or str(notes_value) == "nan" else str(notes_value)
    st.success(f"Loaded entry for {lookup_date_string}. Make your changes, then save.")


def entry_form() -> None:
    _init_form_state()
    st.subheader("Daily Entry")

    existing_entries = load_entries()
    existing_dates = set(existing_entries["date"].astype(str)) if not existing_entries.empty else set()
    load_entry_into_form(existing_entries)

    with st.form("daily_entry_form"):
        left, middle, right = st.columns(3)

        with left:
            st.date_input("Date", key="entry_date")
            st.time_input("Reading time", key="reading_time")
            st.number_input("Glucose (mg/dL)", min_value=0.0, max_value=500.0, step=1.0, key="glucose_mg_dl")

        with middle:
            st.number_input("Ketones (mmol/L)", min_value=0.0, max_value=10.0, step=0.1, key="ketones_mmol_l")
            st.slider("Headache severity", min_value=0, max_value=10, key="headache_severity")
            st.slider("Energy", min_value=1, max_value=10, key="energy")
            st.slider("Mood stability", min_value=1, max_value=10, key="mood_stability")

        with right:
            st.radio("Sleep quality", ["Good", "Disrupted", "Poor"], horizontal=True, key="sleep_quality")
            st.number_input("Sleep hours", min_value=0.0, max_value=14.0, step=0.5, key="sleep_hours")
            st.checkbox("Migraine", key="migraine")
            st.checkbox("Rizatriptan taken", key="rizatriptan")
            st.checkbox("Update/replace entry for this date", key="overwrite_existing_date")

        st.text_area(
            "Notes",
            placeholder=(
                "Optional: sleep, weather/rain, stress, food changes, fasting, electrolytes, "
                "caffeine, exercise, medication details, or anything unusual."
            ),
            height=130,
            key="notes",
        )

        submitted = st.form_submit_button("Save entry", type="primary")

    if not submitted:
        return

    date_string = st.session_state.entry_date.isoformat()
    if date_string in existing_dates and not st.session_state.overwrite_existing_date:
        st.warning("An entry already exists for this date. Check update/replace if you want to edit it.")
        return

    try:
        entry = HealthEntry(
            date=date_string,
            reading_time=st.session_state.reading_time.strftime("%H:%M"),
            glucose_mg_dl=st.session_state.glucose_mg_dl,
            ketones_mmol_l=st.session_state.ketones_mmol_l,
            headache_severity_0_to_10=st.session_state.headache_severity,
            migraine_yes_no=st.session_state.migraine,
            energy_1_to_10=st.session_state.energy,
            mood_stability_1_to_10=st.session_state.mood_stability,
            sleep_quality=st.session_state.sleep_quality,
            sleep_hours=st.session_state.sleep_hours,
            rizatriptan_taken_yes_no=st.session_state.rizatriptan,
            notes=st.session_state.notes.strip(),
        )
        save_entry(entry, overwrite=st.session_state.overwrite_existing_date)
    except ValidationError as error:
        st.error(str(error))
        return

    st.success(f"Saved entry for {date_string}.")


def recent_entries_section() -> None:
    entries = load_entries()

    st.subheader("Recent Entries")
    if entries.empty:
        st.info("No entries yet. Save your first daily entry above.")
        return

    display = entries.tail(10).sort_values("date", ascending=False).copy()
    display["migraine_yes_no"] = display["migraine_yes_no"].map(yes_no_label)
    display["rizatriptan_taken_yes_no"] = display["rizatriptan_taken_yes_no"].map(yes_no_label)
    st.dataframe(display, use_container_width=True, hide_index=True)


def charts_section() -> None:
    entries = load_entries()

    st.subheader("Charts")
    if entries.empty:
        st.info("Charts will appear after you save data.")
        return

    tabs = st.tabs(["Trends", "Relationships"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(glucose_over_time_chart(entries), use_container_width=True)
            st.plotly_chart(headache_over_time_chart(entries), use_container_width=True)
        with col2:
            st.plotly_chart(ketones_over_time_chart(entries), use_container_width=True)
            st.plotly_chart(energy_over_time_chart(entries), use_container_width=True)
            st.plotly_chart(mood_stability_over_time_chart(entries), use_container_width=True)
            st.plotly_chart(sleep_hours_over_time_chart(entries), use_container_width=True)

    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                relationship_chart(entries, "glucose_mg_dl", "headache_severity_0_to_10", "Glucose vs Headache"),
                use_container_width=True,
            )
        with col2:
            st.plotly_chart(
                relationship_chart(entries, "ketones_mmol_l", "energy_1_to_10", "Ketones vs Energy"),
                use_container_width=True,
            )


def observations_section() -> None:
    entries = load_entries()

    st.subheader("Observations")
    if entries.empty:
        st.info("Observations will appear after you save data.")
        return

    observations = build_observations(entries)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Entries", observations["entry_count"])
    metric_cols[1].metric("Migraine days", observations["migraine_days"])
    metric_cols[2].metric("Rizatriptan days", observations["rizatriptan_days"])
    metric_cols[3].metric("High headache days", observations["high_headache_days"])

    st.write("These are simple observations from your logged data, not medical conclusions.")
    st.dataframe(observations["migraine_comparison"], use_container_width=True, hide_index=True)


entry_form()
st.divider()
recent_entries_section()
st.divider()
charts_section()
st.divider()
observations_section()

st.caption(f"Data file: {DEFAULT_CSV_PATH}")
