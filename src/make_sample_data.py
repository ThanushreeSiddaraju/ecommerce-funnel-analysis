"""Generate a sample clickstream file in the exact schema of the public
REES46 "eCommerce behavior data from multi category store" dataset (Kaggle).

The real dataset is tens of GB and needs a Kaggle login, so this script builds a
small file with the same columns so the project runs out of the box:

    event_time, event_type, product_id, category_id, category_code,
    brand, price, user_id, user_session

event_type is one of: view, cart, remove_from_cart, purchase.

Rates are tuned so the funnel shape resembles what analysts report for the
real REES46 data (most sessions only browse; a small share add to cart; roughly
half of carts convert). Swap in the real CSV with `load_data.py --csv`.
"""
import argparse
import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

CATEGORIES = {
    # category_code: (price range, cart propensity multiplier, purchase multiplier)
    "electronics.smartphone": ((120, 1200), 1.30, 1.10),
    "electronics.audio.headphone": ((20, 350), 1.15, 1.00),
    "computers.notebook": ((350, 2200), 0.70, 0.80),
    "appliances.kitchen.refrigerators": ((300, 1800), 0.60, 0.85),
    "apparel.shoes": ((25, 180), 1.00, 0.70),
    "furniture.living_room.sofa": ((200, 1500), 0.45, 0.60),
    "construction.tools.drill": ((40, 300), 0.90, 1.05),
    "kids.toys": ((10, 120), 1.10, 0.95),
}
BRANDS = {
    "electronics.smartphone": ["samsung", "apple", "xiaomi", "huawei"],
    "electronics.audio.headphone": ["sony", "jbl", "apple", "samsung"],
    "computers.notebook": ["lenovo", "hp", "asus", "acer"],
    "appliances.kitchen.refrigerators": ["lg", "samsung", "bosch", "beko"],
    "apparel.shoes": ["nike", "adidas", "puma", "skechers"],
    "furniture.living_room.sofa": ["ikea", "brw", "divan", "comfort"],
    "construction.tools.drill": ["bosch", "makita", "dewalt", "ryobi"],
    "kids.toys": ["lego", "hasbro", "mattel", "playmobil"],
}

BASE_CART_RATE = 0.11      # P(session adds anything to cart)
BASE_PURCHASE_RATE = 0.50  # P(purchase | added to cart)
REMOVE_RATE = 0.18         # P(remove_from_cart | cart, no purchase)


def build_catalog(rng):
    catalog = []
    pid = 1000000
    for cat_idx, (code, ((lo, hi), _, _)) in enumerate(CATEGORIES.items()):
        for _ in range(60):
            pid += rng.randint(1, 50)
            catalog.append({
                "product_id": pid,
                "category_id": 2053013555631882000 + cat_idx,
                "category_code": code,
                "brand": rng.choice(BRANDS[code]),
                "price": round(rng.uniform(lo, hi), 2),
            })
    return catalog


def main(n_users: int, out: Path, seed: int):
    rng = random.Random(seed)
    catalog = build_catalog(rng)
    by_cat = {}
    for p in catalog:
        by_cat.setdefault(p["category_code"], []).append(p)

    start = datetime(2019, 11, 1)
    rows = []
    for user_id in range(512000000, 512000000 + n_users):
        for _ in range(max(1, int(rng.expovariate(1 / 1.8)))):  # sessions per user
            session = str(uuid.UUID(int=rng.getrandbits(128)))
            t = start + timedelta(seconds=rng.randint(0, 30 * 24 * 3600))
            cat = rng.choice(list(CATEGORIES))
            _, cart_mult, buy_mult = CATEGORIES[cat]
            n_views = 1 + int(rng.expovariate(1 / 2.5))
            viewed = [rng.choice(by_cat[cat]) for _ in range(n_views)]

            def emit(event, p):
                nonlocal t
                t += timedelta(seconds=rng.randint(5, 240))
                rows.append([t.strftime("%Y-%m-%d %H:%M:%S UTC"), event, p["product_id"],
                             p["category_id"], p["category_code"], p["brand"], p["price"],
                             user_id, session])

            for p in viewed:
                emit("view", p)

            # more browsing -> more intent; expensive items -> less
            engagement = min(1.8, 0.6 + 0.25 * n_views)
            if rng.random() < BASE_CART_RATE * cart_mult * engagement:
                item = rng.choice(viewed)
                emit("cart", item)
                price_penalty = 1.15 if item["price"] < 100 else 0.85 if item["price"] > 800 else 1.0
                if rng.random() < BASE_PURCHASE_RATE * buy_mult * price_penalty:
                    emit("purchase", item)
                elif rng.random() < REMOVE_RATE:
                    emit("remove_from_cart", item)

    rows.sort(key=lambda r: r[0])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event_time", "event_type", "product_id", "category_id", "category_code",
                    "brand", "price", "user_id", "user_session"])
        w.writerows(rows)
    print(f"wrote {len(rows):,} events to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=25000)
    ap.add_argument("--out", type=Path, default=Path("data/events_sample.csv"))
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    main(a.users, a.out, a.seed)
