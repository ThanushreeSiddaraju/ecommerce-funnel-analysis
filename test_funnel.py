"""Sanity checks on the funnel SQL using a tiny hand-built event log.

Run with:  python -m pytest -q   (or just: python test_funnel.py)
"""
import sqlite3
from pathlib import Path

import pandas as pd

SQL = Path(__file__).parent / "sql"

EVENTS = [
    # session a: views 2 products, carts, buys  -> reaches every step
    ("2019-11-01 10:00:00 UTC", "view", 1, "s_a"),
    ("2019-11-01 10:01:00 UTC", "view", 2, "s_a"),
    ("2019-11-01 10:02:00 UTC", "cart", 2, "s_a"),
    ("2019-11-01 10:03:00 UTC", "purchase", 2, "s_a"),
    # session b: views 2 products, carts, abandons
    ("2019-11-01 11:00:00 UTC", "view", 1, "s_b"),
    ("2019-11-01 11:01:00 UTC", "view", 3, "s_b"),
    ("2019-11-01 11:02:00 UTC", "cart", 3, "s_b"),
    # session c: views 2 products, leaves
    ("2019-11-01 12:00:00 UTC", "view", 1, "s_c"),
    ("2019-11-01 12:01:00 UTC", "view", 4, "s_c"),
    # session d: single view, leaves
    ("2019-11-01 13:00:00 UTC", "view", 5, "s_d"),
]


def make_db():
    con = sqlite3.connect(":memory:")
    df = pd.DataFrame(EVENTS, columns=["event_time", "event_type", "product_id", "user_session"])
    df["category_id"], df["category_code"], df["brand"] = 1, "kids.toys", "lego"
    df["price"], df["user_id"] = 50.0, 1
    df.to_sql("events", con, index=False)
    con.executescript((SQL / "00_session_flags.sql").read_text())
    return con


def test_overall_funnel_counts():
    df = pd.read_sql_query((SQL / "01_funnel_overall.sql").read_text(), make_db())
    assert df["sessions"].tolist() == [4, 3, 2, 1]
    assert df["sessions_lost"].tolist()[1:] == [1, 1, 1]
    assert df["step_conversion_pct"].tolist()[3] == 50.0


def test_funnel_never_grows():
    df = pd.read_sql_query((SQL / "01_funnel_overall.sql").read_text(), make_db())
    assert df["sessions"].is_monotonic_decreasing


def test_cart_abandonment():
    df = pd.read_sql_query((SQL / "03_cart_abandonment_by_price.sql").read_text(), make_db())
    assert df.loc[0, "carted_sessions"] == 2
    assert df.loc[0, "abandoned"] == 1
    assert df.loc[0, "abandonment_pct"] == 50.0


def test_conversion_by_hour():
    df = pd.read_sql_query((SQL / "05_conversion_by_hour.sql").read_text(), make_db())
    assert df["hour_of_day"].tolist() == [10, 11, 12, 13]
    assert df["sessions"].sum() == 4


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
