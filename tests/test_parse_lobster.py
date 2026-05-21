"""Tests for LOBSTER data parsing."""

import sys
from pathlib import Path

import pytest
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_processing.generate_sample import generate_sample
from src.data_processing.parse_lobster import (
    load_lobster,
    filter_trading_hours,
    remove_trading_halts,
    PRICE_FACTOR,
)


@pytest.fixture(scope="module")
def sample_data(tmp_path_factory):
    """Generate sample data once for all tests."""
    tmpdir = str(tmp_path_factory.mktemp("lobster"))
    generate_sample(
        ticker="TEST", date="2023-01-03",
        n_events=500, depth=10, output_dir=tmpdir,
    )
    msgs, ob = load_lobster(tmpdir, "TEST", "2023-01-03", depth=10)
    return msgs, ob


def test_row_count_match(sample_data):
    msgs, ob = sample_data
    assert len(msgs) == len(ob)


def test_prices_are_dollars(sample_data):
    msgs, ob = sample_data
    # Prices should be in reasonable dollar range, not raw LOBSTER integers
    assert msgs["price"].median() < 1000
    assert msgs["price"].median() > 1
    assert ob["mid_price"].median() < 1000


def test_spread_positive(sample_data):
    _, ob = sample_data
    assert (ob["spread"] >= 0).all()


def test_message_types_valid(sample_data):
    msgs, _ = sample_data
    valid_types = {1, 2, 3, 4, 5, 7}
    assert set(msgs["type"].unique()).issubset(valid_types)


def test_filter_trading_hours(sample_data):
    msgs, ob = sample_data
    msgs_f, ob_f = filter_trading_hours(msgs, ob)
    assert len(msgs_f) == len(ob_f)
    assert msgs_f["time"].min() >= 34200
    assert msgs_f["time"].max() <= 57600


def test_remove_halts(sample_data):
    msgs, ob = sample_data
    msgs_f, ob_f = remove_trading_halts(msgs, ob)
    assert 7 not in msgs_f["type"].values
