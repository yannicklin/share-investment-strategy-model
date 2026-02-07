# User Activity Scenarios & Functional Planning

This document outlines the conceptual workflow for end-users interacting with the AI Trading Bot system. These scenarios serve as the blueprint for future UI/UX and logic implementation.

---

## 1. Dashboard & Profile Management
**Scenario**: Admin entry point and profile navigation.
- **Workflow**: 
    1. **Landing**: Upon login, the user is presented with a Dashboard listing all existing profiles (Active and Archived).
    2. **Creation**: A prominent "Create New Profile" Call-to-Action (CTA) allows for immediate expansion of the trading portfolio.
    3. **Navigation**: User selects a specific stock profile (e.g., `ABB.AX`) to view details or fine-tune parameters.
- **Parameter Adjustment**: Modifies stop-loss/profit-take thresholds, holding periods, hurdle rates, or trading fee assumptions.
- **Tax Awareness**: Updates personal income tax levels to ensure hurdle rate calculations remain accurate.
- **Confirmation**: A modal/popup appears summarizing changes; data is only persisted upon explicit confirmation.

## 2. Multi-Channel & Multi-Recipient Notifications
**Scenario**: Signals must reach multiple stakeholders or devices simultaneously.
- **Capability**: A single profile can be configured to broadcast Buy/Sell signals to:
    - Multiple mobile numbers (SMS).
    - Multiple Telegram/LINE IDs.
- **Channel Selection**: Users can toggle channels on/off (e.g., "SMS + Telegram" or "LINE only") per profile.

## 3. Single-Stock Profile Architecture
**Scenario**: Granular control over individual stock strategies.
- **Constraint**: Each Profile is strictly mapped to **ONE** stock ticker.
- **Validation**: Before saving any profile change, the system performs a mandatory `validate_ticker()` check.
- **Initial Funding**: New profiles require an **Initial Fund** amount input in the local market currency.

## 4. Transaction Ledger & Resource Tracking
**Scenario**: Keeping the bot synced with real-world brokerage actions via a "Shortcut Tab".
- **Quick Entry Workflow**:
    1. **Target Selection**: Single dropdown to select the target profile.
    2. **Auto-Populate**: System defaults to current date/time.
    3. **Action Context**:
        - **BUY Action**: User inputs *Share Price* and *Quantity* (Units Purchased).
        - **SELL Action**: User inputs *Share Price* and *Gross Cash* (Total assumes received).
    4. **Auto-Calculation**: System automatically calculates:
        - Transaction Fees (based on profile settings).
        - Tax-Assumed (based on tax model).
- **Resource Sync**: Updates Cash Balance and Share Inventory for next-day signal generation.

## 5. Profile Lifecycle Management
**Scenario**: Managing the state and existence of trading strategies.
- **States**: 
    - **ACTIVE**: Bot performs daily analysis and sends notifications.
    - **ARCHIVED**: Logic is suspended.
- **Reactivation**: Moving from Archived to Active requires re-inputting the **Initial Fund**. History and parameters are preserved.
- **Secure Deletion**: Requires high-friction confirmation (typing the profile name).

## 6. Market-Specific Tax Management (Cumulative Liability)
**Scenario**: Handling markets like ASX/TWN where tax is not withheld at the point of sale.
- **Tax Models**:
    - **Withholding (USA)**: Tax is deducted immediately from gross sale proceeds.
    - **Cumulative (ASX/TWN)**: Tax is calculated as a liability but the cash remains in the account.
- **Cumulative Tax Payable**: Each profile maintains a running "Tax Payable" bucket.
- **Tax Adjustment Ledger**: A dedicated log to track tax-specific movements:
    - **Directions**: "Add" (Increase liability) or "Minus" (Decrease liability).
    - **Reasons**: "Calculation Adjustment" (correcting errors) or "Tax Paid" (clearing liability).
- **Net Remaining Concept**: System uses the Liability vs. Cash ratio to provide a true concept of "Remaining Spendable Capital."

---
*Note: This is a planning document. Implementation of these features is pending based on architectural review.*
