"""Load clickstream events into SQLite, run the SQL in /sql, and export:

  output/*.csv              one file per query
  output/funnel.png         funnel chart
  output/funnel_report.xlsx all results + a native Excel funnel chart

Usage:
  python src/run_analysis.py                          # uses data/events_sample.csv
  python src/run_analysis.py --csv data/2019-Nov.csv  # real REES46 file from Kaggle
"""
import argparse
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR, OUT_DIR = ROOT / "sql", ROOT / "output"
COLS = ["event_time", "event_type", "product_id", "category_id", "category_code",
        "brand", "price", "user_id", "user_session"]


def load(csv_path: Path, db_path: Path, max_rows: int | None) -> sqlite3.Connection:
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    total = 0
    for chunk in pd.read_csv(csv_path, usecols=COLS, chunksize=500_000):
        if max_rows and total >= max_rows:
            break
        if max_rows:
            chunk = chunk.head(max_rows - total)
        chunk.to_sql("events", con, if_exists="append", index=False)
        total += len(chunk)
    con.execute("CREATE INDEX idx_session ON events(user_session)")
    print(f"loaded {total:,} events")
    return con


def run_queries(con) -> dict[str, pd.DataFrame]:
    con.executescript((SQL_DIR / "00_session_flags.sql").read_text())
    results = {}
    for f in sorted(SQL_DIR.glob("0[1-9]_*.sql")):
        name = f.stem[3:]
        results[name] = pd.read_sql_query(f.read_text(), con)
        results[name].to_csv(OUT_DIR / f"{f.stem}.csv", index=False)
    return results


def plot_funnel(df: pd.DataFrame, path: Path):
    worst = df["sessions_lost"].idxmax()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    widths = df["sessions"].to_numpy()
    colors = ["#c0392b" if i == worst else "#2c7fb8" for i in range(len(df))]
    y = range(len(df))[::-1]
    ax.barh(y, widths, left=(widths.max() - widths) / 2, color=colors, height=0.75)
    for yi, (_, r) in zip(y, df.iterrows()):
        wide = r.sessions > widths.max() * 0.35  # narrow bars get their label beside them
        ax.text(widths.max() / 2 if wide else (widths.max() + r.sessions) / 2 + widths.max() * 0.02, yi,
                f"{r.step}\n{int(r.sessions):,} sessions ({r.pct_of_top:.1f}%)",
                ha="center" if wide else "left", va="center", fontsize=10, fontweight="bold",
                color="white" if wide else "#222")
        if pd.notna(r.step_dropoff_pct):
            ax.text(widths.max() * 1.02, yi + 0.5, f"-{r.step_dropoff_pct:.1f}%",
                    va="center", color="#c0392b" if _ == worst else "#555", fontsize=10)
    ax.set_xlim(0, widths.max() * 1.15)
    ax.axis("off")
    ax.set_title(f"Session funnel — biggest leak: {df.loc[worst - 1, 'step'][3:]} → {df.loc[worst, 'step'][3:]} "
                 f"(loses {int(df.loc[worst, 'sessions_lost']):,} sessions)", fontsize=12, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_excel(results: dict[str, pd.DataFrame], path: Path):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, df in results.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
    wb = load_workbook(path)
    for ws in wb.worksheets:
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2C7FB8")
        for i, col in enumerate(ws.columns, 1):
            ws.column_dimensions[get_column_letter(i)].width = max(14, max(len(str(c.value or "")) for c in col) + 2)

    ws = wb["funnel_overall"]
    chart = BarChart()
    chart.type = "bar"
    chart.title = "Session funnel"
    chart.y_axis.title = "Sessions"
    chart.legend = None
    n = ws.max_row
    chart.add_data(Reference(ws, min_col=2, min_row=1, max_row=n), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=n))
    chart.x_axis.scaling.orientation = "maxMin"  # top step at the top, like a funnel
    chart.height, chart.width = 8, 18
    ws.add_chart(chart, "H2")
    wb.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=ROOT / "data" / "events_sample.csv")
    ap.add_argument("--max-rows", type=int, default=None, help="cap rows loaded from a huge file")
    a = ap.parse_args()
    OUT_DIR.mkdir(exist_ok=True)

    con = load(a.csv, ROOT / "data" / "events.db", a.max_rows)
    results = run_queries(con)
    plot_funnel(results["funnel_overall"], OUT_DIR / "funnel.png")
    write_excel(results, OUT_DIR / "funnel_report.xlsx")

    pd.set_option("display.width", 160)
    for name, df in results.items():
        print(f"\n== {name} ==\n{df.to_string(index=False)}")


if __name__ == "__main__":
    main()
