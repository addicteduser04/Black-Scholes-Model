from __future__ import annotations

from math import isnan

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine import black_scholes_pricing, implied_volatility, option_price_grid, pnl_at_expiration

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - optional runtime dependency in some environments
    yf = None


st.set_page_config(page_title="Black-Scholes Dashboard", layout="wide")


def _safe_market_snapshot(ticker: str) -> tuple[float | None, float | None, str | None]:
    if yf is None:
        return None, None, "Install yfinance to enable live market data."

    try:
        ticker_data = yf.Ticker(ticker)
        history = ticker_data.history(period="5d")
        if history.empty:
            return None, None, f"No price data returned for {ticker}."
        spot = float(history["Close"].dropna().iloc[-1])

        treasury_data = yf.Ticker("^TNX").history(period="5d")
        risk_free_rate = None
        if not treasury_data.empty:
            risk_free_rate = float(treasury_data["Close"].dropna().iloc[-1]) / 100.0

        return spot, risk_free_rate, None
    except Exception as exc:  # pragma: no cover - network dependent
        return None, None, f"Market data lookup failed: {exc}"


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_metric(value: float) -> str:
    return f"{value:.4f}"


def _build_heatmap(data: pd.DataFrame, title: str, colorscale: str) -> go.Figure:
    fig = go.Figure(
        data=go.Heatmap(
            z=data.values,
            x=data.columns.tolist(),
            y=(data.index * 100).round(2).tolist(),
            colorscale=colorscale,
            colorbar={"title": "Option Price"},
            hovertemplate="Spot: %{x}<br>Volatility: %{y}%<br>Price: %{z:.4f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="Spot Price",
        yaxis_title="Volatility (%)",
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    return fig


def _build_pnl_chart(stock_prices: np.ndarray, call_pnl: np.ndarray, put_pnl: np.ndarray) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=stock_prices,
            y=call_pnl,
            mode="lines",
            name="Call P&L",
            line={"color": "#1f77b4", "width": 3},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stock_prices,
            y=put_pnl,
            mode="lines",
            name="Put P&L",
            line={"color": "#d62728", "width": 3},
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Profit & Loss At Expiration",
        xaxis_title="Underlying Price At Expiration",
        yaxis_title="Profit / Loss",
        hovermode="x unified",
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
    )
    return fig


st.title("Black-Scholes Option Pricing Dashboard")
st.caption("Interactive pricing, Greeks, volatility sensitivity, payoff analysis, and implied volatility.")

if "spot_input" not in st.session_state:
    st.session_state.spot_input = 100.0
if "rate_input" not in st.session_state:
    st.session_state.rate_input = 0.05

with st.sidebar:
    st.header("Model Inputs")
    ticker = st.text_input("Ticker For Live Price", value="AAPL").strip().upper()
    if st.button("Fetch Live Market Snapshot", width="stretch"):
        live_spot, live_rate, error_message = _safe_market_snapshot(ticker)
        if error_message:
            st.warning(error_message)
        else:
            st.session_state.spot_input = live_spot
            if live_rate is not None and not isnan(live_rate):
                st.session_state.rate_input = live_rate
            st.success(f"Updated spot from {ticker}" + (" and risk-free rate." if live_rate is not None else "."))

    spot = st.number_input("Spot Price (S0)", min_value=1.0, value=float(st.session_state.spot_input), step=1.0)
    strike = st.number_input("Strike Price (K)", min_value=1.0, value=100.0, step=1.0)
    maturity_days = st.slider("Time To Maturity (days)", min_value=1, max_value=365, value=180, step=1)
    rate_pct = st.slider("Risk-Free Rate (%)", min_value=0.0, max_value=15.0, value=float(st.session_state.rate_input * 100), step=0.1)
    volatility_pct = st.slider("Volatility (%)", min_value=1.0, max_value=150.0, value=20.0, step=0.5)
    purchase_price = st.number_input("Option Premium / Purchase Price", min_value=0.0, value=10.0, step=0.1)
    heatmap_points = st.slider("Heatmap Resolution", min_value=10, max_value=40, value=21, step=1)

maturity = maturity_days / 365.0
rate = rate_pct / 100.0
volatility = volatility_pct / 100.0

try:
    result = black_scholes_pricing(
        spot=spot,
        strike=strike,
        maturity=maturity,
        rate=rate,
        volatility=volatility,
    )
except ValueError as exc:
    st.error(str(exc))
    st.stop()

call_col, put_col, meta_col = st.columns(3)
call_col.metric("Call Price", f"{result.call.price:.4f}")
put_col.metric("Put Price", f"{result.put.price:.4f}")
meta_col.metric("Time To Maturity", f"{maturity:.3f} years")

overview_tab, heatmap_tab, pnl_tab, iv_tab = st.tabs(
    ["Overview", "Sensitivity Heatmaps", "P&L Curves", "Implied Volatility"]
)

with overview_tab:
    greeks_df = pd.DataFrame(
        {
            "Metric": ["Price", "Delta", "Gamma", "Theta", "Vega", "Rho"],
            "Call": [
                _format_metric(result.call.price),
                _format_metric(result.call.delta),
                _format_metric(result.call.gamma),
                _format_metric(result.call.theta),
                _format_metric(result.call.vega),
                _format_metric(result.call.rho),
            ],
            "Put": [
                _format_metric(result.put.price),
                _format_metric(result.put.delta),
                _format_metric(result.put.gamma),
                _format_metric(result.put.theta),
                _format_metric(result.put.vega),
                _format_metric(result.put.rho),
            ],
        }
    )

    left_col, right_col = st.columns([1.2, 1])
    left_col.subheader("Option Greeks")
    left_col.dataframe(greeks_df, width="stretch", hide_index=True)

    right_col.subheader("Model Snapshot")
    right_col.write(
        pd.DataFrame(
            {
                "Input": ["Spot", "Strike", "Maturity", "Rate", "Volatility", "d1", "d2"],
                "Value": [
                    f"{spot:.2f}",
                    f"{strike:.2f}",
                    f"{maturity:.4f} years",
                    _format_percent(rate),
                    _format_percent(volatility),
                    _format_metric(result.d1),
                    _format_metric(result.d2),
                ],
            }
        )
    )

with heatmap_tab:
    call_grid = option_price_grid(
        strike=strike,
        maturity=maturity,
        rate=rate,
        base_spot=spot,
        base_volatility=volatility,
        option_type="call",
        spot_points=heatmap_points,
        volatility_points=heatmap_points,
    )
    put_grid = option_price_grid(
        strike=strike,
        maturity=maturity,
        rate=rate,
        base_spot=spot,
        base_volatility=volatility,
        option_type="put",
        spot_points=heatmap_points,
        volatility_points=heatmap_points,
    )

    call_heatmap_col, put_heatmap_col = st.columns(2)
    call_heatmap_col.plotly_chart(
        _build_heatmap(call_grid, "Call Price Heatmap", "Blues"),
        width="stretch",
    )
    put_heatmap_col.plotly_chart(
        _build_heatmap(put_grid, "Put Price Heatmap", "Reds"),
        width="stretch",
    )

with pnl_tab:
    stock_range = np.linspace(spot * 0.5, spot * 1.5, 200)
    call_pnl = pnl_at_expiration(stock_range, strike=strike, premium=purchase_price, option_type="call")
    put_pnl = pnl_at_expiration(stock_range, strike=strike, premium=purchase_price, option_type="put")

    st.plotly_chart(
        _build_pnl_chart(stock_range, call_pnl, put_pnl),
        width="stretch",
    )

    break_even_call = strike + purchase_price
    break_even_put = strike - purchase_price
    breakeven_col1, breakeven_col2 = st.columns(2)
    breakeven_col1.metric("Call Break-Even", f"{break_even_call:.2f}")
    breakeven_col2.metric("Put Break-Even", f"{break_even_put:.2f}")

with iv_tab:
    st.subheader("Back Out Implied Volatility From A Market Price")
    iv_option_type = st.selectbox("Option Type", options=["call", "put"], index=0)
    market_option_price = st.number_input("Observed Market Option Price", min_value=0.01, value=max(result.call.price, 0.01), step=0.1)

    if st.button("Solve Implied Volatility", width="stretch"):
        try:
            iv_value = implied_volatility(
                option_price=market_option_price,
                spot=spot,
                strike=strike,
                maturity=maturity,
                rate=rate,
                option_type=iv_option_type,
            )
            st.success(f"Implied volatility: {iv_value * 100:.2f}%")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Could not solve implied volatility: {exc}")
