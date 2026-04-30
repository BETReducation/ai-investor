from __future__ import annotations
import math


def calculate_metrics(trades: list[dict], equity_curve: list[dict]) -> dict:
    """Summarise a completed backtest into performance metrics."""
    empty = {
        "total_return_pct": 0.0, "win_rate": 0.0, "num_trades": 0,
        "avg_trade_pct": 0.0, "best_trade_pct": 0.0, "worst_trade_pct": 0.0,
        "max_drawdown_pct": 0.0, "sharpe_ratio": 0.0, "profit_factor": 0.0,
        "avg_bars_held": 0,
    }
    if not trades:
        return empty

    returns = [t["return_pct"] for t in trades]
    winners = [r for r in returns if r > 0]
    losers  = [r for r in returns if r <= 0]

    # Total return from the equity curve endpoints
    start_eq = equity_curve[0]["equity"] if equity_curve else 1.0
    end_eq   = equity_curve[-1]["equity"] if equity_curve else 1.0
    total_return = (end_eq / start_eq - 1) * 100

    # Max drawdown (peak-to-trough on equity curve)
    peak   = equity_curve[0]["equity"] if equity_curve else 1.0
    max_dd = 0.0
    for pt in equity_curve:
        v = pt["equity"]
        if v > peak:
            peak = v
        dd = (peak - v) / peak * 100
        if dd > max_dd:
            max_dd = dd

    # Sharpe ratio (annualised, trade-level returns, no risk-free rate)
    sharpe = 0.0
    if len(returns) > 1:
        mean_r = sum(returns) / len(returns)
        var    = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
        std_r  = math.sqrt(var) if var > 0 else 0.0
        sharpe = mean_r / std_r * math.sqrt(252) if std_r > 0 else 0.0

    # Profit factor
    gross_profit = sum(winners) if winners else 0.0
    gross_loss   = abs(sum(losers)) if losers else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    return {
        "total_return_pct": round(total_return, 2),
        "win_rate":         round(len(winners) / len(trades) * 100, 1),
        "num_trades":       len(trades),
        "avg_trade_pct":    round(sum(returns) / len(returns), 2),
        "best_trade_pct":   round(max(returns), 2),
        "worst_trade_pct":  round(min(returns), 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe_ratio":     round(sharpe, 2),
        "profit_factor":    round(min(profit_factor, 99.0), 2),
    }
