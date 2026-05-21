"""
Generate synthetic LOBSTER-format sample data for testing.

Produces a small message + orderbook file pair that mimics LOBSTER's CSV format.
Useful for running the pipeline before downloading real data.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample(
    ticker: str = "SAMPLE",
    date: str = "2023-01-03",
    n_events: int = 1000,
    depth: int = 10,
    output_dir: str = "data/samples",
    seed: int = 42,
):
    """Generate synthetic LOBSTER message + orderbook files."""
    rng = np.random.default_rng(seed)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ── Messages ──
    # Time: random within trading hours (09:30–16:00 ET)
    times = np.sort(rng.uniform(34200, 57600, n_events))

    # Types: weighted toward submissions and cancellations
    types = rng.choice(
        [1, 2, 3, 4, 5],
        size=n_events,
        p=[0.35, 0.15, 0.20, 0.25, 0.05],
    )

    order_ids = rng.integers(1, 1_000_000, size=n_events)
    sizes = rng.integers(1, 500, size=n_events) * 100  # Round lots
    directions = rng.choice([1, -1], size=n_events)

    # Price: random walk around $150
    base_price = 150.0
    price_changes = rng.normal(0, 0.01, n_events).cumsum()
    prices = ((base_price + price_changes) * 10_000).astype(int)

    messages = pd.DataFrame({
        0: times,
        1: types,
        2: order_ids,
        3: sizes,
        4: prices,
        5: directions,
    })

    # ── Orderbook ──
    ob_data = []
    for i in range(n_events):
        mid = prices[i] / 10_000
        row = []
        for level in range(1, depth + 1):
            spread_half = 0.01 * level + rng.uniform(0, 0.005)
            ask_p = int((mid + spread_half) * 10_000)
            bid_p = int((mid - spread_half) * 10_000)
            ask_s = int(rng.integers(100, 5000))
            bid_s = int(rng.integers(100, 5000))
            row.extend([ask_p, ask_s, bid_p, bid_s])
        ob_data.append(row)

    orderbook = pd.DataFrame(ob_data)

    # ── Write CSVs ──
    prefix = f"{ticker}_{date}_34200_57600"
    msg_path = Path(output_dir) / f"{prefix}_message_{depth}.csv"
    ob_path = Path(output_dir) / f"{prefix}_orderbook_{depth}.csv"

    messages.to_csv(msg_path, index=False, header=False)
    orderbook.to_csv(ob_path, index=False, header=False)

    print(f"Generated {n_events} events → {msg_path.name}, {ob_path.name}")
    return msg_path, ob_path


if __name__ == "__main__":
    generate_sample()
