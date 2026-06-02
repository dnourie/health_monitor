from __future__ import annotations

import pandas as pd


COMPARISON_COLUMNS = [
    "glucose_mg_dl",
    "ketones_mmol_l",
    "energy_1_to_10",
    "mood_stability_1_to_10",
    "sleep_hours",
    "headache_severity_0_to_10",
]


def build_observations(entries: pd.DataFrame) -> dict[str, object]:
    if entries.empty:
        return {
            "entry_count": 0,
            "migraine_days": 0,
            "rizatriptan_days": 0,
            "high_headache_days": 0,
            "migraine_comparison": pd.DataFrame(),
        }

    migraine_days = entries["migraine_yes_no"].sum()
    rizatriptan_days = entries["rizatriptan_taken_yes_no"].sum()
    high_headache_days = (entries["headache_severity_0_to_10"] >= 7).sum()

    comparison = (
        entries.groupby("migraine_yes_no")[COMPARISON_COLUMNS]
        .mean(numeric_only=True)
        .round(2)
        .reset_index()
    )
    comparison["migraine_yes_no"] = comparison["migraine_yes_no"].map({False: "Non-migraine days", True: "Migraine days"})

    return {
        "entry_count": len(entries),
        "migraine_days": int(migraine_days),
        "rizatriptan_days": int(rizatriptan_days),
        "high_headache_days": int(high_headache_days),
        "migraine_comparison": comparison,
    }
