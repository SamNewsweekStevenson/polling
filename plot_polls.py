#!/usr/bin/env python3
"""Generate interactive Plotly HTML visualisations from poll_data.csv.

Creates `polls.html` in the same folder. Uses `plotly` and `pandas`.
"""
from pathlib import Path
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from plotly.offline import plot


DATA_FILE = Path(__file__).parent / "poll_data.csv"
OUT_FILE = Path(__file__).parent / "polls.html"
BRAND_IMG = "https://www.logolounge.com/wp-content/uploads/2025/10/newsweek-wordmark-new-1024x253.png"


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # keep only numeric approve/disapprove
    df = df.dropna(subset=["approve", "disapprove"]).copy()
    df["approve"] = pd.to_numeric(df["approve"], errors="coerce")
    df["disapprove"] = pd.to_numeric(df["disapprove"], errors="coerce")
    df = df.dropna(subset=["approve", "disapprove"]) 
    return df


def make_figure(df: pd.DataFrame):
    top50 = df.head(50).reset_index(drop=True)
    top10 = df.head(10).reset_index(drop=True)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.55, 0.30, 0.15],
                        vertical_spacing=0.04,
                        subplot_titles=("Top 50 Most Recent Polls: Approve vs Disapprove",
                                        "Most Recent 10 Polls",
                                        "Rolling average (window=3) — most recent 10 polls"))

    x50 = top50["pollster"] + " — " + top50["date"]
    x10 = top10["pollster"] + " — " + top10["date"]

    fig.add_trace(go.Scatter(x=x50, y=top50["approve"], mode="lines+markers",
                             name="Approve", line=dict(color="#1f77b4")), row=1, col=1)
    fig.add_trace(go.Scatter(x=x50, y=top50["disapprove"], mode="lines+markers",
                             name="Disapprove", line=dict(color="#d62728")), row=1, col=1)

    fig.add_trace(go.Scatter(x=x10, y=top10["approve"], mode="lines+markers",
                             name="Approve (last 10)", line=dict(color="#1f77b4")), row=2, col=1)
    fig.add_trace(go.Scatter(x=x10, y=top10["disapprove"], mode="lines+markers",
                             name="Disapprove (last 10)", line=dict(color="#d62728")), row=2, col=1)

    # rolling average for top10
    roll_window = 3
    r_approve = top10["approve"].rolling(window=roll_window, min_periods=1).mean()
    r_disapprove = top10["disapprove"].rolling(window=roll_window, min_periods=1).mean()

    fig.add_trace(go.Scatter(x=x10, y=r_approve, mode="lines+markers",
                             name=f"Approve {roll_window}-pt rolling avg", line=dict(color="#1f77b4")), row=3, col=1)
    fig.add_trace(go.Scatter(x=x10, y=r_disapprove, mode="lines+markers",
                             name=f"Disapprove {roll_window}-pt rolling avg", line=dict(color="#d62728")), row=3, col=1)

    fig.update_layout(height=900, width=1200,
                      title_text="Donald Trump Approval — Newsweek",
                      margin=dict(t=120, b=80))

    # add Newsweek branding image (will reference the file in same folder)
    fig.update_layout(images=[dict(
        source=BRAND_IMG,
        xref="paper", yref="paper",
        x=0.01, y=1.12,
        sizex=0.28, sizey=0.16,
        xanchor="left", yanchor="top",
        layer="above"
    )])

    # footer credit
    fig.add_annotation(text="Created by Sam Stevenson, Associate News Editor",
                       xref="paper", yref="paper",
                       x=0.5, y=-0.03, showarrow=False,
                       font=dict(size=12), align="center")

    # improve axes
    fig.update_xaxes(tickangle=45, tickfont=dict(size=10))
    fig.update_yaxes(title_text="Percent", rangemode="tozero")

    return fig


def main():
    if not DATA_FILE.exists():
        print(f"Data file not found: {DATA_FILE}")
        return
    df = load_data(DATA_FILE)
    if df.empty:
        print("No valid rows found in CSV.")
        return

    fig = make_figure(df)

    # write HTML with plotly.js loaded from CDN and the image reference
    plot(fig, filename=str(OUT_FILE), auto_open=False, include_plotlyjs='cdn')
    print(f"Wrote: {OUT_FILE}")


if __name__ == "__main__":
    main()
