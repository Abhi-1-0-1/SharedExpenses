import csv
from pathlib import Path

import pytest

import project


SAMPLE_DIR = Path(__file__).parent / "sampleData"


def copy_sample(tmp_path: Path, filename: str) -> Path:
    src = SAMPLE_DIR / filename
    dest = tmp_path / filename
    dest.write_bytes(src.read_bytes())
    return dest


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open(newline="") as f:
        return list(csv.reader(f))


def make_stores(tmp_path: Path, exp_name: str, people_name: str):
    people_path = copy_sample(tmp_path, people_name)
    exp_path = copy_sample(tmp_path, exp_name)
    people_store = project.PeopleStore(people_path)
    expense_store = project.ExpenseStore(exp_path, people_store)
    return people_store, expense_store


def test_normalize_expenses_adds_header_and_lowercases(tmp_path: Path):
    people_store, expense_store = make_stores(tmp_path, "expenses_missing_header.csv", "people_small.txt")
    expense_store.normalize()

    rows = read_csv_rows(expense_store.path)
    assert rows[0][:4] == project.CSV_HEADERS

    item, amount, payer, participants = rows[1][:4]
    assert item == "pizza"
    assert amount == "10"
    assert payer == "alice"
    assert participants == "GRP"

    item2, amount2, payer2, participants2 = rows[2][:4]
    assert item2 == "burger"
    assert amount2 == "15"
    assert payer2 == "bob"
    assert participants2 == "alice,bob"


def test_condense_grp_entries_converts_full_list(tmp_path: Path):
    people_store, expense_store = make_stores(tmp_path, "expenses_full_list.csv", "people_small.txt")
    expense_store.condense_grp()
    rows = read_csv_rows(expense_store.path)

    assert rows[0][:4] == project.CSV_HEADERS
    assert rows[1][3] == "GRP"


def test_match_people_detects_unknown(tmp_path: Path):
    people_store, expense_store = make_stores(tmp_path, "expenses_invalid_name.csv", "people_small.txt")
    assert expense_store.match_people() is False


def test_compute_balances_with_grp_expense():
    people = ["alice", "bob", "charlie"]
    expense = project.Expense(item="dinner", amount=90.0, payer="alice", participants=["GRP"])
    balances = project.BalanceCalculator.compute([expense], people)

    assert balances["alice"] == pytest.approx(60.0)
    assert balances["bob"] == pytest.approx(-30.0)
    assert balances["charlie"] == pytest.approx(-30.0)


def test_ensure_expenses_header_inserts_when_missing(tmp_path: Path):
    people_store, expense_store = make_stores(tmp_path, "expenses_missing_header.csv", "people_small.txt")
    with expense_store.path.open("w", newline="") as f:
        f.write("pizza,10,alice,grp\n")

    expense_store.ensure_header()
    rows = read_csv_rows(expense_store.path)
    assert rows[0][:4] == project.CSV_HEADERS
    assert rows[1][0] == "pizza"


def test_normalize_people_file_lowercases(tmp_path: Path):
    people_path = tmp_path / "people.txt"
    people_path.write_text("Alice\nBob\n")

    store = project.PeopleStore(people_path)
    store.normalize()
    assert store.read() == ["alice", "bob"]


def test_delete_expense_removes_selected_row_and_keeps_header(tmp_path: Path):
    people_store, expense_store = make_stores(tmp_path, "expenses_missing_header.csv", "people_small.txt")
    expense_store.normalize()

    removed = expense_store.delete_expense(0)
    rows = read_csv_rows(expense_store.path)

    assert removed is not None
    assert removed.item == "pizza"
    assert rows[0][:4] == project.CSV_HEADERS
    assert len(rows) == 2
    assert rows[1][0] == "burger"


def test_delete_expense_returns_none_for_invalid_index(tmp_path: Path):
    people_store, expense_store = make_stores(tmp_path, "expenses_missing_header.csv", "people_small.txt")
    expense_store.normalize()

    removed = expense_store.delete_expense(10)
    rows = read_csv_rows(expense_store.path)

    assert removed is None
    assert len(rows) == 3
