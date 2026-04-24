# Horizon-Aware Split BUY/EXIT Signal Architecture

## Overview

This document describes the multi-horizon model architecture for Taiwan stock AI trading system, where BUY and EXIT signals are generated from separate, horizon-specialized models.

## Architecture

### Core Concept

- **BUY Signal** (horizon = N days): Predicts long-term price movement; confirms entry decision
- **EXIT Signal** (horizon = 1 day): Predicts short-term price movement; confirms exit/hold decision
- **Bundle Storage**: Both models stored in single `.joblib` bundle under `bundle["horizons"]` namespace

### Why Separate Models?

1. **Temporal Specialization**: Different market dynamics at different timeframes
   - BUY (N days): Trend-based, fundamental-driven
   - EXIT (1 day): Momentum-based, tactical micro-movements

2. **Risk Reduction**: Exit decision uses short-term predictability, independent of N-day trend
   - If 5-day trend is bullish but tomorrow is bearish, EXIT model provides tactical exit signal
   - Prevents holding through short-term reversals that violate risk constraints

3. **Backwards Compatibility**: Legacy single-horizon bundles still supported
   - `_extract_horizon_entry()` helper handles both formats
   - Lazy retraining if horizon missing from bundle

## Model Bundle Structure

```python
bundle = {
    "horizons": {
        1: {                          # EXIT model (always present)
            "scaler": StandardScaler,
            "target_scaler": None,    # May be None
            "model_class": "RandomForest",
            "weighting_type": "volume",
            "target_horizon_days": 1,
            "keras_path": "path/to/h1.keras"  # Only for LSTM models
            # OR "model": RandomForestModel
        },
        5: {                          # BUY model (example: 5-day horizon)
            "scaler": StandardScaler,
            "target_scaler": None,
            "model_class": "RandomForest",
            "weighting_type": "volume",
            "target_horizon_days": 5,
            "model": RandomForestModel
        }
    },
    # Legacy compatibility (deprecated but supported):
    "scaler": ...,                    # Falls back here if horizons[] missing
    "model": ...,
    "target_scaler": ...,
    "target_horizon_days": ...
}
```

## Implementation

### Model Loading Workflow

1. **Load BUY Model** (horizon = N)
   ```python
   model_builder.load_or_build(ticker, target_horizon_days=5)
   ```
   - Loads `bundle["horizons"][5]` scaler and model
   - If horizon=5 missing from bundle, triggers retraining to populate it
   - After loading, `model_builder.model` and `model_builder.scaler` point to BUY model

2. **Load EXIT Model** (horizon = 1)
   ```python
   exit_builder = ModelBuilder(config)
   exit_builder.load_exit_model(ticker, buy_horizon_days=5)
   ```
   - Reads from same `h5d` bundle (created during training with both horizons)
   - Loads `bundle["horizons"][1]` instead
   - For 1-day strategies, delegates to `load_or_build(horizon=1)` (same model)

### Training Process

```python
# Trains both horizon=1 and horizon=5 in single pass
model_builder.train(ticker, target_horizon_days=5)
```

Creates bundle with both horizons populated:
- Loops: `for h in sorted({1, 5})`
- Each iteration:
  - Prepares features with target_horizon_days=h
  - Trains model on h-day returns
  - Stores under `bundle["horizons"][h]`
- Read-modify-write pattern preserves existing entries

### Backtesting Workflow

```python
# Model mode (single model)
engine.run_model_mode(ticker, "random_forest")
# Internally:
# - Loads BUY model (horizon=5)
# - Loads EXIT model (horizon=1)
# - Creates signal_buy() and signal_exit() callbacks
# - Passes exit_signal_func to _core_run()

# Strategy mode (committee)
engine.run_strategy_mode(ticker, ["random_forest", "lstm", "prophet"])
# Internally:
# - Loads BUY models for all three types
# - Loads EXIT models for all three types
# - Creates consensus_buy() and consensus_exit() callbacks
# - Passes exit_signal_func to _core_run()
```

## Signal Function Semantics

### BUY Signal
```python
def signal_buy(i, df, features, current_capital) -> bool:
    pred = get_prediction(buy_model, df, i)
    return pred_return > hurdle_rate
```
Returns: `True` = enter position, `False` = stay flat

### EXIT Signal
```python
def signal_exit(i, df, features, current_capital) -> bool:
    pred = get_prediction(exit_model, df, i)
    return pred_return > hurdle_rate
```
Returns: `True` = exit position, `False` = hold position

### Exit Logic in _core_run()
```python
if position > 0:  # In position
    if min_hold_passed:
        # Use exit_signal_func if provided, else fall back to buy signal
        _exit_fn = exit_signal_func if exit_signal_func else signal_func
        if not _exit_fn(i, df, features, ...):  # Exit confirmed
            sell(reason="model-exit")
```

## Market-Specific Calendars

Each market preserves its trading calendar during horizon-aware implementation:

### Taiwan (TWN)
- Calendar: `pandas_market_calendars.get_calendar("XTAI")`
- Features: KD indicator, FinMind institutional data, TWSE volume weighting
- Preserved in model_builder.py and backtest_engine.py

### USA
- Calendar: `pandas_market_calendars.get_calendar("NYSE")`
- Features: Standard technical indicators, CRSP/TAQ volume data
- Implemented in research branch

### ASX
- Calendar: `pandas_market_calendars.get_calendar("ASX")`
- Features: Australian-specific indicators, ASX volume data
- Original implementation template

## Backwards Compatibility

### Handling Legacy Bundles

When bundle doesn't have `horizons[]` namespace (old format):

```python
@staticmethod
def _extract_horizon_entry(bundle, target_h):
    # Try new multi-horizon format
    if "horizons" in bundle and target_h in bundle["horizons"]:
        return bundle["horizons"][target_h]
    
    # Fall back to legacy flat format
    if "scaler" in bundle and target_h == 1:
        return {
            "scaler": bundle["scaler"],
            "model": bundle.get("model"),
            "target_scaler": bundle.get("target_scaler"),
            "model_class": bundle.get("model_class", "Unknown"),
            "weighting_type": bundle.get("weighting_type", "equal"),
            "target_horizon_days": 1,
        }
    
    # Horizon not found → raise error → trigger retraining
    raise FileNotFoundError(f"Horizon {target_h} not in bundle")
```

### Migration Strategy

1. First load with new code auto-trains missing horizons
2. Bundle upgraded to multi-horizon format on next save
3. No manual migration needed; automatic via lazy retraining

## Testing Checklist

- [ ] BUY model loads from correct horizon entry
- [ ] EXIT model loads from h=1 entry
- [ ] 1-day strategy uses same model for both BUY and EXIT
- [ ] N-day strategy uses separate BUY/EXIT models
- [ ] Committee voting aggregates exit consensus correctly
- [ ] Exit_signal_func falls back to signal_func if None
- [ ] Legacy bundles still load without retraining
- [ ] Market calendar preserved in backtesting (Taiwan ±10% limits applied correctly)
- [ ] Taiwan STT and settlement logistics unaffected
- [ ] Model classes, weights, target scalers loaded correctly per horizon

## Files Modified

- `core/model_builder.py`: Added `_get_lstm_horizon_path()`, `_extract_horizon_entry()`, multi-horizon `train()`, updated `load_or_build()`, added `load_exit_model()`
- `core/backtest_engine.py`: Updated `_core_run()` with exit_signal_func parameter, split `run_model_mode()` and `run_strategy_mode()` into BUY/EXIT signal pairs, added builder parameter to `_get_bulk_predictions()`
