from __future__ import annotations

from datetime import date, datetime, time
from pathlib import Path

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


APP_VERSION = "1.0.3"
STYLE_PATH = Path(__file__).parent / "assets" / "styles.css"


def load_css() -> None:
    st.markdown(f"<style>{STYLE_PATH.read_text()}</style>", unsafe_allow_html=True)


def page_header() -> None:
    st.markdown(
        f"""
        <header class="hm-hero">
          <div class="hm-icon" aria-hidden="true">
            <svg viewBox="0 0 48 48" role="img">
              <path fill="currentColor" d="M24 42s-1.2-1-2.9-2.5C10.6 30.2 5 24.7 5 16.4C5 10.5 9.5 6 15.3 6c3.3 0 6.5 1.6 8.7 4.2C26.2 7.6 29.4 6 32.7 6C38.5 6 43 10.5 43 16.4c0 8.3-5.6 13.8-16.1 23.1C25.2 41 24 42 24 42Z"/>
              <path fill="#ffffff" d="M21 16h6v7h7v6h-7v7h-6v-7h-7v-6h7z"/>
            </svg>
          </div>
          <div>
            <h1 class="hm-title">Personal Health Monitor</h1>
            <p class="hm-subtitle">
              Track glucose, ketones, sleep, headache, migraine status, energy, mood, diet, medication use,
              and notes. For personal insight only, not medical advice.
            </p>
            <span class="hm-version">Version {APP_VERSION}</span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def section_heading(label: str) -> None:
    st.markdown(f'<h2 class="hm-section-heading">{label}</h2>', unsafe_allow_html=True)


def section_heading_small(label: str) -> None:
    st.markdown(f'<h3 class="hm-section-heading-small">{label}</h3>', unsafe_allow_html=True)


st.set_page_config(page_title="Health Monitor", page_icon="HM", layout="wide")
load_css()
page_header()


def yes_no_label(value: bool) -> str:
    return "Yes" if value else "No"


def _parse_time(value: object) -> time:
    if not value:
        return datetime.now().time().replace(second=0, microsecond=0)
    try:
        return datetime.strptime(str(value), "%H:%M").time()
    except ValueError:
        return datetime.now().time().replace(second=0, microsecond=0)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(value != value)
    except (TypeError, ValueError):
        return False


def _float_or_default(value: object, default: float) -> float:
    if _is_missing(value):
        return default
    try:
        return default if value is None else float(value)
    except (TypeError, ValueError):
        return default


def _int_or_default(value: object, default: int) -> int:
    if _is_missing(value):
        return default
    try:
        return default if value is None else int(value)
    except (TypeError, ValueError):
        return default


def _bool_or_default(value: object, default: bool = False) -> bool:
    if _is_missing(value):
        return default
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _text_or_default(value: object, default: str = "") -> str:
    if _is_missing(value):
        return default
    return str(value)


def _entry_for_date(entries, entry_date: str):
    if entries.empty:
        return None
    matching_entries = entries[entries["date"].astype(str) == entry_date]
    if matching_entries.empty:
        return None
    return matching_entries.iloc[-1]


def _entry_from_row(row, **overrides: object) -> HealthEntry:
    values = {
        "date": str(row["date"]),
        "reading_time": str(row["reading_time"]),
        "glucose_mg_dl": _float_or_default(row["glucose_mg_dl"], 90.0),
        "ketones_mmol_l": _float_or_default(row["ketones_mmol_l"], 0.5),
        "headache_severity_0_to_10": _int_or_default(row["headache_severity_0_to_10"], 0),
        "migraine_yes_no": _bool_or_default(row["migraine_yes_no"]),
        "energy_1_to_10": _int_or_default(row["energy_1_to_10"], 5),
        "mood_stability_1_to_10": _int_or_default(row["mood_stability_1_to_10"], 5),
        "sleep_quality": _text_or_default(row["sleep_quality"], "Good"),
        "sleep_hours": _float_or_default(row["sleep_hours"], 8.0),
        "rizatriptan_taken_yes_no": _bool_or_default(row["rizatriptan_taken_yes_no"]),
        "notes": _text_or_default(row["notes"]),
        "carbs_g": _float_or_default(row.get("carbs_g"), 0.0),
        "protein_g": _float_or_default(row.get("protein_g"), 0.0),
        "fats_g": _float_or_default(row.get("fats_g"), 0.0),
        "fasting_yes_no": _bool_or_default(row.get("fasting_yes_no")),
        "electrolyte_notes": _text_or_default(row.get("electrolyte_notes")),
    }
    values.update(overrides)
    return HealthEntry(**values)


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
        "diet_date": date.today(),
        "carbs_g": 0.0,
        "protein_g": 0.0,
        "fats_g": 0.0,
        "fasting": False,
        "electrolyte_notes": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def load_entry_into_form(entries) -> None:
    if entries.empty:
        return

    section_heading_small("Create New or Edit Existing Entry")
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
    section_heading("Daily Entry")

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

    existing_entry = _entry_for_date(existing_entries, date_string)
    diet_values = {}
    if existing_entry is not None:
        diet_values = {
            "carbs_g": _float_or_default(existing_entry.get("carbs_g"), 0.0),
            "protein_g": _float_or_default(existing_entry.get("protein_g"), 0.0),
            "fats_g": _float_or_default(existing_entry.get("fats_g"), 0.0),
            "fasting_yes_no": _bool_or_default(existing_entry.get("fasting_yes_no")),
            "electrolyte_notes": _text_or_default(existing_entry.get("electrolyte_notes")),
        }

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
            **diet_values,
        )
        save_entry(entry, overwrite=st.session_state.overwrite_existing_date)
    except ValidationError as error:
        st.error(str(error))
        return

    st.success(f"Saved entry for {date_string}.")


def diet_form() -> None:
    _init_form_state()
    section_heading("Diet Entry")

    entries = load_entries()
    diet_date = st.date_input("Date", key="diet_date")
    diet_date_string = diet_date.isoformat()
    existing_entry = _entry_for_date(entries, diet_date_string)

    if st.button("Load diet for date"):
        if existing_entry is None:
            st.warning(f"No daily health entry found for {diet_date_string}. Save Daily Health first.")
        else:
            st.session_state.carbs_g = _float_or_default(existing_entry.get("carbs_g"), 0.0)
            st.session_state.protein_g = _float_or_default(existing_entry.get("protein_g"), 0.0)
            st.session_state.fats_g = _float_or_default(existing_entry.get("fats_g"), 0.0)
            st.session_state.fasting = _bool_or_default(existing_entry.get("fasting_yes_no"))
            st.session_state.electrolyte_notes = _text_or_default(existing_entry.get("electrolyte_notes"))
            st.success(f"Loaded diet entry for {diet_date_string}.")

    with st.form("diet_entry_form"):
        left, middle, right = st.columns(3)

        with left:
            st.number_input("Carbs (g)", min_value=0.0, step=1.0, key="carbs_g")
            st.number_input("Protein (g)", min_value=0.0, step=1.0, key="protein_g")

        with middle:
            st.number_input("Fats (g)", min_value=0.0, step=1.0, key="fats_g")
            st.checkbox("Fasting", key="fasting")

        with right:
            st.text_area("Electrolyte notes", height=130, key="electrolyte_notes")

        submitted = st.form_submit_button("Save diet entry", type="primary")

    if not submitted:
        diet_entries_section(entries)
        return

    if existing_entry is None:
        st.warning(f"No daily health entry found for {diet_date_string}. Save Daily Health first, then add diet.")
        diet_entries_section(entries)
        return

    try:
        entry = _entry_from_row(
            existing_entry,
            carbs_g=st.session_state.carbs_g,
            protein_g=st.session_state.protein_g,
            fats_g=st.session_state.fats_g,
            fasting_yes_no=st.session_state.fasting,
            electrolyte_notes=st.session_state.electrolyte_notes.strip(),
        )
        save_entry(entry, overwrite=True)
    except ValidationError as error:
        st.error(str(error))
        diet_entries_section(entries)
        return

    st.success(f"Saved diet entry for {diet_date_string}.")
    diet_entries_section(load_entries())


def diet_entries_section(entries) -> None:
    section_heading("Recent Diet Entries")
    if entries.empty:
        st.info("Diet entries will appear after you save Daily Health and Diet data.")
        return

    diet_columns = [
        "date",
        "carbs_g",
        "protein_g",
        "fats_g",
        "fasting_yes_no",
        "electrolyte_notes",
    ]
    display = entries[diet_columns].tail(10).sort_values("date", ascending=False).copy()
    display["fasting_yes_no"] = display["fasting_yes_no"].map(yes_no_label)
    st.dataframe(display, width="stretch", hide_index=True)


def recent_entries_section() -> None:
    entries = load_entries()

    section_heading("Recent Entries")
    if entries.empty:
        st.info("No entries yet. Save your first daily entry above.")
        return

    display = entries.tail(10).sort_values("date", ascending=False).copy()
    display["migraine_yes_no"] = display["migraine_yes_no"].map(yes_no_label)
    display["rizatriptan_taken_yes_no"] = display["rizatriptan_taken_yes_no"].map(yes_no_label)
    st.dataframe(display, width="stretch", hide_index=True)


def charts_section() -> None:
    entries = load_entries()

    section_heading("Charts")
    if entries.empty:
        st.info("Charts will appear after you save data.")
        return

    tabs = st.tabs(["Trends", "Relationships"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(glucose_over_time_chart(entries), width="stretch")
            st.plotly_chart(headache_over_time_chart(entries), width="stretch")
        with col2:
            st.plotly_chart(ketones_over_time_chart(entries), width="stretch")
            st.plotly_chart(energy_over_time_chart(entries), width="stretch")
            st.plotly_chart(mood_stability_over_time_chart(entries), width="stretch")
            st.plotly_chart(sleep_hours_over_time_chart(entries), width="stretch")

    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                relationship_chart(entries, "glucose_mg_dl", "headache_severity_0_to_10", "Glucose vs Headache"),
                width="stretch",
            )
        with col2:
            st.plotly_chart(
                relationship_chart(entries, "ketones_mmol_l", "energy_1_to_10", "Ketones vs Energy"),
                width="stretch",
            )


def observations_section() -> None:
    entries = load_entries()

    section_heading("Observations")
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
    st.dataframe(observations["migraine_comparison"], width="stretch", hide_index=True)


daily_health_tab, diet_tab = st.tabs(["Daily Health", "Diet"])

with daily_health_tab:
    entry_form()
    st.divider()
    recent_entries_section()
    st.divider()
    charts_section()
    st.divider()
    observations_section()

with diet_tab:
    diet_form()

st.markdown(f'<p class="hm-data-file">Data file: {DEFAULT_CSV_PATH}</p>', unsafe_allow_html=True)
