from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _chart_data(entries: pd.DataFrame) -> pd.DataFrame:
    chart_data = entries.copy()
    chart_data["date"] = pd.to_datetime(chart_data["date"])
    return chart_data.sort_values("date")


def _line_chart(entries: pd.DataFrame, y_column: str, title: str, y_label: str) -> go.Figure:
    chart_data = _chart_data(entries)
    figure = px.line(chart_data, x="date", y=y_column, markers=True, title=title)
    figure.update_layout(xaxis_title="Date", yaxis_title=y_label)
    return figure


def glucose_over_time_chart(entries: pd.DataFrame) -> go.Figure:
    return _line_chart(entries, "glucose_mg_dl", "Glucose Over Time", "Glucose (mg/dL)")


def ketones_over_time_chart(entries: pd.DataFrame) -> go.Figure:
    return _line_chart(entries, "ketones_mmol_l", "Ketones Over Time", "Ketones (mmol/L)")


def headache_over_time_chart(entries: pd.DataFrame) -> go.Figure:
    return _line_chart(
        entries,
        "headache_severity_0_to_10",
        "Headache Severity Over Time",
        "Headache severity",
    )


def energy_over_time_chart(entries: pd.DataFrame) -> go.Figure:
    return _line_chart(entries, "energy_1_to_10", "Energy Over Time", "Energy")


def mood_stability_over_time_chart(entries: pd.DataFrame) -> go.Figure:
    return _line_chart(entries, "mood_stability_1_to_10", "Mood Stability Over Time", "Mood stability")


def sleep_hours_over_time_chart(entries: pd.DataFrame) -> go.Figure:
    return _line_chart(entries, "sleep_hours", "Sleep Hours Over Time", "Sleep hours")


def relationship_chart(entries: pd.DataFrame, x_column: str, y_column: str, title: str) -> go.Figure:
    chart_data = _chart_data(entries)
    figure = px.scatter(
        chart_data,
        x=x_column,
        y=y_column,
        color="migraine_yes_no",
        hover_data=["date", "notes"],
        title=title,
    )
    figure.update_layout(xaxis_title=x_column.replace("_", " "), yaxis_title=y_column.replace("_", " "))
    return figure


def ketomojo_measure_chart(sessions: pd.DataFrame, y_column: str, title: str, y_label: str) -> go.Figure:
    chart_data = sessions.dropna(subset=[y_column]).copy()
    chart_data["session_time"] = pd.to_datetime(chart_data["session_time"])
    chart_data = chart_data.sort_values("session_time")
    figure = px.line(chart_data, x="session_time", y=y_column, markers=True, title=title)
    figure.update_layout(xaxis_title="Date", yaxis_title=y_label)
    return figure


def ketomojo_rolling_chart(sessions: pd.DataFrame) -> go.Figure:
    chart_data = sessions.copy()
    chart_data["session_time"] = pd.to_datetime(chart_data["session_time"])
    chart_data = chart_data.set_index("session_time")[["glucose", "ketone", "glucose_ketone_index"]]
    rolling = chart_data.rolling("14D", min_periods=3).mean().reset_index()
    rolling_long = rolling.melt(
        id_vars="session_time",
        value_vars=["glucose", "ketone", "glucose_ketone_index"],
        var_name="measure",
        value_name="rolling_mean",
    ).dropna()
    figure = px.line(
        rolling_long,
        x="session_time",
        y="rolling_mean",
        color="measure",
        facet_row="measure",
        title="Keto-Mojo 14-Day Rolling Averages",
    )
    figure.update_yaxes(matches=None)
    figure.update_layout(xaxis_title="Date", yaxis_title="Rolling mean", showlegend=False)
    return figure


def ketomojo_time_of_day_chart(sessions: pd.DataFrame) -> go.Figure:
    chart_data = sessions.melt(
        id_vars=["time_of_day"],
        value_vars=["glucose", "ketone", "glucose_ketone_index"],
        var_name="measure",
        value_name="value",
    ).dropna()
    figure = px.box(
        chart_data,
        x="time_of_day",
        y="value",
        color="measure",
        facet_row="measure",
        points="all",
        title="Keto-Mojo Patterns by Time of Day",
    )
    figure.update_yaxes(matches=None)
    figure.update_layout(xaxis_title="Time of day", yaxis_title="Value", showlegend=False)
    return figure


def ketomojo_gki_category_chart(sessions: pd.DataFrame) -> go.Figure:
    categories = pd.cut(
        sessions["glucose_ketone_index"].dropna(),
        bins=[-float("inf"), 1, 3, 6, 9, float("inf")],
        labels=["<=1", "1-3", "3-6", "6-9", ">9"],
    )
    counts = categories.value_counts().sort_index().rename_axis("GKI range").reset_index(name="sessions")
    figure = px.bar(counts, x="GKI range", y="sessions", title="GKI Category Counts")
    figure.update_layout(xaxis_title="GKI range", yaxis_title="Sessions")
    return figure
