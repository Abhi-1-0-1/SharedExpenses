# SharedExpenses

## CS50 Python Final Project

**SharedExpenses** is a terminal-first expense tracker for small groups. It keeps everything in two human-readable files (`expenses.csv` and `people.txt`), normalizes the data, and walks users through adding expenses, viewing balances, and settling debts with clear tabular output.

---

## Table of Contents

1. [Overview](#overview)
2. [Usage](#usage)
3. [How It Works & Technical Architecture](#how-it-works--technical-architecture)
4. [Project Structure](#project-structure)
5. [Data & Validation Rules](#data--validation-rules)
6. [Key Features](#key-features)
7. [Technologies Used](#technologies-used)
8. [Future of the Project](#future-of-the-project)
9. [License](#license)
10. [Acknowledgements](#acknowledgements)
11. [Author](#author)

---

## Overview

SharedExpenses solves the classic “who owes whom?” problem after group outings. The app favors portability (plain CSV/TXT), consistency (all data normalized to lowercase internally), and clarity (title-cased output with banners and dividers). Every session uses the canonical filenames `expenses.csv` and `people.txt`, so calculations always reference the same sources.

---

## Usage
See the app in use [here](https://youtu.be/tyNXCdRL2AE). The Flask web application contains two main interfaces for encryption and decryption operations.

Run the program from the `project` directory:

```
python project.py
```

You start at the **Start Menu** with three paths:

1. **Start new session** – Enter names; the app creates normalized `people.txt` and `expenses.csv`.
2. **Continue previous session** – Reuses existing canonical files.
3. **Load a session** – Copy external `.csv`/`.txt` into the canonical names, then normalize and validate.

Once in the **Function Menu**:

- **Add Expense**: pick payer, enter amount and item, choose participants (`0` for `GRP` = whole group). The row is appended in normalized form.
- **View Expenses**: shows a tabulated grid of item, amount, payer, and participants with comma+space formatting.
- **View Balances**: computes net balances (positive means to receive, negative means to pay) and displays them.
- **Settle Debt**: prints greedy settlement instructions (e.g., “Bob pays Alice 7.50”) using title-cased names.
- **Exit**: quit the app.

---

## How It Works & Technical Architecture

This is a single-file Python CLI built around deterministic file normalization and lightweight business logic.

### Normalization Pipeline

When loading or starting sessions:
- Enforce extensions: only `.csv` for expenses and `.txt` for people.
- Copy provided files to canonical names `expenses.csv` and `people.txt`.
- `normalize_people_file`: lowercase/trim each name, remove empties.
- `ensure_expenses_header`: insert `Item,Amount,Payer,Participants` if missing.
- `normalize_expenses_file`: lowercase item/payer/participants (except literal `GRP`), trim, dedupe/sort participant lists, rewrite file with header.
- `condense_grp_entries`: if a row lists everyone in `people.txt`, replace the participant list with `GRP`.
- `match_people`: fail fast if any payer/participant is not in `people.txt`.

### Core Logic

- **Expense storage**: `Expense` dataclass holds `item`, `amount`, `payer`, `participants`.
- **Balances**: `compute_balances` credits the payer and debits participants equally (or whole group via `GRP`).
- **Settlement**: greedy pairing of biggest debtor with biggest creditor until balances zero out.

### UI Layer

- Banners and single dividers for each screen.
- Status messages prefixed with `>`.
- Title-cased names/items on output; lowercase used internally to avoid duplicates (`Bob` vs `bob`).

---

## Project Structure

```
project/
├── project.py              # Main CLI application
├── README.md               # General project README
├── requirements.txt        # Python dependencies (tabulate)
├── pseudo.txt                # Option/menu design notes
├── sampleData/             # Fixture CSV/TXT files for testing
└── workingFiles/           # Active copies when running locally
```

---

## Data & Validation Rules

- **people.txt**
  - One name per line, stored lowercase.
  - Must contain at least two names to proceed.
- **expenses.csv**
  - Header: `Item,Amount,Payer,Participants` (auto-added if missing).
  - `Item`: lowercase internally; printed title case.
  - `Amount`: numeric > 0.
  - `Payer`: must exist in `people.txt`.
  - `Participants`: `GRP` or comma-separated lowercase names from `people.txt`; stored sorted/deduped.
- **Normalization Invariants**
  - No unknown names allowed.
  - Full participant lists are condensed to `GRP`.
  - Internal comparisons are case-insensitive via lowercase; display is title case.

---

## Key Features

- **Single source of truth**: always uses `expenses.csv` and `people.txt`.
- **Robust loading**: validates extensions, adds headers, and normalizes casing/spaces.
- **Clear tables**: `tabulate` grids for expenses and balances; comma+space in participant lists.
- **Greedy settlement**: concise pay/receive instructions.
- **Friendly CLI**: section headers, clean dividers, and explicit status/error lines.

---

## Technologies Used

- **Language**: Python 3
- **CLI Formatting**: `tabulate`
- **Standard Library**: `csv`, `os`, `shutil`, `pathlib`
- **Testing**: `pytest` (see `test_project.py` and `sampleData` fixtures)

---

## Future of the Project

- Currency symbol/locale customization.
- Unequal splits or percentage-based shares.
- Export settlements to CSV.
- Colorized terminal output when ANSI is available.
- Expanded automated tests for interactive flows.

---

## License

This project has been created exclusively for **educational purposes** as part of **CS50 Python 2026's Final Project**. Feel free to use and modify the application for learning and non-commercial purposes.

---

## Acknowledgements

- **Harvard & CS50 Staff** for the course material and inspiration.
- **Python & tabulate communities** for solid tooling.
- **Testers and friends** whose group outings inspired real-world scenarios.

---

## Author

**Abhinav Parasher**

**Github Username**: Abhi-1-0-1

**EdX Username**: --Abhinav--

**City And Country**: Muscat, Oman

_CS50 Python Final Project - 2026_

---