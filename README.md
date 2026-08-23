# Black-Scholes Options Pricing and Risk Dashboard

A focused derivatives-pricing application for European options, combining a standalone numerical engine with an interactive Streamlit risk dashboard.

## Capabilities

- Closed-form European call and put valuation.
- Delta, Gamma, Theta, Vega, and Rho for both option types.
- Implied-volatility estimation with Brent's root-finding method.
- Option-value heatmaps across spot price and volatility.
- Three-dimensional Greek sensitivity surfaces.
- Call and put payoff/P&L curves with break-even levels.
- Optional Yahoo Finance spot lookup and `^TNX` Treasury-yield rate proxy.

## Model

For spot price `S`, strike `K`, maturity `T`, risk-free rate `r`, and volatility `σ`:

```text
d1 = [ln(S / K) + (r + σ² / 2)T] / (σ√T)
d2 = d1 - σ√T

Call = S N(d1) - K e^(-rT) N(d2)
Put  = K e^(-rT) N(-d2) - S N(-d1)
```

The pricing layer is isolated in `engine.py`; `app.py` provides Streamlit controls, tables, and Plotly visualizations. Implied volatility is found by matching the model and observed option prices over a bounded interval.

## Reference validation

For `S = 100`, `K = 100`, `T = 1`, `r = 5%`, and `σ = 20%`:

| Instrument | Theoretical value |
| --- | ---: |
| European call | `10.4506` |
| European put | `5.5735` |

## Dashboard

- **Overview:** prices, model inputs, and the complete Greek set.
- **Sensitivity Heatmaps:** call and put values over spot/volatility grids.
- **3D Greeks:** interactive Delta, Gamma, Theta, Vega, or Rho surfaces.
- **P&L Curves:** expiration payoff after the entered premium.
- **Implied Volatility:** volatility backed out from a market option price.

## Run locally

```bash
git clone https://github.com/addicteduser04/Black-Scholes-Model.git
cd Black-Scholes-Model
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The stack is Python, NumPy, pandas, SciPy, Plotly, Streamlit, and optional Yahoo Finance data.

## Repository map

```text
engine.py              pricing, Greeks, implied volatility, and grid functions
app.py                 Streamlit dashboard and market-data helper
requirements.txt       runtime dependencies
.streamlit/config.toml interface theme configuration
```

## Assumptions and limitations

The model assumes European exercise, no dividends, constant volatility, a constant risk-free rate, lognormal price dynamics, continuous trading, and frictionless markets. The `^TNX` lookup is a convenient rate proxy rather than maturity-matched curve construction. The application does not model volatility smiles, early exercise, transaction costs, discrete hedging, or market microstructure.

This is an educational pricing and risk-analysis tool, not trading or investment advice.

## Author

**Sifeddine El Kadiri** — Finance & Computer Science Engineering Student at ENSIAS
