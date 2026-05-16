import csv
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from tabulate import tabulate


# ----------------- constants -----------------
CSV_HEADERS = ["Item", "Amount", "Payer", "Participants"]
DEFAULT_EXPENSES_FILE = "workingFiles/expenses.csv"
DEFAULT_PEOPLE_FILE = "workingFiles/people.txt"
SEPARATOR_WIDTH = 60


# ----------------- helpers -----------------
def normalize_name(name: str) -> str:
    name = name.strip()
    return "GRP" if name.upper() == "GRP" else name.lower()


def title_case(name: str) -> str:
    return name if name == "GRP" else name.title()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Expense:
    item: str
    amount: float
    payer: str
    participants: List[str]


class Renderer:
    @staticmethod
    def divider(char: str = "-", width: int = SEPARATOR_WIDTH) -> None:
        print(char * width)

    @staticmethod
    def header(title: str) -> None:
        Renderer.divider("=")
        centered = title.center(SEPARATOR_WIDTH)
        print(centered)
        Renderer.divider("=")

    @staticmethod
    def status(msg: str) -> None:
        print(f"> {msg}")

    @staticmethod
    def list_choices(prompt: str, choices: list[str]) -> None:
        print(prompt)
        for idx, choice in enumerate(choices, start=1):
            print(f"{idx}. {choice}")

    @staticmethod
    def ask_choice(prompt: str, choices: list[str]) -> int:
        while True:
            try:
                choice = int(input("Enter your choice: ").strip())
                if 1 <= choice <= len(choices):
                    return choice
                raise ValueError
            except ValueError:
                Renderer.status(f"Please enter a number between 1 and {len(choices)}.")

    @staticmethod
    def ask_yes_no(prompt: str) -> bool:
        while True:
            answer = input(f"{prompt} (y/n): ").strip().lower()
            if answer in {"y", "yes"}:
                return True
            if answer in {"n", "no"}:
                return False
            Renderer.status("Please answer y or n.")


class PeopleStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def exists(self) -> bool:
        return self.path.exists()

    def read(self) -> list[str]:
        if not self.path.exists():
            return []
        with self.path.open("r", newline="") as f:
            return [line.strip() for line in f if line.strip()]

    def write(self, people: Iterable[str]) -> None:
        ensure_parent(self.path)
        with self.path.open("w", newline="") as f:
            for person in people:
                f.write(person + "\n")

    def normalize(self) -> None:
        people = [normalize_name(p) for p in self.read() if p.strip()]
        self.write(people)

    def collect_interactive(self) -> list[str] | None:
        Renderer.header("Add People")
        people: set[str] = set()
        while True:
            name = input("Enter the name of a person (or press Enter to finish): ").strip()
            if not name:
                break
            normalized = normalize_name(name)
            if normalized in people:
                Renderer.status("Person already exists.")
                continue
            people.add(normalized)
        if len(people) < 2:
            Renderer.status("At least two people are required.")
            return None
        ordered = sorted(people)
        self.write(ordered)
        return ordered


class ExpenseStore:
    def __init__(self, path: Path, people_store: PeopleStore) -> None:
        self.path = path
        self.people_store = people_store

    def exists(self) -> bool:
        return self.path.exists()

    def ensure_header(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            self.create_blank()
            return
        if rows[0][:4] == CSV_HEADERS:
            return
        with self.path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            writer.writerows(rows)

    def create_blank(self) -> None:
        ensure_parent(self.path)
        with self.path.open("w", newline="") as f:
            csv.writer(f).writerow(CSV_HEADERS)

    def normalize(self) -> None:
        if not self.path.exists():
            return
        rows: list[list[str]] = []
        with self.path.open("r", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 4:
                    continue
                item = normalize_name(row[0])
                amount = row[1].strip()
                payer = normalize_name(row[2])
                participants = [normalize_name(p) for p in row[3].split(",") if p.strip()]
                rows.append([item, amount, payer, ",".join(sorted(set(participants)))])
        with self.path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            writer.writerows(rows)

    def load(self) -> list[Expense]:
        if not self.path.exists():
            return []
        with self.path.open("r", newline="") as f:
            reader = csv.reader(f)
            first = next(reader, None)
            data_rows = []
            if first:
                if first[:4] == CSV_HEADERS:
                    data_rows = list(reader)
                else:
                    data_rows = [first] + list(reader)
        expenses: list[Expense] = []
        for row in data_rows:
            if len(row) < 4:
                continue
            item, amount_raw, payer, participants = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
            try:
                amount = float(amount_raw)
            except ValueError:
                continue
            participants_list = [normalize_name(p) for p in participants.split(",") if p.strip()]
            if not participants_list:
                continue
            expenses.append(
                Expense(
                    item=normalize_name(item),
                    amount=amount,
                    payer=normalize_name(payer),
                    participants=participants_list,
                )
            )
        return expenses

    def append(self, expense: Expense) -> None:
        ensure_parent(self.path)
        with self.path.open("a+", newline="") as f:
            f.seek(0)
            content = f.read()
            if content and not content.endswith(("\n", "\r")):
                f.write("\n")
            writer = csv.writer(f)
            writer.writerow(
                [
                    normalize_name(expense.item),
                    expense.amount,
                    normalize_name(expense.payer),
                    ",".join(sorted(set(expense.participants))),
                ]
            )

    def delete_expense(self, index: int) -> Expense | None:
        expenses = self.load()
        if index < 0 or index >= len(expenses):
            return None

        removed = expenses.pop(index)
        ensure_parent(self.path)
        with self.path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            for expense in expenses:
                writer.writerow(
                    [
                        normalize_name(expense.item),
                        expense.amount,
                        normalize_name(expense.payer),
                        ",".join(sorted(set(expense.participants))),
                    ]
                )
        return removed

    def condense_grp(self) -> None:
        if not self.path.exists() or not self.people_store.exists():
            return
        people = set(normalize_name(p) for p in self.people_store.read())
        if not people:
            return
        with self.path.open("r", newline="") as f:
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
            if set(participants) == people and len(participants) == len(people):
                if row[3] != "GRP":
                    row[3] = "GRP"
                    changed = True
        if not changed:
            return
        with self.path.open("w", newline="") as f:
            writer = csv.writer(f)
            if has_header:
                writer.writerow(rows[0])
            writer.writerows(data_rows)

    def people_from_expenses(self) -> set[str]:
        if not self.path.exists():
            return set()
        people: set[str] = set()
        with self.path.open("r", newline="") as f:
            reader = csv.reader(f)
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

    def match_people(self) -> bool:
        csv_people = self.people_from_expenses()
        txt_people = set(normalize_name(p) for p in self.people_store.read())
        return csv_people.issubset(txt_people)


class BalanceCalculator:
    @staticmethod
    def compute(expenses: list[Expense], people: list[str]) -> dict[str, float]:
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
                balances.setdefault(participant, 0.0)
                balances[participant] -= share
        return balances

    @staticmethod
    def greedy_settlement(balances: dict[str, float]) -> list[tuple[str, str, float]]:
        debtors = [(p, -amt) for p, amt in balances.items() if amt < 0]
        creditors = [(p, amt) for p, amt in balances.items() if amt > 0]
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)

        settlements = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            debtor, debt_amt = debtors[i]
            creditor, cred_amt = creditors[j]
            pay = min(debt_amt, cred_amt)
            settlements.append((debtor, creditor, pay))
            debt_amt -= pay
            cred_amt -= pay
            if debt_amt == 0:
                i += 1
            else:
                debtors[i] = (debtor, debt_amt)
            if cred_amt == 0:
                j += 1
            else:
                creditors[j] = (creditor, cred_amt)
        return settlements


class SessionManager:
    def __init__(self, expenses_path: Path, people_path: Path) -> None:
        self.people = PeopleStore(people_path)
        self.expenses = ExpenseStore(expenses_path, self.people)

    def _valid_extensions(self, exp_file: Path, people_file: Path) -> bool:
        if exp_file.suffix.lower() != ".csv":
            Renderer.status("Expenses file must have .csv extension.")
            return False
        if people_file.suffix.lower() != ".txt":
            Renderer.status("People file must have .txt extension.")
            return False
        return True

    def start_new(self) -> bool:
        Renderer.header("Start New Session")
        self.expenses.create_blank()
        people = self.people.collect_interactive()
        if people is None:
            return False
        Renderer.status("Session created.")
        return True

    def continue_previous(self) -> bool:
        Renderer.header("Continue Previous Session")
        if not self.expenses.exists() or not self.people.exists():
            Renderer.status("No existing session. Create a new one.")
            return False
        Renderer.status("Session loaded.")
        return True

    def load_session(self) -> bool:
        Renderer.header("Load Session From Files")
        exp_name = input("Enter the expenses filename: ").strip()
        people_name = input("Enter the people filename: ").strip()
        src_exp = Path(exp_name)
        src_people = Path(people_name)
        if not self._valid_extensions(src_exp, src_people):
            return False
        if not src_exp.exists() or not src_people.exists():
            Renderer.status("One or both files not found.")
            return False

        # copy into canonical files
        shutil.copy(src_exp, self.expenses.path)
        shutil.copy(src_people, self.people.path)

        # normalize and validate
        self.people.normalize()
        self.expenses.ensure_header()
        self.expenses.normalize()
        self.expenses.condense_grp()

        if not self.expenses.match_people():
            Renderer.status("Files are corrupted (unknown names in expenses).")
            return False

        Renderer.status("Session loaded and normalized.")
        return True


class ExpenseTrackerApp:
    def __init__(self) -> None:
        self.session = SessionManager(Path(DEFAULT_EXPENSES_FILE), Path(DEFAULT_PEOPLE_FILE))

    # ------------- UI actions -------------
    def add_expense(self) -> None:
        people = self.session.people.read()
        if len(people) < 2:
            Renderer.status("Add at least two people first.")
            return
        Renderer.header("Add Expense")
        display_people = [title_case(p) for p in people]
        Renderer.list_choices("Select payer:", display_people)
        payer_idx = Renderer.ask_choice("Select payer:", display_people) - 1
        payer = people[payer_idx]

        amount = self._prompt_amount()
        if amount is None:
            return

        item = normalize_name(input("Enter item/description: ").strip())
        participants = self._prompt_participants(people)
        if participants is None:
            return

        expense = Expense(item=item, amount=amount, payer=payer, participants=participants)
        self.session.expenses.append(expense)
        Renderer.status(
            f"Added expense: {item.title()} ({amount}) by {title_case(payer)} for {self._participants_label(participants)}"
        )
        Renderer.divider()

    def view_expenses(self) -> None:
        Renderer.header("View Expenses")
        expenses = self.session.expenses.load()
        if not expenses:
            Renderer.status("No expenses recorded.")
            Renderer.divider()
            return
        table = []
        for idx, exp in enumerate(expenses, start=1):
            participants = ", ".join(title_case(p) for p in exp.participants) if exp.participants != ["GRP"] else "GRP"
            table.append([idx, exp.item.title(), exp.amount, title_case(exp.payer), participants])
        print(tabulate(table, headers=["No."] + CSV_HEADERS, tablefmt="grid"))
        Renderer.divider()

    def view_people(self) -> None:
        Renderer.header("View People")
        people = self.session.people.read()
        if not people:
            Renderer.status("No people stored.")
            Renderer.divider()
            return
        rows = [[idx, title_case(person)] for idx, person in enumerate(people, start=1)]
        print(tabulate(rows, headers=["No.", "Person"], tablefmt="grid"))
        Renderer.divider()

    def delete_expense(self) -> None:
        Renderer.header("Delete Expense")
        expenses = self.session.expenses.load()
        if not expenses:
            Renderer.status("No expenses recorded.")
            Renderer.divider()
            return

        table = []
        for idx, exp in enumerate(expenses, start=1):
            participants = ", ".join(title_case(p) for p in exp.participants) if exp.participants != ["GRP"] else "GRP"
            table.append([idx, exp.item.title(), exp.amount, title_case(exp.payer), participants])
        print(tabulate(table, headers=["No."] + CSV_HEADERS, tablefmt="grid"))

        while True:
            raw = input("Enter the expense number to delete (or press Enter to cancel): ").strip()
            if raw == "":
                Renderer.status("Deletion cancelled.")
                Renderer.divider()
                return
            try:
                choice = int(raw)
                removed = self.session.expenses.delete_expense(choice - 1)
                if removed is None:
                    raise ValueError
                Renderer.status(
                    f"Deleted expense: {removed.item.title()} ({removed.amount}) by {title_case(removed.payer)}"
                )
                Renderer.divider()
                return
            except ValueError:
                Renderer.status(f"Please enter a number between 1 and {len(expenses)}.")

    def view_balances(self) -> None:
        Renderer.header("View Balances")
        people = self.session.people.read()
        expenses = self.session.expenses.load()
        balances = BalanceCalculator.compute(expenses, people)
        rows = [[title_case(person), round(amount, 2)] for person, amount in balances.items()]
        print(tabulate(rows, headers=["Person", "Balance"], tablefmt="grid"))
        Renderer.divider()

    def settle_debt(self) -> None:
        Renderer.header("Settle Debt")
        people = self.session.people.read()
        expenses = self.session.expenses.load()
        balances = BalanceCalculator.compute(expenses, people)
        settlements = BalanceCalculator.greedy_settlement(balances)
        if not settlements:
            Renderer.status("No debts to settle.")
            Renderer.divider()
            return
        for debtor, creditor, amount in settlements:
            print(f"{title_case(debtor)} pays {title_case(creditor)} {amount:.2f}")
        Renderer.divider()

    # ------------- menus -------------
    def start_menu(self) -> bool:
        while True:
            Renderer.header("Start Menu")
            options = [
                "Start new session",
                "Continue previous session",
                "Load a session",
                "Exit",
            ]
            Renderer.list_choices("Start Menu:", options)
            choice = Renderer.ask_choice("Start Menu:", options)
            if choice == 1 and self.session.start_new():
                return True
            if choice == 2 and self.session.continue_previous():
                return True
            if choice == 3 and self.session.load_session():
                return True
            if choice == 4:
                return False

    def function_menu(self) -> None:
        while True:
            Renderer.header("Function Menu")
            options = [
                "Add Expense",
                "View Expenses",
                "Delete Expense",
                "View People",
                "View Balances",
                "Settle Debt",
                "Exit",
            ]
            Renderer.list_choices("Function Menu:", options)
            choice = Renderer.ask_choice("Function Menu:", options)
            if choice == 1:
                self.add_expense()
            elif choice == 2:
                self.view_expenses()
            elif choice == 3:
                self.delete_expense()
            elif choice == 4:
                self.view_people()
            elif choice == 5:
                self.view_balances()
            elif choice == 6:
                self.settle_debt()
            elif choice == 7:
                break

    # ------------- helpers -------------
    def _prompt_amount(self) -> float | None:
        while True:
            raw = input("Enter amount: ").strip()
            try:
                amount = float(raw)
                if amount <= 0:
                    raise ValueError
                return amount
            except ValueError:
                Renderer.status("Enter a positive number.")

    def _prompt_participants(self, people: list[str]) -> list[str] | None:
        print("Participants:")
        print("0. GRP (entire group)")
        for idx, name in enumerate(people, start=1):
            print(f"{idx}. {title_case(name)}")
        while True:
            raw = input("Enter participant numbers separated by commas (e.g., 1,3) or 0 for GRP: ").strip()
            if raw == "0":
                return ["GRP"]
            try:
                indexes = [int(x) for x in raw.split(",") if x.strip()]
                if not indexes:
                    raise ValueError
                if any(i < 1 or i > len(people) for i in indexes):
                    raise ValueError
                participants = sorted(set(people[i - 1] for i in indexes))
                return participants
            except ValueError:
                Renderer.status("Invalid selection. Try again.")

    @staticmethod
    def _participants_label(participants: list[str]) -> str:
        if participants == ["GRP"]:
            return "GRP"
        return ", ".join(title_case(p) for p in participants)

    # ------------- app entry -------------
    def run(self) -> None:
        Renderer.header("SharedExpenses")
        if self.start_menu():
            self.function_menu()


def main() -> None:
    app = ExpenseTrackerApp()
    app.run()


if __name__ == "__main__":
    main()
