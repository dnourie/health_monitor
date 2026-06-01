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
