# ASX Mode 2 / Mode 3 Upgrade Plan

This document is now a completed-only record of the ASX Mode 2 / Mode 3 improvement work in `share-investment-strategy-model`.

## Completed Work

- ASX calendar filtering is in place.
- T+2 settlement is in place.
- Tax-aware hurdle rate logic is in place.
- Batch transaction ledger output is in place.
- Backend-only consensus diagnostics are returned from the engine.
- Backend-only execution diagnostics are returned from the engine.
- Stop-loss and take-profit are evaluated before consensus voting.
- Buy readiness is fee-aware and blocks impossible entries earlier.
- Public wrappers were added for market data access in `ModelBuilder`.
- UI consensus counters were removed so the dashboard stays focused on outcomes.
- Error categorization remains available for failed Mode 3 tickers.
- The 90-day warm-up buffer already exists in `ModelBuilder.fetch_data()`.

## Notes

- No outstanding implementation items are tracked in this document.
- Treat the production bot patterns as inspiration only; no broader consensus redesign is required here.
