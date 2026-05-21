# Limit-Order-Book-Research

Market microstructure research using NASDAQ limit order book data from [LOBSTER](https://lobsterdata.com/).

## Project Overview

This project studies intraday market microstructure dynamics using reconstructed limit order book (LOB) data. Focus areas include:

- **Order book shape & dynamics** — depth profiles, order imbalance, resilience after trades
- **Price impact** — permanent vs. transient impact, Kyle's lambda estimation
- **Spread decomposition** — informed vs. inventory vs. order-processing components
- **Intraday patterns** — volatility seasonality, volume clustering, quote activity
- **High-frequency signals** — order flow imbalance (OFI), trade informativeness, VPIN

## Data

**Source:** [LOBSTER](https://lobsterdata.com/) (Limit Order Book System — The Efficient Reconstructor)

LOBSTER provides NASDAQ historical order book data at arbitrary depth levels. Each instrument-day consists of two files:

| File | Description |
|------|-------------|
| `{TICKER}_{DATE}_{FROM}_{TO}_message_{DEPTH}.csv` | Event-by-event message file (order submissions, cancellations, executions) |
| `{TICKER}_{DATE}_{FROM}_{TO}_orderbook_{DEPTH}.csv` | Order book snapshot after each event (bid/ask prices & volumes at N levels) |

**Message types:** 1 = new limit order, 2 = partial cancellation, 3 = full cancellation, 4 = visible execution, 5 = hidden execution, 7 = trading halt

> ⚠️ Raw LOBSTER data is **not included** in this repo (licensed, large files). Place downloaded files in `data/raw/` — they are gitignored. A small synthetic sample is provided in `data/samples/` for testing.

## Project Structure

```
Limit-Order-Book-Research/
├── configs/              # YAML configs for data paths, parameters
├── data/
│   ├── raw/              # LOBSTER downloads (gitignored)
│   ├── processed/        # Cleaned & feature-enriched data (gitignored)
│   └── samples/          # Small synthetic samples for testing
├── notebooks/            # Exploratory analysis & figures
├── src/
│   ├── data_processing/  # LOBSTER parsing, cleaning, resampling
│   ├── features/         # Microstructure feature extraction
│   ├── models/           # Statistical models & estimation
│   └── visualization/    # Plotting utilities
├── results/
│   ├── figures/          # Generated plots
│   └── tables/           # LaTeX tables for write-up
├── tests/                # Unit tests
├── requirements.txt
└── README.md
```

## Setup

```bash
git clone https://github.com/<YOUR_USERNAME>/Limit-Order-Book-Research.git
cd Limit-Order-Book-Research
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# 1. Place LOBSTER data in data/raw/
# 2. Parse and clean
python -m src.data_processing.parse_lobster --ticker AAPL --date 2023-01-03

# 3. Extract features
python -m src.features.order_imbalance --ticker AAPL --date 2023-01-03

# 4. Run analysis notebooks
jupyter lab notebooks/
```

## Key References

- Huang, R. & Polak, T. (2011). *LOBSTER: Limit Order Book Reconstruction System.* Working Paper.
- Cont, R., Kukanov, A., & Stoikov, S. (2014). *The Price Impact of Order Book Events.* Journal of Financial Econometrics.
- Gould, M. D. et al. (2013). *Limit Order Books.* Quantitative Finance.
- Kyle, A. S. (1985). *Continuous Auctions and Insider Trading.* Econometrica.
- Easley, D. et al. (2012). *Flow Toxicity and Liquidity in a High-Frequency World.* Review of Financial Studies.

## License

MIT
