from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp, log, sqrt

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm


@dataclass(frozen=True)
class OptionMetrics:
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class PricingResult:
    d1: float
    d2: float
    call: OptionMetrics
    put: OptionMetrics

    def to_dict(self) -> dict[str, dict[str, float] | float]:
        return {
            "d1": self.d1,
            "d2": self.d2,
            "call": self.call.to_dict(),
            "put": self.put.to_dict(),
        }


def _validate_inputs(spot: float, strike: float, maturity: float, rate: float, volatility: float) -> None:
    if spot <= 0:
        raise ValueError("Spot price must be positive.")
    if strike <= 0:
        raise ValueError("Strike price must be positive.")
    if maturity < 0:
        raise ValueError("Time to maturity cannot be negative.")
    if volatility <= 0:
        raise ValueError("Volatility must be positive.")
    if not np.isfinite(rate):
        raise ValueError("Risk-free rate must be finite.")


def _intrinsic_result(spot: float, strike: float) -> PricingResult:
    call_price = max(spot - strike, 0.0)
    put_price = max(strike - spot, 0.0)
    call_delta = 1.0 if spot > strike else 0.0 if spot < strike else 0.5
    put_delta = call_delta - 1.0

    call = OptionMetrics(price=call_price, delta=call_delta, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)
    put = OptionMetrics(price=put_price, delta=put_delta, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)
    return PricingResult(d1=float("inf"), d2=float("inf"), call=call, put=put)


def black_scholes_pricing(
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    volatility: float,
) -> PricingResult:
    _validate_inputs(spot, strike, maturity, rate, volatility)

    if maturity == 0:
        return _intrinsic_result(spot, strike)

    sqrt_t = sqrt(maturity)
    sigma_sqrt_t = volatility * sqrt_t
    d1 = (log(spot / strike) + (rate + 0.5 * volatility**2) * maturity) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t

    discount = exp(-rate * maturity)
    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_d2 = norm.cdf(d2)

    call_price = spot * cdf_d1 - strike * discount * cdf_d2
    put_price = strike * discount * norm.cdf(-d2) - spot * norm.cdf(-d1)

    gamma = pdf_d1 / (spot * sigma_sqrt_t)
    vega = spot * pdf_d1 * sqrt_t

    call = OptionMetrics(
        price=call_price,
        delta=cdf_d1,
        gamma=gamma,
        theta=(-(spot * pdf_d1 * volatility) / (2 * sqrt_t) - rate * strike * discount * cdf_d2),
        vega=vega,
        rho=strike * maturity * discount * cdf_d2,
    )
    put = OptionMetrics(
        price=put_price,
        delta=cdf_d1 - 1,
        gamma=gamma,
        theta=(-(spot * pdf_d1 * volatility) / (2 * sqrt_t) + rate * strike * discount * norm.cdf(-d2)),
        vega=vega,
        rho=-strike * maturity * discount * norm.cdf(-d2),
    )

    return PricingResult(d1=d1, d2=d2, call=call, put=put)


def implied_volatility(
    option_price: float,
    spot: float,
    strike: float,
    maturity: float,
    rate: float,
    option_type: str = "call",
    lower_bound: float = 1e-6,
    upper_bound: float = 5.0,
) -> float:
    if option_price <= 0:
        raise ValueError("Option market price must be positive.")
    if maturity <= 0:
        raise ValueError("Time to maturity must be positive for implied volatility.")

    option_key = option_type.lower()
    if option_key not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")

    def objective(volatility: float) -> float:
        result = black_scholes_pricing(spot, strike, maturity, rate, volatility)
        model_price = result.call.price if option_key == "call" else result.put.price
        return model_price - option_price

    return brentq(objective, lower_bound, upper_bound)


def option_price_grid(
    strike: float,
    maturity: float,
    rate: float,
    base_spot: float,
    base_volatility: float,
    option_type: str = "call",
    spot_points: int = 21,
    volatility_points: int = 21,
    spot_min_factor: float = 0.8,
    spot_max_factor: float = 1.2,
    vol_min_factor: float = 0.5,
    vol_max_factor: float = 1.5,
) -> pd.DataFrame:
    if spot_points < 2 or volatility_points < 2:
        raise ValueError("Heatmap requires at least two points on each axis.")

    option_key = option_type.lower()
    if option_key not in {"call", "put"}:
        raise ValueError("option_type must be 'call' or 'put'.")

    spot_values = np.linspace(base_spot * spot_min_factor, base_spot * spot_max_factor, spot_points)
    vol_floor = max(base_volatility * vol_min_factor, 0.01)
    vol_values = np.linspace(vol_floor, base_volatility * vol_max_factor, volatility_points)

    data = []
    for volatility in vol_values:
        row = []
        for spot in spot_values:
            result = black_scholes_pricing(spot, strike, maturity, rate, float(volatility))
            row.append(result.call.price if option_key == "call" else result.put.price)
        data.append(row)

    return pd.DataFrame(
        data=np.array(data),
        index=np.round(vol_values, 4),
        columns=np.round(spot_values, 2),
    )


def pnl_at_expiration(stock_prices: np.ndarray, strike: float, premium: float, option_type: str = "call") -> np.ndarray:
    option_key = option_type.lower()
    if option_key == "call":
        payoff = np.maximum(stock_prices - strike, 0.0)
    elif option_key == "put":
        payoff = np.maximum(strike - stock_prices, 0.0)
    else:
        raise ValueError("option_type must be 'call' or 'put'.")
    return payoff - premium
