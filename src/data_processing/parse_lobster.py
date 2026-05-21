"""
LOBSTER Data Parser
===================
Parse LOBSTER message and orderbook CSV files into clean DataFrames.

LOBSTER file format:
  - message file:    Time(s), Type, OrderID, Size, Price, Direction
  - orderbook file:  AskPrice1, AskSize1, BidPrice1, BidSize1, ..., AskPriceN, AskSizeN, BidPriceN, BidSizeN

Prices are in dollar-price × 10,000 (integer). E.g. 1234567 = $123.4567

Message types:
  1 = Submission of new limit order
  2 = Partial cancellation
  3 = Total cancellation
  4 = Execution of visible limit order
  5 = Execution of hidden limit order
  7 = Trading halt indicator
"""

import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


# ── Constants ──────────────────────────────────────────────────────

PRICE_FACTOR = 10_000  # LOBSTER prices → dollars

MSG_TYPES = {
    1: "submission",
    2: "partial_cancel",
    3: "total_cancel",
    4: "execution_visible",
    5: "execution_hidden",
    7: "trading_halt",
}

MSG_COLUMNS = ["time", "type", "order_id", "size", "price", "direction"]
# direction: 1 = buy, -1 = sell


def _find_lobster_files(
    data_dir: str, ticker: str, date: str
) -> tuple[Optional[str], Optional[str]]:
    """Find message and orderbook files for a given ticker-date."""
    data_path = Path(data_dir)
    msg_file = None
    ob_file = None

    for f in data_path.glob(f"{ticker}_{date}*"):
        name = f.name
        if "message" in name:
            msg_file = str(f)
        elif "orderbook" in name:
            ob_file = str(f)

    return msg_file, ob_file


def parse_messages(filepath: str) -> pd.DataFrame:
    """
    Parse a LOBSTER message file.

    Returns
    -------
    DataFrame with columns: time, type, type_str, order_id, size, price, direction
        - time: float, seconds after midnight ET
        - price: float, dollars (converted from LOBSTER integer format)
        - direction: 1 = buy, -1 = sell
    """
    df = pd.read_csv(filepath, header=None, names=MSG_COLUMNS)

    # Convert price from integer format to dollars
    df["price"] = df["price"] / PRICE_FACTOR

    # Add human-readable message type
    df["type_str"] = df["type"].map(MSG_TYPES).fillna("unknown")

    # Convert time to timedelta for easier manipulation
    df["timestamp"] = pd.to_timedelta(df["time"], unit="s")

    return df


def parse_orderbook(filepath: str, depth: int = 10) -> pd.DataFrame:
    """
    Parse a LOBSTER orderbook file.

    Parameters
    ----------
    filepath : str
        Path to orderbook CSV.
    depth : int
        Number of price levels on each side.

    Returns
    -------
    DataFrame with columns: ask_price_1, ask_size_1, bid_price_1, bid_size_1, ...
    """
    # Build column names
    columns = []
    for i in range(1, depth + 1):
        columns.extend([
            f"ask_price_{i}", f"ask_size_{i}",
            f"bid_price_{i}", f"bid_size_{i}",
        ])

    df = pd.read_csv(filepath, header=None, names=columns)

    # Convert prices to dollars
    price_cols = [c for c in df.columns if "price" in c]
    df[price_cols] = df[price_cols] / PRICE_FACTOR

    return df


def load_lobster(
    data_dir: str,
    ticker: str,
    date: str,
    depth: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and align LOBSTER message + orderbook files for one ticker-date.

    Parameters
    ----------
    data_dir : str
        Directory containing LOBSTER CSV files.
    ticker : str
        Stock ticker (e.g. "AAPL").
    date : str
        Date string as used in filename (e.g. "2023-01-03").
    depth : int
        Order book depth levels.

    Returns
    -------
    messages : DataFrame
        Event-by-event messages.
    orderbook : DataFrame
        Order book state after each event (same row count as messages).
    """
    msg_file, ob_file = _find_lobster_files(data_dir, ticker, date)

    if msg_file is None or ob_file is None:
        available = list(Path(data_dir).glob(f"{ticker}*"))
        raise FileNotFoundError(
            f"LOBSTER files not found for {ticker} on {date} in {data_dir}. "
            f"Found: {[f.name for f in available]}"
        )

    messages = parse_messages(msg_file)
    orderbook = parse_orderbook(ob_file, depth=depth)

    # Sanity check: row counts must match
    assert len(messages) == len(orderbook), (
        f"Row count mismatch: {len(messages)} messages vs "
        f"{len(orderbook)} orderbook snapshots"
    )

    # Add key derived fields to orderbook
    orderbook["mid_price"] = (
        orderbook["ask_price_1"] + orderbook["bid_price_1"]
    ) / 2
    orderbook["spread"] = (
        orderbook["ask_price_1"] - orderbook["bid_price_1"]
    )
    orderbook["spread_bps"] = (
        orderbook["spread"] / orderbook["mid_price"] * 10_000
    )

    # Attach timestamp from messages
    orderbook["time"] = messages["time"].values
    orderbook["timestamp"] = messages["timestamp"].values

    print(f"Loaded {ticker} {date}: {len(messages):,} events, "
          f"{depth} depth levels")
    print(f"  Time range: {messages['time'].iloc[0]:.1f}s – "
          f"{messages['time'].iloc[-1]:.1f}s")
    print(f"  Mid price: ${orderbook['mid_price'].iloc[0]:.2f} → "
          f"${orderbook['mid_price'].iloc[-1]:.2f}")
    print(f"  Median spread: {orderbook['spread_bps'].median():.1f} bps")

    return messages, orderbook


# ── Filtering & Cleaning ──────────────────────────────────────────

def filter_trading_hours(
    messages: pd.DataFrame,
    orderbook: pd.DataFrame,
    market_open: float = 34200,   # 09:30 ET
    market_close: float = 57600,  # 16:00 ET
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep only events within regular trading hours."""
    mask = (messages["time"] >= market_open) & (messages["time"] <= market_close)
    return messages.loc[mask].reset_index(drop=True), \
           orderbook.loc[mask].reset_index(drop=True)


def remove_trading_halts(
    messages: pd.DataFrame,
    orderbook: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove trading halt events (type 7)."""
    mask = messages["type"] != 7
    return messages.loc[mask].reset_index(drop=True), \
           orderbook.loc[mask].reset_index(drop=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python parse_lobster.py <data_dir> <ticker> <date>")
        print("Example: python parse_lobster.py data/raw AAPL 2023-01-03")
        sys.exit(1)

    data_dir, ticker, date = sys.argv[1], sys.argv[2], sys.argv[3]
    msgs, ob = load_lobster(data_dir, ticker, date)
    msgs_clean, ob_clean = filter_trading_hours(msgs, ob)
    msgs_clean, ob_clean = remove_trading_halts(msgs_clean, ob_clean)
    print(f"\nAfter cleaning: {len(msgs_clean):,} events")
