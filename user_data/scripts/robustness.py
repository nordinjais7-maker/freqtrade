"""
Robustness checks for a backtest's trade list (used by sessionsweep_variants.py).

Ideas ported from HKUDS/Vibe-Trading (backtest/validation.py and
strategy_discovery/evidence_harness.py), rewritten for Freqtrade trade frames:

1. Sign-flip permutation test   - is the average trade really above zero, or could
                                  random +/- luck produce it? (p-value, one-sided)
2. Bootstrap confidence bands    - 95% range for expectancy (USDT per trade) and PF
                                  after resampling the trades with replacement.
3. Time-split stability          - trades split into equal calendar folds by close
                                  date; how many folds have PF > 1. (Walk-forward
                                  style consistency check; nothing is re-optimised.)
4. Regime split                  - each trade is tagged bull / bear / chop by the
                                  pair's trailing 30-day return at the previous daily
                                  close (causal, no look-ahead), then scored per regime.

All functions are pure (pandas / numpy only) except load_regimes(), which reads the
pair's cached 1h candles through Freqtrade's own data loader.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


N_PERM = 5000
N_BOOT = 2000
N_FOLDS = 5
REGIME_LOOKBACK_DAYS = 30
REGIME_THRESHOLD = 0.10  # +/-10% trailing return splits bull / chop / bear
SEED = 7


def profit_factor(p: np.ndarray) -> float:
    gains = p[p > 0].sum()
    losses = -p[p < 0].sum()
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return float(gains / losses)


def permutation_pvalue(p: np.ndarray, n_perm: int = N_PERM, seed: int = SEED) -> float:
    """One-sided sign-flip test of H0: mean trade P&L <= 0.

    Each trade's sign is flipped at random; the p-value is the share of shuffled
    means that are at least as large as the real one (with +1 smoothing).
    """
    p = np.asarray(p, dtype=float)
    if len(p) < 2:
        return float("nan")
    rng = np.random.default_rng(seed)
    real = p.mean()
    signs = rng.choice((-1.0, 1.0), size=(n_perm, len(p)))
    perm_means = (signs * np.abs(p)).mean(axis=1)
    return float((1 + np.sum(perm_means >= real)) / (n_perm + 1))


def bootstrap_ci(p: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """95% bootstrap bands for expectancy and profit factor."""
    p = np.asarray(p, dtype=float)
    if len(p) < 2:
        nan = float("nan")
        return {"exp_lo": nan, "exp_hi": nan, "pf_lo": nan, "pf_hi": nan}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(p), size=(n_boot, len(p)))
    samples = p[idx]
    means = samples.mean(axis=1)
    gains = np.where(samples > 0, samples, 0).sum(axis=1)
    losses = -np.where(samples < 0, samples, 0).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        pfs = np.where(losses > 0, gains / losses, np.inf)
    pfs = np.where(np.isfinite(pfs), pfs, 99.0)  # cap "no losses" draws for percentiles
    return {
        "exp_lo": float(np.percentile(means, 2.5)),
        "exp_hi": float(np.percentile(means, 97.5)),
        "pf_lo": float(np.percentile(pfs, 2.5)),
        "pf_hi": float(np.percentile(pfs, 97.5)),
    }


def time_split(trades: pd.DataFrame, n_folds: int = N_FOLDS) -> dict:
    """PF per equal-length calendar fold (by close date)."""
    if trades.empty:
        return {"wf_pos": 0, "wf_n": 0, "wf_pfs": []}
    close = pd.to_datetime(trades["close_date"], utc=True)
    edges = pd.date_range(close.min(), close.max(), periods=n_folds + 1)
    pfs = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        last = hi == edges[-1]
        mask = (close >= lo) & ((close <= hi) if last else (close < hi))
        fold = trades.loc[mask, "profit_abs"].to_numpy(dtype=float)
        if len(fold):
            pfs.append(profit_factor(fold))
    return {"wf_pos": sum(pf > 1 for pf in pfs), "wf_n": len(pfs), "wf_pfs": pfs}


def label_regimes(
    candles: pd.DataFrame,
    lookback_days: int = REGIME_LOOKBACK_DAYS,
    threshold: float = REGIME_THRESHOLD,
) -> pd.Series:
    """Daily regime labels, indexed by UTC date, using only data up to the prior close."""
    daily = (
        candles.set_index(pd.to_datetime(candles["date"], utc=True))["close"]
        .resample("1D")
        .last()
        .dropna()
    )
    trailing = daily / daily.shift(lookback_days) - 1
    # shift(1): a trade opened on day D only sees the return up to day D-1's close
    trailing = trailing.shift(1)
    labels = pd.Series("chop", index=trailing.index)
    labels[trailing >= threshold] = "bull"
    labels[trailing <= -threshold] = "bear"
    labels[trailing.isna()] = "warmup"
    labels.index = labels.index.normalize()
    return labels


def load_regimes(pair: str, datadir: Path = Path("user_data/data/binance")) -> pd.Series | None:
    """Regime labels from the pair's cached 1h futures candles (None if unavailable)."""
    try:
        from freqtrade.data.history import load_pair_history
        from freqtrade.enums import CandleType

        candles = load_pair_history(pair, "1h", datadir, candle_type=CandleType.FUTURES)
    except Exception:
        return None
    if candles is None or candles.empty:
        return None
    return label_regimes(candles)


def regime_split(trades: pd.DataFrame, regimes: pd.Series | None) -> dict:
    out = {}
    for reg in ("bull", "bear", "chop"):
        out[f"{reg}_n"] = 0
        out[f"{reg}_PF"] = float("nan")
    if regimes is None or trades.empty:
        return out
    days = pd.to_datetime(trades["open_date"], utc=True).dt.normalize()
    tags = days.map(regimes).fillna("warmup")
    for reg in ("bull", "bear", "chop"):
        p = trades.loc[tags.to_numpy() == reg, "profit_abs"].to_numpy(dtype=float)
        out[f"{reg}_n"] = len(p)
        out[f"{reg}_PF"] = profit_factor(p) if len(p) else float("nan")
    return out


def analyze(trades: pd.DataFrame, regimes: pd.Series | None = None) -> dict:
    """All robustness numbers for one backtest's trade list."""
    if trades is None or trades.empty:
        base = {"n": 0, "exp": 0.0, "p_perm": float("nan")}
        base.update(bootstrap_ci(np.array([])))
        base.update({"wf_pos": 0, "wf_n": 0})
        base.update(regime_split(pd.DataFrame(), None))
        return base
    p = trades["profit_abs"].to_numpy(dtype=float)
    row = {"n": len(p), "exp": float(p.mean()), "p_perm": permutation_pvalue(p)}
    row.update(bootstrap_ci(p))
    ts = time_split(trades)
    row.update({"wf_pos": ts["wf_pos"], "wf_n": ts["wf_n"]})
    row.update(regime_split(trades, regimes))
    return row


def _f(x: float, fmt: str) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "-".rjust(len(fmt.format(0)))
    if isinstance(x, float) and math.isinf(x):
        return "inf".rjust(len(fmt.format(0)))
    return fmt.format(x)


def print_robust_table(rows: dict[str, dict], n_tests: int) -> None:
    """One line per variant. n_tests drives the multiple-testing p threshold."""
    alpha = 0.05 / max(n_tests, 1)
    print(
        "variant".ljust(22)
        + "    n   exp$/tr  p_perm  exp95%lo  PF95%lo  PF95%hi  WF+  "
        + "bull_n bull_PF  bear_n bear_PF  chop_n chop_PF"
    )
    print("-" * 132)
    for name, r in rows.items():
        star = "*" if (not math.isnan(r["p_perm"]) and r["p_perm"] < alpha) else " "
        print(
            name.ljust(22)
            + f"{r['n']:>5d} "
            + _f(r["exp"], "{:>9.3f}")
            + " "
            + _f(r["p_perm"], "{:>6.3f}")
            + star
            + _f(r["exp_lo"], "{:>9.3f}")
            + _f(r["pf_lo"], "{:>9.2f}")
            + _f(r["pf_hi"], "{:>9.2f}")
            + f"  {r['wf_pos']}/{r['wf_n']}  "
            + f"{r['bull_n']:>6d} "
            + _f(r["bull_PF"], "{:>7.2f}")
            + f"  {r['bear_n']:>6d} "
            + _f(r["bear_PF"], "{:>7.2f}")
            + f"  {r['chop_n']:>6d} "
            + _f(r["chop_PF"], "{:>7.2f}")
        )
    print(
        f"\np_perm = chance random +/- luck gives this average trade (one-sided sign-flip test)."
        f"\n* = p_perm < {alpha:.4f} (0.05 split across {n_tests} tests: the bar for 'not luck')."
        "\nexp95%lo / PF95%lo..hi = bootstrap 95% band; a real edge keeps exp95%lo > 0 and PF95%lo > 1."
        f"\nWF+ = calendar folds (of {N_FOLDS}) with PF > 1. Regime = pair's trailing "
        f"{REGIME_LOOKBACK_DAYS}d return at the prior close (>= +{REGIME_THRESHOLD:.0%} bull, "
        f"<= -{REGIME_THRESHOLD:.0%} bear, else chop)."
    )


def verdict(cells: list[dict], n_tests: int) -> str:
    """Across every pair/year cell: PASS / WATCH / FAIL."""
    alpha = 0.05 / max(n_tests, 1)
    if not cells or any(c["n"] < 30 for c in cells):
        return "THIN"  # too few trades somewhere to judge
    pf_lo_ok = all(c["pf_lo"] > 1 for c in cells)
    sig = all((not math.isnan(c["p_perm"])) and c["p_perm"] < alpha for c in cells)
    folds_ok = all(c["wf_n"] and c["wf_pos"] / c["wf_n"] >= 0.6 for c in cells)
    exp_pos = all(c["exp"] > 0 for c in cells)
    if pf_lo_ok and sig and folds_ok:
        return "PASS"
    if exp_pos and folds_ok:
        return "WATCH"
    return "FAIL"
