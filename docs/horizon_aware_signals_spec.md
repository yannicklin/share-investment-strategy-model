# Horizon-Aware Signal Design: ASX Model

**Context**: The `trading-platform-bot` (`main` branch) received a "horizon-aware buy signals" upgrade (April 2026) that trains separate submodels for SELL (horizon=1) and BUY (horizon=holding_period), stores both inside one `.joblib` bundle, and routes daily signal generation accordingly. This document captures the assessment and final design decision for applying the equivalent pattern to `share-investment-strategy-model` (ASX research branch).

---

## 1. Architectural Comparison

| Dimension | `trading-platform-bot` | `share-investment-strategy-model` |
|---|---|---|
| **Purpose** | Live daily signal generation | Backtesting & research lab |
| **Model storage** | One bundle, multiple horizons inside (`bundle["horizons"][N]`) | One file per BUY horizon (`h{N}d` suffix) — **bundle extended to include horizon=1 entry** |
| **Sell decision** | Model vote at horizon=1 | **Model vote at horizon=1** (planned — same as bot) |
| **Buy decision** | Model vote at horizon=holding_period | Model vote at horizon=holding_period (unchanged) |
| **`load_or_build`** | Production-only; fails fast | Self-contained; auto-trains from scratch if file missing |
| **Multi-horizon compare** | Not needed (one mandate per runtime) | Core feature of Mode 2 — each file is one BUY strategy |

---

## 2. What Does NOT Change

### 2.1 Horizon-Suffix Filename Convention

The filename format **stays unchanged**:

```
{ticker}_{model_type}_{weighting}_h{N}d_model.joblib
```

The `h{N}d` suffix identifies the **BUY horizon** being evaluated. Mode 2 (Time-Span Comparison) trains and loads multiple files during a single run — one per holding period — so isolating them by filename remains correct and intentional.

What changes is the **contents** of each bundle: every `h{N}d` file now stores two horizon entries internally, just like the bot:

```python
bundle = {
    "horizons": {
        1: {"model": ..., "scaler": ..., "target_horizon_days": 1, ...},   # SELL / exit confirmation
        N: {"model": ..., "scaler": ..., "target_horizon_days": N, ...},   # BUY entry
    }
}
```

**Special case — `h1d`**: When `holding_period=1`, the set `{1, max(1,1)}` = `{1}`. The bundle stores only one entry; that entry serves both roles. No redundancy.

### 2.2 Production / Training / Previous Folder Structure

The bot requires a staged pipeline (`/training/ → /previous/ → /production/`) because it promotes models on a schedule. The ASX model is a self-contained research tool with no deployment lifecycle.

**Decision: No folder promotion pipeline needed.**

---

## 3. The Gap: Wrong Model Used for Exit Decisions

### 3.1 Current Behaviour (All Three Modes)

Both `run_model_mode` (Mode 1) and `run_strategy_mode` (Mode 2/3) share the same core loop via `_core_run`. The `signal_func` callback is called once per trading day and returns a single boolean (`is_bullish`). That **same boolean** drives two independent decisions:

1. **BUY entry** — `position == 0 and is_bullish` → open a position
2. **Model-exit after min_hold** — `not is_bullish` → close the position

```python
# Mode 1 signal — loaded with target_horizon_days=holding_period
def signal(i, df_inner, _features_inner, current_cap):
    pred_return = (all_preds[i] - current_price) / current_price
    return pred_return > hurdle  # horizon-N model

# _core_run uses the same result for both:
if position == 0 and is_bullish:        # BUY: asks "will it be higher in N days?" ✅
    ...
elif not is_bullish and min_hold_passed: # EXIT: asks "will it be higher in N days?" ❌
    reason = "model-exit"               #       should ask "will it close lower today?"
```

The exit question is wrong. A holding-period model predicts end-of-hold returns, not whether today is a good day to exit. This is the same design flaw that the bot corrected.

### 3.2 Scope: Affects Mode 1, Mode 2, and Mode 3

- **Mode 1** (`run_model_mode`): single `all_preds` array built from horizon-N model; `signal()` uses it for both BUY and exit
- **Mode 2 / Mode 3** (`run_strategy_mode`): `committee_preds[m_type]` built from horizon-N per model; consensus `signal()` uses it for both BUY and exit

The fix is identical for all modes because they all go through `_core_run` with the same `signal_func` contract.

---

## 4. Planned Design: Split BUY and EXIT Signals

### 4.1 Bundle Change

Every `h{N}d_model.joblib` is trained for **two horizons**:
- `horizons[1]` — same-session close prediction; used exclusively for exit confirmation
- `horizons[N]` — holding-period return prediction; used exclusively for BUY entry

Training iterates `required_horizons = sorted({1, max(1, int(holding_period_days))})`, same pattern as the bot.

### 4.2 Backtest Engine Change

`_core_run` receives **two** prediction sets instead of one:
- `buy_preds` — from horizon-N model; evaluated against hurdle for BUY entry
- `exit_preds` — from horizon-1 model; used to determine if model-exit should fire after min_hold

The `signal_func` contract splits into two callbacks or one that returns a named pair — exact API is an implementation detail for the plan.

Exit logic after the change:
- Hard exits (stop-loss, pre-hold take-profit) remain **rule-based and unchanged** — no model gating
- `model-exit` (after `min_hold_passed`, no take-profit) → fires when `exit_pred` predicts a negative same-session close change

### 4.3 Ledger Note

The `notes` field on SELL entries already records the exit reason. No new ledger fields required — `"model-exit"` continues to identify exits driven by the model path.

### 4.4 Mode-Specific Bulk Predictions

| Mode | BUY predictions | EXIT predictions |
|---|---|---|
| Mode 1 | `_get_bulk_predictions(horizon=N, model_type)` | `_get_bulk_predictions(horizon=1, model_type)` |
| Mode 2/3 | `committee_preds[m_type]` at horizon=N | `exit_committee_preds[m_type]` at horizon=1 — consensus vote same as BUY |

---

## 5. Summary Decision

| Change | Decision | Rationale |
|---|---|---|
| Adopt single-bundle multi-horizon file format | ✅ Yes — with `h{N}d` filename preserved | Bundle stores horizon=1 + horizon=N; filename identifies BUY strategy |
| Adopt production/training/previous folder pipeline | ❌ No | ASX model is a local research tool; no deployment lifecycle |
| Add split buy/exit horizon — Mode 1 | ✅ Yes | BUY uses horizon-N model; model-exit uses horizon-1 model |
| Add split buy/exit horizon — Mode 2 & 3 | ✅ Yes | Same `_core_run` path; identical fix applies |
| Hard exits (stop-loss, early take-profit) remain rule-based | ✅ Yes | Deterministic rules must not be gated by a model for research reproducibility |
| Keep `target_horizon_days` naming | ✅ Yes | Consistent with existing ASX codebase; no rename needed |
| Keep `load_or_build()` auto-train fallback | ✅ Yes | Appropriate for a self-contained research tool |

---

## 6. Out of Scope

- No promotion scoring or threshold configuration (no `SystemSettings` equivalent)
- No `prediction_horizon` / `buy_horizon` / `sell_horizon` fields on a request contract — the backtest engine resolves horizons internally from `Config`
- No UI changes required — all split-horizon logic is inside the engine and model builder

---

*Last Updated: April 2026*
*Reference: `trading-platform-bot` spec — `specs/6-horizon-aware-buy-signals/spec.md`*
