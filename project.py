import os
import csv
import shutil
import sys

from tabulate import tabulate

# Default file names and shared CSV header
DEFAULT_EXPENSES_FILE = "workingFiles/expenses.csv"
DEFAULT_PEOPLE_FILE = "workingFiles/people.txt"
CSV_HEADERS = ["Item", "Amount", "Payer", "Participants"]
SEPARATOR_WIDTH = 60
NEGATIVE_CONFIRMED_ONCE = False

# ---------- Beautifiers ----------
# Small helpers for the terminal UI
def print_divider(char: str = "-", width: int = SEPARATOR_WIDTH) -> None:
    """Draw a horizontal separator for the terminal UI."""
    print(char * width)


def print_section_header(title: str) -> None:
    """Show a centered banner for the current section."""
    print()
    print_divider("=")
    print(title.center(SEPARATOR_WIDTH))
    print_divider("=")


def print_status(message: str) -> None:
    """Echo a short status line under the current banner."""
    print(f"> {message}")


class Expense:
    """Representation of a single expense."""

    def __init__(self, item: str, amount: float, payer: str, participants: list[str]):
        self.item = item
        self.amount = amount
        self.payer = payer
        self.participants = participants


# ---------- UI helpers ----------
# Small helpers for menu prompts and y/n questions. Keep I/O in one place.
def print_choices(header: str, choices: list[str]) -> None:
    print(f"{header}:")
    for i, choice in enumerate(choices, start=1):
        print(f"{i}. {choice}")


def ask_choice(header: str, choices: list[str]) -> int:
    """Show numbered options and return a valid choice index (1-based)."""
    print_choices(header, choices)
    while True:
        try:
            choice = int(input("Enter your choice: "))
            if 1 <= choice <= len(choices):
                return choice
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def ask_yes_no(prompt: str) -> bool:
    """Return True/False from a y/n style prompt."""
    while True:
        answer = input(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer with y/n.")


def prompt_existing_file(label: str) -> str | None:
    """Prompt until the user provides an existing filename."""
    while True:
        filename = input(f"Enter the {label} filename: ").strip()
        if not filename:
            print("No filename entered.")
            continue
        if not os.path.exists(filename):
            print(f"{filename} not found.")
            continue
        return filename


# ---------- file helpers ----------
# Everything that reads/writes people lists or expense files.
def write_people_file(people: list[str], path: str = DEFAULT_PEOPLE_FILE) -> None:
    with open(path, "w", newline="") as file:
        for person in people:
            file.write(person + "\n")


def read_people_file(path: str) -> list[str]:
    """Return cleaned list of names from people.txt."""
    with open(path, "r") as file:
        return [line.strip() for line in file if line.strip()]


def normalize_name(name: str) -> str:
    name = name.strip()
    return "GRP" if name.upper() == "GRP" else name.lower()


def normalize_people_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", newline="") as file:
        names = [normalize_name(line) for line in file if line.strip()]
    with open(path, "w", newline="") as file:
        for name in names:
            file.write(name + "\n")


def normalize_expenses_file(path: str) -> None:
    if not os.path.exists(path):
        return
    rows: list[list[str]] = []
    with open(path, "r", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) < 4:
                continue
            item = normalize_name(row[0])
            amount = row[1].strip()
            payer = normalize_name(row[2])
            participants = [normalize_name(p) for p in row[3].split(",") if p.strip()]
            rows.append([item, amount, payer, ",".join(participants)])
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)


def collect_people(existing: list[str] | None = None) -> list[str] | None:
    """Interactive name collection; enforces uniqueness and minimum group size."""
    people = set(normalize_name(p) for p in (existing or []))
    while True:
        name = input("Enter the name of a person (or press Enter to finish): ").strip()
        if name == "":
            break
        name = normalize_name(name)
        if name in people:
            print("Person already exists.")
            continue
        people.add(name)

    if len(people) < 2:
        print("At least two people are required.")
        return None

    return sorted(people)


def choose_person(prompt_label: str, people: list[str]) -> str | None:
    """Ask user to pick one name from the list."""
    if not people:
        print_status("No people available.")
        return None
    display = [p.title() if p != "GRP" else p for p in people]
    idx = ask_choice(prompt_label, display)
    return people[idx - 1]


def create_expenses_file(path: str = DEFAULT_EXPENSES_FILE) -> None:
    """Initialize an expenses CSV with the standard header."""
    with open(path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADERS)


def append_expense(expense: Expense, path: str = DEFAULT_EXPENSES_FILE) -> None:
    """Persist a single expense row."""
    with open(path, "a+", newline="") as file:
        file.seek(0)
        content = file.read()
        if content and not content.endswith(("\n", "\r")):
            file.write("\n")
        writer = csv.writer(file)
        writer.writerow([normalize_name(expense.item), expense.amount, normalize_name(expense.payer), ",".join(expense.participants)])


def load_expenses(path: str = DEFAULT_EXPENSES_FILE) -> list[Expense]:
    """Return all expenses from CSV; ignore incomplete rows."""
    if not os.path.exists(path):
        return []
    expenses: list[Expense] = []
    with open(path, "r", newline="") as file:
        reader = csv.reader(file)
        first = next(reader, None)
        rows = []
        if first:
            if first[:4] == CSV_HEADERS:
                rows = list(reader)
            else:
                rows = [first] + list(reader)
        for row in rows:
            if len(row) < 4:
                continue
            item, amount_raw, payer, participants = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
            if not item or not payer or not amount_raw:
                continue
            try:
                amount = float(amount_raw)
            except ValueError:
                continue
            participant_list = [p.strip() for p in participants.split(",") if p.strip()]
            if not participant_list:
                continue
            expenses.append(Expense(item=normalize_name(item), amount=amount, payer=normalize_name(payer), participants=[normalize_name(p) for p in participant_list]))
    return expenses


def ensure_expenses_header(path: str) -> None:
    """Guarantee the expenses file starts with CSV_HEADERS; preserve existing rows."""
    if not os.path.exists(path):
        return
    with open(path, "r", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        create_expenses_file(path)
        return
    if rows[0][:4] == CSV_HEADERS:
        return
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)
        writer.writerows(rows)


def condense_grp_entries(expenses_path: str, people_path: str) -> None:
    """Replace participant lists that exactly match the people set with GRP."""
    if not os.path.exists(expenses_path) or not os.path.exists(people_path):
        return
    people = set(normalize_name(name) for name in read_people_file(people_path))
    if not people:
        return

    with open(expenses_path, "r", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return
    has_header = rows[0][:4] == CSV_HEADERS
    data_rows = rows[1:] if has_header else rows
    changed = False
    for row in data_rows:
        if len(row) < 4:
            continue
        participants = [normalize_name(p) for p in row[3].split(",") if p.strip()]
        if participants and set(participants) == people and len(participants) == len(people):
            if row[3] != "GRP":
                row[3] = "GRP"
                changed = True

    if not changed:
        return

    with open(expenses_path, "w", newline="") as f:
        writer = csv.writer(f)
        if has_header:
            writer.writerow(rows[0])
        writer.writerows(data_rows)


def compute_balances(expenses: list[Expense], people: list[str]) -> dict[str, float]:
    """Return each person’s net balance (positive = owed money)."""
    balances = {person: 0.0 for person in people}
    if not people:
        return balances

    for expense in expenses:
        participants = (
            people if len(expense.participants) == 1 and expense.participants[0] == "GRP" else expense.participants
        )
        if not participants:
            continue
        share = expense.amount / len(participants)
        balances.setdefault(expense.payer, 0.0)
        balances[expense.payer] += expense.amount
        for participant in participants:
            if participant not in balances:
                balances[participant] = 0.0
            balances[participant] -= share
    return balances


def people_from_expenses(csv_path: str) -> set[str]:
    """Harvest unique payers/participants from an expenses CSV (ignores GRP token)."""
    people: set[str] = set()
    with open(csv_path, "r", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)  # skip header if present
        for row in reader:
            if len(row) < 4:
                continue
            payer = normalize_name(row[2])
            if payer:
                people.add(payer)
            participants = [normalize_name(p) for p in row[3].split(",") if p.strip()]
            for participant in participants:
                if participant != "GRP":
                    people.add(participant)
    return people


def expenses_contain_grp(csv_path: str) -> bool:
    """Detect whether any expense row uses the GRP shorthand."""
    with open(csv_path, "r", newline="") as file:
        reader = csv.reader(file)
        next(reader, None)
        return any(len(row) >= 4 and "GRP" in row[3] for row in reader)


def match_people(expenses_path: str, people_path: str) -> bool:
    """Ensure no unknown names appear in expenses compared to people file."""
    csv_people = people_from_expenses(expenses_path)
    txt_people = set(normalize_name(p) for p in read_people_file(people_path))
    return csv_people.issubset(txt_people)


def is_valid_database(expenses_path: str, people_path: str) -> bool:
    """Full validation: files exist, >=2 people, and participants match."""
    if not os.path.exists(expenses_path):
        print(f"{expenses_path} not found.")
        return False

    if not os.path.exists(people_path):
        print(f"{people_path} not found.")
        return False

    if len(read_people_file(people_path)) < 2:
        print("At least two people are required.")
        return False

    if not match_people(expenses_path, people_path):
        print("Files are corrupted.")
        return False

    return True


# ---------- session flows ----------
# Orchestrate the Start Menu paths.
def start_new_session() -> bool:
    """Create fresh expense/people files and gather the group."""
    print_section_header("Start New Session")
    create_expenses_file(DEFAULT_EXPENSES_FILE)
    people = collect_people()
    if not people:
        print_status("Session initialization cancelled.")
        return False
    write_people_file(people, DEFAULT_PEOPLE_FILE)
    print_status("People list saved.")
    normalize_people_file(DEFAULT_PEOPLE_FILE)
    return True


def continue_previous_session() -> bool:
    """Validate and reuse the default filenames without prompting."""
    print_section_header("Continue Previous Session")
    if is_valid_database(DEFAULT_EXPENSES_FILE, DEFAULT_PEOPLE_FILE):
        print_status("Existing expenses and people files validated.")
        return True
    print_status("Continuing session aborted.")
    print_divider()
    return False


def maybe_extend_people(people_file: str) -> None:
    """Optional add-on when loading a GRP-based file."""
    if not ask_yes_no("Do you want to add more people? (y/n): "):
        return
    current_people = read_people_file(people_file)
    updated_people = collect_people(current_people)
    if updated_people:
        write_people_file(updated_people, people_file)
        print_status("People list updated.")


def load_session() -> bool:
    """Load user-specified expense file; handle GRP vs non-GRP paths."""
    print_section_header("Load Session From Files")
    expenses_filename = prompt_existing_file("expenses")
    if not expenses_filename:
        print_status("Load cancelled.")
        print_divider()
        return False
    if not expenses_filename.lower().endswith(".csv"):
        print_status("Expenses file must use .csv extension.")
        print_divider()
        return False

    if expenses_contain_grp(expenses_filename):
        print_status('"GRP" token detected; people file required.')
        people_filename = prompt_existing_file("people list (required because \"GRP\" token is used)")
        if not people_filename:
            print_status("Load cancelled.")
            print_divider()
            return False
        if not people_filename.lower().endswith(".txt"):
            print_status("People list must use .txt extension.")
            print_divider()
            return False
        if not is_valid_database(expenses_filename, people_filename):
            print_status("Load failed due to validation errors.")
            print_divider()
            return False
        try:
            if os.path.abspath(people_filename) != os.path.abspath(DEFAULT_PEOPLE_FILE):
                shutil.copyfile(people_filename, DEFAULT_PEOPLE_FILE)
                print_status(f"Copied {people_filename} -> {DEFAULT_PEOPLE_FILE}.")
            else:
                print_status(f"Using existing {DEFAULT_PEOPLE_FILE}.")
        except OSError:
            print_status("Failed to sync people file.")
            print_divider()
            return False
        normalize_people_file(DEFAULT_PEOPLE_FILE)
    else:
        people = people_from_expenses(expenses_filename)
        if len(people) < 2:
            print("At least two people are required.")
            print_status("Load cancelled.")
            print_divider()
            return False
        write_people_file(sorted(people), DEFAULT_PEOPLE_FILE)
        normalize_people_file(DEFAULT_PEOPLE_FILE)
        print_status(f"Generated {DEFAULT_PEOPLE_FILE} from {expenses_filename}.")
        maybe_extend_people(DEFAULT_PEOPLE_FILE)

    try:
        if os.path.abspath(expenses_filename) != os.path.abspath(DEFAULT_EXPENSES_FILE):
            shutil.copyfile(expenses_filename, DEFAULT_EXPENSES_FILE)
            print_status(f"Copied {expenses_filename} -> {DEFAULT_EXPENSES_FILE}.")
        else:
            print_status(f"Using existing {DEFAULT_EXPENSES_FILE}.")
        normalize_expenses_file(DEFAULT_EXPENSES_FILE)
        ensure_expenses_header(DEFAULT_EXPENSES_FILE)
        condense_grp_entries(DEFAULT_EXPENSES_FILE, DEFAULT_PEOPLE_FILE)
    except OSError:
        print_status("Failed to sync expenses file.")
        print_divider()
        return False

    print_status("Session loaded.")
    return True


# ---------- expense workflows ----------
def prompt_amount() -> float:
    """Prompt for a numeric amount; confirm on negative the first time."""
    global NEGATIVE_CONFIRMED_ONCE
    while True:
        raw = input("Enter amount: ").strip()
        try:
            amount = float(raw)
        except ValueError:
            print("Invalid amount. Please enter a number.")
            continue
        if amount < 0 and not NEGATIVE_CONFIRMED_ONCE:
            if not ask_yes_no("You entered a negative amount. Are you sure? (y/n): "):
                continue
            NEGATIVE_CONFIRMED_ONCE = True
        return amount


def prompt_participants(people: list[str]) -> list[str] | None:
    """Let user choose participants; GRP (everyone) available as option 0."""
    if not people:
        print_status("No people available.")
        return None

    print("Participants:")
    print("0. GRP (entire group)")
    for i, person in enumerate(people, start=1):
        print(f"{i}. {person}")

    while True:
        raw = input("Enter participant numbers separated by commas (e.g., 1,3) or 0 for GRP: ").strip()
        if not raw:
            print("Please enter at least one participant.")
            continue
        try:
            choices = {int(x) for x in raw.split(",")}
        except ValueError:
            print("Invalid input. Use numbers separated by commas.")
            continue

        if 0 in choices:
            return ["GRP"]

        invalid = [c for c in choices if c < 1 or c > len(people)]
        if invalid:
            print(f"Invalid choices: {invalid}")
            continue

        return [people[c - 1] for c in sorted(choices)]


def add_expense(expenses_path: str = DEFAULT_EXPENSES_FILE, people_path: str = DEFAULT_PEOPLE_FILE) -> None:
    """Interactive flow to add an expense entry."""
    print_section_header("Add Expense")

    if not os.path.exists(people_path):
        print_status(f"{people_path} not found.")
        print_divider()
        return
    people = read_people_file(people_path)
    if len(people) < 2:
        print_status("Need at least two people to add an expense.")
        print_divider()
        return

    payer = choose_person("Select payer", people)
    if not payer:
        print_divider()
        return

    amount = prompt_amount()

    item = ""
    while not item:
        item = input("Enter item/description: ").strip()
        if not item:
            print("Item cannot be empty.")
        else:
            item = item.title()

    participants = prompt_participants(people)
    if not participants:
        print_divider()
        return

    expense = Expense(item=item, amount=amount, payer=payer, participants=participants)
    append_expense(expense, DEFAULT_EXPENSES_FILE)
    print_status(f"Added expense: {item} ({amount}) by {payer} for {','.join(participants)}")
    print_divider()


def _ensure_people_for_ui() -> list[str] | None:
    if not os.path.exists(DEFAULT_PEOPLE_FILE):
        print_status(f"{DEFAULT_PEOPLE_FILE} not found.")
        return None
    people = read_people_file(DEFAULT_PEOPLE_FILE)
    if len(people) < 2:
        print_status("Need at least two people to compute balances.")
        return None
    return people


def view_balances() -> None:
    """Display computed balances using a grid."""
    print_section_header("View Balances")
    people = _ensure_people_for_ui()
    if not people:
        print_divider()
        return
    expenses = load_expenses()
    balances = compute_balances(expenses, people)
    if not balances:
        print_status("No balances to show.")
        print_divider()
        return
    rows = []
    for name in sorted(balances):
        display_name = name.title() if name != "GRP" else name
        rows.append([display_name, f"{balances[name]:+.2f}"])
    print(tabulate(rows, headers=["Person", "Balance"], tablefmt="grid"))
    print_divider()


def settle_debt() -> None:
    """Greedy transfer suggestions to zero out balances."""
    print_section_header("Settle Debt")
    people = _ensure_people_for_ui()
    if not people:
        print_divider()
        return
    expenses = load_expenses()
    balances = compute_balances(expenses, people)
    transfers: list[tuple[str, str, float]] = []
    creditors = [(name, bal) for name, bal in balances.items() if bal > 0.0]
    debtors = [(name, -bal) for name, bal in balances.items() if bal < 0.0]
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    ci = di = 0
    while ci < len(creditors) and di < len(debtors):
        creditor, credit_amt = creditors[ci]
        debtor, debt_amt = debtors[di]
        transfer = min(credit_amt, debt_amt)
        transfers.append((debtor, creditor, transfer))
        credit_amt -= transfer
        debt_amt -= transfer
        creditors[ci] = (creditor, credit_amt)
        debtors[di] = (debtor, debt_amt)
        if credit_amt <= 1e-9:
            ci += 1
        if debt_amt <= 1e-9:
            di += 1
    if not transfers:
        print_status("All balances are settled.")
        print_divider()
        return
    rows = [[debtor.title() if debtor != "GRP" else debtor,
             creditor.title() if creditor != "GRP" else creditor,
             f"{amount:.2f}"]
            for debtor, creditor, amount in transfers]
    print(tabulate(rows, headers=["Payer", "Receiver", "Amount"], tablefmt="grid"))
    print_divider()


def view_expenses(expenses_path: str = DEFAULT_EXPENSES_FILE) -> None:
    print_section_header("View Expenses")
    if not os.path.exists(expenses_path):
        print_status(f"{expenses_path} not found.")
        print_divider()
        return
    with open(expenses_path, "r", newline="") as file:
        table = []
        reader = list(csv.reader(file))
        data_rows = reader[1:] if reader and reader[0][:4] == CSV_HEADERS else reader
        for row in data_rows:
            if len(row) < 4:
                continue
            participants = ", ".join(p.strip() for p in row[3].split(",") if p.strip())
            table.append([row[0].title(), row[1], row[2].title(), participants.title()])
    if not table:
        print_status("No expenses recorded.")
        print_divider()
        return
    print(tabulate(table, headers=CSV_HEADERS, tablefmt="grid"))
    print_divider()

# ---------- main ----------
def main():
    print_section_header("Expense Tracker")

    while True:
        print_section_header("Start Menu")
        choice = ask_choice(
            "Start Menu",
            ["Start new session", "Continue previous session", "Load a session", "Exit"],
        )
        match choice:
            case 1:
                if start_new_session():
                    break
            case 2:
                if continue_previous_session():
                    break
            case 3:
                if load_session():
                    break
            case 4:
                print_status("Goodbye!")
                sys.exit(0)
            case _:
                print("Invalid choice. Please try again.\n")

    while True:
        print_section_header("Function Menu")
        f_choice = ask_choice(
            "Function Menu",
            ["Add Expense", "View Expenses", "View Balances", "Settle Debt", "Exit"],
        )
        match f_choice:
            case 1:
                add_expense()
            case 2:
                view_expenses()
            case 3:
                view_balances()
            case 4:
                settle_debt()
            case 5:
                print_status("Goodbye!")
                sys.exit(0)


if __name__ == "__main__":
    main()

