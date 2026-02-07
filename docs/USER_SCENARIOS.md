# User Activity Scenarios & Functional Planning

This document outlines the conceptual workflow for end-users interacting with the AI Trading Bot system. These scenarios serve as the blueprint for future UI/UX and logic implementation.

---

## 1. Dashboard & Profile Management
**Scenario**: Admin entry point and profile navigation.
- **Workflow**: 
    1. **Landing**: Upon login, the user is presented with a Dashboard listing all existing profiles (Active and Archived).
    2. **Shortcut Tabs**: High-level tabs provide quick access to "Add Transaction" and "Adjust Tax" across all profiles via a dropdown selector.
    3. **Creation**: A prominent "Create New Profile" CTA.
        - **Default Funding**: Initial Fund defaults to **3000** (market currency).
        - **Holding Periods**: Limited to fixed intervals: **"1 week"**, **"2 weeks"**, or **"1 month"**.
    4. **Navigation**: User selects a specific stock profile (e.g., `ABB.AX`) to view details, modify parameters, or manage specific ledgers.
- **Confirmation**: A modal/popup appears summarizing any changes to profile parameters; data is only persisted upon explicit confirmation.

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

## 4. Transaction Ledger & Resource Tracking
**Scenario**: Maintaining a permanent, auditable record of all trading activities.
- **Quick Entry (Global Shortcut)**: A tab on the main dashboard allows adding a transaction for any profile using a dropdown.
- **Profile-Specific View**: Inside each profile, a dedicated "Transactions" tab shows historical data and allows adding new records.
- **Data Integrity (Append-Only)**:
    - **No Edit/Delete**: Once a transaction is saved, it cannot be modified or removed.
    - **Adjustment Records**: Errors or corrections are handled by appending a new "Adjustment" record with mandatory notes/purpose to justify the change in share quantity or cash balance.
- **Action Context**:
    - **BUY Action**: User inputs *Share Price* and *Quantity* (Units Purchased).
    - **SELL Action**: User inputs *Share Price* and *Gross Cash* (Total assumes received).
- **Auto-Calculation**: System automatically calculates Transaction Fees and Tax-Assumed based on current profile settings.

## 5. Profile Lifecycle Management
**Scenario**: Managing the state and existence of trading strategies.
- **States**: 
    - **ACTIVE**: Bot performs daily analysis and sends notifications.
    - **ARCHIVED**: Logic is suspended.
- **Reactivation**: Moving from Archived to Active requires re-inputting the **Initial Fund**. Historical parameters and the complete transaction ledger are preserved.
- **Secure Deletion**: Requires high-friction confirmation (typing the profile name).

## 6. Market-Specific Tax Management (Cumulative Liability)
**Scenario**: Handling markets like ASX/TWN where tax is not withheld at the point of sale.
- **Quick Entry (Global Shortcut)**: A dashboard tab allows for quick tax liability adjustments using a profile dropdown.
- **Profile-Specific View**: A "Tax Activities" tab within the profile allows for granular tracking.
- **Cumulative Tax Payable**: Each profile maintains a running "Tax Payable" bucket.
- **Append-Only Ledger**: Just like transactions, tax records cannot be edited. Corrections require an adjustment entry with notes.
    - **Directions**: "Add" (Increase liability) or "Minus" (Decrease liability).
    - **Reasons**: "Calculation Adjustment" or "Tax Paid".
- **Net Remaining Concept**: System uses the Liability vs. Cash ratio to provide a true concept of "Remaining Spendable Capital."

---
*Note: This is a planning document. Implementation of these features is pending based on architectural review.*
