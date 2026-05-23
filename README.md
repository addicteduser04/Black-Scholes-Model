# Black-Scholes Dashboard

Interactive Streamlit dashboard for European option pricing with:

- Black-Scholes call and put prices
- Greeks: Delta, Gamma, Theta, Vega, Rho
- Sensitivity heatmaps across spot and volatility
- Profit and loss curves at expiration
- Implied volatility solver
- Optional live price and Treasury yield lookup with `yfinance`

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Reference Validation Case

For:

- `S = 100`
- `K = 100`
- `T = 1`
- `r = 0.05`
- `sigma = 0.20`

The theoretical prices should be approximately:

- Call: `10.4506`
- Put: `5.5735`
