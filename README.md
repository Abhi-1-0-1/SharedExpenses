<!-- README for SharedExpenses -->

# SharedExpenses

SharedExpenses is a terminal-first expense tracker for small groups who want spreadsheet-level control with guardrails. It keeps everything in two human-readable files (`expenses.csv` and `people.txt`), normalizes the data, and presents clear menus to add expenses, view balances, and settle debts. The internal logic works entirely in lowercase (except the literal `GRP` token for whole-group expenses), while the UI prints names and items in title case for readability. This README walks through how it works, how to run it, and how to keep your data tidy.

## Why This Tool

- **Portable, zero lock-in** – Uses plain CSV/TXT that can be inspected or edited with any editor. No hidden database.
- **Predictable math** – Every load path revalidates and normalizes data before calculations, reducing “silent” mis-matches in names or missing headers.
- **CLI-friendly** – Banners, separators, and table output (via `tabulate`) make it easy to follow along in a terminal session.
- **Group semantics built-in** – The `GRP` token stands for “every person in people.txt”. When a loaded expense lists everyone individually, the loader condenses it back to `GRP`, keeping files compact.
- **Lowercase internally, clean display externally** – Lowercase storage prevents subtle duplicates (`Bob` vs `bob`); title-cased output keeps the interface friendly.

## Key Features

- Start new, continue, or load a prior session; all paths rewrite source files into the canonical `expenses.csv` and `people.txt`.
- Strict extension checks: only `.csv` for expenses and `.txt` for people files are accepted.
- Automatic normalization:
  - Adds a header to expenses if missing.
  - Lowercases every name and item (except `GRP` token), sorts and dedupes participants, and ensures comma-space formatting when shown.
  - Validates that every participant/payer exists in `people.txt`.
  - Converts full-participant rows into `GRP` to stay compact.
- Expense management:
  - Add expense with prompts for payer, amount, item, and participants (`GRP` option included).
  - View expenses in a grid with aligned columns.
  - View per-person balances and suggested greedy settlements.
- UI polish:
  - Section headers and single dividers keep screens readable.
  - Errors and confirmations are prefixed with clear markers (e.g., `> Added expense ...`).

## Repository Layout

```
project/
├── project.py          # Main application
├── README.md           # This document
├── requirements.txt    # Python deps (tabulate)
├── text.txt            # Design notes / option overview
├── sampleData/         # Example CSV/TXT payloads
└── workingFiles/       # Active copies of expenses.csv / people.txt when running locally
```

Only `project.py`, `expenses.csv`, and `people.txt` are required at runtime. Sample data is optional and safe to delete.

## Installation

1. **Python**: Requires Python 3.9+ (standard library only, plus tabulate).
2. **Dependencies**: From the `project` folder run:
   ```
   pip install -r requirements.txt
   ```
3. **Files**: Ensure `expenses.csv` and `people.txt` exist before selecting “Continue previous session”, or use “Start new session” to create them.

## Quick Start

1. `cd project`
2. `python project.py`
3. Choose an option from the **Start Menu**:
   - **1. Start new session** – Creates fresh `expenses.csv`/`people.txt` from your input.
   - **2. Continue previous session** – Uses existing canonical files if present.
   - **3. Load a session** – Copy and normalize external files into the canonical names.
4. In the **Function Menu**, pick:
   - **Add Expense** – Enter payer, amount, item, and participants (`0` for whole group).
   - **View Expenses** – Show a formatted table.
   - **View Balances** – Show who owes/gets what.
   - **Settle Debt** – Greedy pairing of debtors and creditors with title-cased names.
   - **Exit**

## Data Model

- **people.txt**: One name per line, lowercase internally. UI renders title case. No commas.
- **expenses.csv**: Columns `Item,Amount,Payer,Participants`.
  - `Item`: Lowercase internally; printed title case.
  - `Amount`: Decimal number.
  - `Payer`: Lowercase name that exists in `people.txt`.
  - `Participants`: Either `GRP` or a comma-separated list of lowercase names from `people.txt` (order does not matter; stored sorted and deduped).

## Normalization Pipeline (Load Session)

When you load external files, the app:

1. **Extension check** – Rejects non-`.csv` or `.txt`.
2. **Copy** – Writes the provided files to canonical names `expenses.csv` and `people.txt` in the working directory.
3. **Normalize people** – Lowercases and strips each line; removes empties and duplicates.
4. **Ensure header** – Adds `Item,Amount,Payer,Participants` if missing from the CSV.
5. **Normalize expenses** – For each row:
   - Lowercase item, payer, and participant names (except `GRP` literal).
   - Validate payer/participants exist in `people.txt`.
   - Sort and dedupe participant lists; convert “all members listed” to `GRP`.
6. **Persist** – Rewrites `expenses.csv` with clean rows and proper header.

All later operations (add, view, balances, settlement) rely on this normalized state, so calculations stay consistent.

## Adding an Expense

Flow (from Function Menu → Add Expense):

1. Pick payer by number (list comes from `people.txt`).
2. Enter amount (validated as positive float).
3. Enter item/description (internally lowercased).
4. Select participants:
   - Enter `0` for `GRP`, or
   - Enter comma-separated indices; blanks are rejected; duplicates are removed.
5. The new normalized row is appended to `expenses.csv`.
6. A confirmation line prints: `> Added expense: Item (amount) by Payer for Participants`.

### Common Input Guards

- Non-numeric amounts are rejected.
- Negative or zero amounts are rejected.
- Invalid payer index re-prompts.
- Participant choices outside range re-prompts.
- Empty participant selection re-prompts.

## Viewing Expenses

- Uses `tabulate` to present `Item`, `Amount`, `Payer`, and `Participants`.
- Participants print with a comma and a space (`Alice, Bob`) for readability.
- If no expenses exist, the UI prints a friendly notice instead of an empty table.

## Balances and Settlement

### Balance Calculation

For each expense:

- Split cost evenly among participants (or whole group via `GRP`).
- Each participant owes their share.
- Payer is credited the full amount.

Net balance per person = credits received – shares owed.

### Viewing Balances

- Shows a two-column table: `Person | Balance`.
- Positive means the person should receive money; negative means they owe.
- Names are title-cased in the UI only; internal math remains lowercase.

### Settling Debt

- Implements a simple greedy strategy:
  1. Separate creditors (positive balances) and debtors (negative balances).
  2. Sort by magnitude.
  3. Pair the largest debtor with the largest creditor until one is settled; continue.
- Output lines read like: `Bob pays Alice 7.50`.
- Results use title-cased names for clarity.

## File Format Details

`expenses.csv` example (on disk):
```
Item,Amount,Payer,Participants
pizza,10,alice,grp
burger,15,bob,alice,bob
```

`people.txt` example (on disk):
```
alice
bob
charlie
```

Displayed in UI (title case):
```
| Item   | Amount | Payer | Participants |
| Pizza  | 10.00  | Alice | GRP          |
| Burger | 15.00  | Bob   | Alice, Bob   |
```

## UI Conventions

- Banners mark major sections: “Start Menu”, “Load Session From Files”, “Function Menu”, etc.
- Single horizontal dividers separate operations to prevent the “double divider” effect.
- Status lines start with `>` so they stand out from prompts.
- Errors are explained briefly before re-prompting.

## Error Handling and Validation

- **Extension errors**: Refuses files without `.csv`/`.txt`.
- **Missing header**: Automatically inserted into `expenses.csv`.
- **Name mismatches**: Fails fast if payer/participant not present in `people.txt`.
- **Corrupt rows**: Skips or prompts when a line has wrong column count.
- **Empty files**: Creates header-only expenses file; people file must contain at least one name to proceed.
- **Normalization**: Lowercases names/items and trims whitespace; `GRP` is preserved uppercase.

## Workflow Examples

### Start New Session

1. Choose “Start new session”.
2. Enter people names (any casing; stored lowercase).
3. `people.txt` and `expenses.csv` are created in canonical form.
4. Use Function Menu to add expenses and view balances.

### Load Existing Files

1. Choose “Load a session”.
2. Provide paths to an external expenses CSV and people TXT.
3. App copies them into `expenses.csv` / `people.txt`, normalizes, ensures header, and condenses `GRP` rows.
4. Continue using the Function Menu with the cleaned data.

### Continue Previous Session

1. Choose “Continue previous session”.
2. If canonical files exist, they are used as-is (they are already normalized from prior runs).
3. Proceed to Function Menu.

## Internal Design Notes

- **Lowercase-first logic**: All comparisons, lookups, and balance math happen on normalized lowercase strings to avoid subtle duplication.
- **Stateless menus**: Each action reads from disk, does its work, and writes back if needed; no hidden global caches beyond the canonical file names.
- **Helpers**:
  - `normalize_people_file` and `normalize_expenses_file` handle rewriting data.
  - `ensure_expenses_header` inserts the header row if missing.
  - `condense_grp_entries` replaces “all participants explicitly listed” with `GRP`.
  - `match_people` checks expenses against the known people list.

## Running Tests

The repository includes a placeholder `test_project.py`. To add tests:

1. Install `pytest` (`pip install pytest`).
2. Write tests that create temporary CSV/TXT fixtures and call the helper functions (e.g., normalization, balance computation).
3. Run `pytest`.

Because the app is CLI-oriented, focus tests on pure functions (`compute_balances`, normalization helpers) rather than interactive flows.

## Troubleshooting

- **Tabulate not recognized**: Ensure the virtual environment matches the interpreter used to run `project.py`. Run `pip show tabulate` to confirm installation. If multiple Pythons exist, install with `python -m pip install tabulate`.
- **Double dividers**: The current UI prints single dividers between sections. If you see doubles, you may have stray prints; restart to confirm.
- **Header missing after load**: The loader automatically adds the header. If you manually edit `expenses.csv` and remove it, restart and choose “Load session” again so the header is reinserted.
- **Name mismatch errors**: Open `people.txt` and confirm all payer/participant names exist (remember, stored lowercase).
- **Amounts rounding**: Amounts are stored as float; displayed with two decimals via `tabulate`. For exact cents, enter values with two decimals.

## Roadmap Ideas

- Configurable currency symbol in output.
- Optional percentage-based splits or unequal shares.
- Export settlements as a separate CSV.
- Unit test suite covering all helpers and menu flows.
- Colorized terminal output when available.

## Frequently Asked Questions

- **Why lowercase everything internally?** To avoid subtle duplicates (`Bob`, `bob`, `BOB`) and keep comparisons predictable. Display uses title case so the UI stays readable.
- **Do I need to type `GRP`?** No. When adding an expense, enter `0` to apply the expense to the whole group. When loading data, any row that lists every person is converted to `GRP`.
- **Can I edit the CSV manually?** Yes, but keep the header and lowercase names. If you add rows manually, re-run “Load session” to normalize spacing and participants.
- **How are debts settled?** A greedy algorithm pairs largest debtor with largest creditor until balances are zeroed. It is simple and effective for small groups.
- **What happens if I load files with wrong extensions?** The loader rejects them before copying; provide `.csv` for expenses and `.txt` for people.

## Contributing

This is a learning-oriented CLI app. If you want to extend it:

1. Fork or branch.
2. Add focused tests for new helpers.
3. Keep UI output concise and legible.
4. Preserve lowercase-internal/title-case-display convention.

## License

SharedExpenses is released under the MIT License (see `LICENSE`).

## At a Glance (Cheat Sheet)

- Run: `python project.py`
- New session: option 1
- Load session: option 3 (accepts only .csv/.txt)
- Files in use: `expenses.csv`, `people.txt`
- `GRP` means everyone in `people.txt`
- Storage: lowercase; Display: title case
- Tables: powered by `tabulate`

Enjoy tracking and settling group costs with SharedExpenses!
