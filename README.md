# Personal Health Monitor

Version 1.1.0

A simple local Streamlit app for tracking glucose, ketones, sleep quality and hours, headache symptoms, migraine days, energy, mood stability, diet, medication use, and notes. It can also import Keto-Mojo CSV exports so glucose, ketone, and GKI readings do not need to be typed manually. The goal is to make it easier to notice possible correlations between these measures over time.

This project is for personal tracking and reflection only. It is not medical advice, diagnosis, or a replacement for care from a qualified clinician.

## What It Tracks

The daily form keeps the core tracking fields small:

- Date
- Reading time
- Optional manual glucose in mg/dL
- Optional manual ketones in mmol/L
- Headache severity from 0 to 10
- Migraine yes/no
- Energy from 1 to 10
- Mood stability from 1 to 10
- Sleep quality: Good, Disrupted, or Poor
- Sleep hours from 0 to 14
- Rizatriptan taken yes/no
- Carbs, protein, and fats in grams
- Fasting yes/no
- Electrolyte notes
- Notes

The Keto-Mojo tab imports CSV exports from the meter app. Uploading the full export each week is supported; the app stores imported readings separately and skips duplicate rows automatically.

The notes field is intentionally flexible. It can include weather or rain, stress, unusual foods, fasting, electrolytes, caffeine, exercise, medication details, or anything else that felt relevant that day.

## Project Structure

```text
health_monitor/
  app.py
  assets/
    styles.css
  data/
  src/
    __init__.py
    analysis.py
    charts.py
    data_model.py
    ketomojo.py
    storage.py
  notebooks/
    exploratory_analysis.ipynb
  README.md
  requirements.txt
```

## Install

From this folder, install the requirements:

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Or double-click this file in Finder:

```text
start_health_monitor.command
```

It starts the Streamlit server if needed and opens the app at:

```text
http://127.0.0.1:8501
```

Leave the terminal window open while using the app.

## Auto-Start on Mac

To have the server start automatically when you log in, run:

```bash
./scripts/install_autostart.sh
```

After that, open the app in your browser at:

```text
http://127.0.0.1:8501
```

To remove auto-start:

```bash
./scripts/uninstall_autostart.sh
```

The app stores data locally in:

```text
data/health_log.csv
data/ketomojo_readings.csv
data/ketomojo_import_history.csv
```

The CSV is created automatically the first time you save an entry.

Personal CSV data is ignored by Git by default so health entries do not get pushed to GitHub accidentally.

## Future Ideas

- Add richer Keto-Mojo analytics inside the app
- Add weather enrichment for rain, precipitation, pressure, humidity, and temperature swings
- Add monthly Markdown reports for doctor visits
- Add lag analysis to compare yesterday's factors with today's headache or migraine status
- Promote repeated note themes into structured fields if they prove useful
