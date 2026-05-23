# Black-Scholes Dashboard

An interactive Streamlit application for pricing European call and put options with the Black-Scholes model. The project combines a standalone quantitative pricing engine with a clean dashboard for risk analysis, sensitivity visualization, payoff inspection, and implied volatility estimation.

## Overview

This project is structured in two layers:

- `engine.py`: pure pricing logic, Greeks, implied volatility, heatmap matrix generation, and payoff functions
- `app.py`: Streamlit user interface, market-data helpers, KPI cards, tabs, and interactive charts

The dashboard is designed to feel more like a mini trading analytics tool than a simple calculator.

## Features

- Black-Scholes pricing for European calls and puts
- Full Greeks output: Delta, Gamma, Theta, Vega, and Rho
- Sensitivity heatmaps across spot price and volatility
- Profit and loss curves at expiration
- Implied volatility solver from observed market price
- Optional live price lookup with `yfinance`
- Risk-free rate proxy using the `^TNX` Treasury yield ticker

## Pricing Model

For spot price `S`, strike `K`, time to maturity `T`, risk-free rate `r`, and volatility `sigma`:

```text
d1 = [ln(S / K) + (r + sigma^2 / 2)T] / [sigma * sqrt(T)]
d2 = d1 - sigma * sqrt(T)

Call = S * N(d1) - K * e^(-rT) * N(d2)
Put  = K * e^(-rT) * N(-d2) - S * N(-d1)
```

The engine also computes the standard Greeks so the app can be used for both pricing and risk interpretation.

## Dashboard Layout

- **Sidebar inputs**: spot, strike, maturity, rate, volatility, premium, and heatmap resolution
- **Top metrics**: call price, put price, and maturity summary
- **Overview tab**: option Greeks and model snapshot
- **Sensitivity Heatmaps tab**: option value surfaces across spot and volatility
- **P&L Curves tab**: payoff and break-even analysis at expiration
- **Implied Volatility tab**: back out volatility from a market option price

## Project Structure

```text
.
├── app.py
├── engine.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run The App

```bash
streamlit run app.py
```

Once the server starts, open the local Streamlit URL shown in your terminal.

## Dependencies

The project uses:

- `streamlit` for the dashboard
- `numpy` and `pandas` for numerical work and data shaping
- `scipy` for the normal distribution and root finding
- `plotly` for interactive charts
- `yfinance` for optional live market data

## Validation Case

Use the standard textbook example below to verify the pricing engine:

- `S = 100`
- `K = 100`
- `T = 1`
- `r = 0.05`
- `sigma = 0.20`

Expected theoretical values:

- Call price: `10.4506`
- Put price: `5.5735`

## Assumptions And Limitations

The Black-Scholes framework assumes:

- European exercise
- Constant volatility
- Constant risk-free rate
- No dividends in the current implementation
- Lognormal asset-price dynamics and frictionless markets

This makes the dashboard a strong educational and portfolio project, but not a full production options system.

## Possible Extensions

- Dividend yield support
- Historical volatility estimation from price data
- Volatility smile or term-structure views
- Strategy payoffs for spreads, straddles, and strangles
- Monte Carlo pricing comparison
- Option chain integration for real market contracts

## Quick Start Summary

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
