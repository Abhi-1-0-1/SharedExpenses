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


def test_normalize_expenses_adds_header_and_lowercases(tmp_path: Path):
    exp_path = copy_sample(tmp_path, "expenses_missing_header.csv")
    project.normalize_expenses_file(exp_path)

    rows = read_csv_rows(exp_path)
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
    people_path = copy_sample(tmp_path, "people_small.txt")
    exp_path = copy_sample(tmp_path, "expenses_full_list.csv")

    project.condense_grp_entries(exp_path, people_path)
    rows = read_csv_rows(exp_path)

    assert rows[0][:4] == project.CSV_HEADERS
    assert rows[1][3] == "GRP"


def test_match_people_detects_unknown(tmp_path: Path):
    people_path = copy_sample(tmp_path, "people_small.txt")
    exp_path = copy_sample(tmp_path, "expenses_invalid_name.csv")

    assert project.match_people(exp_path, people_path) is False


def test_compute_balances_with_grp_expense():
    people = ["alice", "bob", "charlie"]
    expense = project.Expense(item="dinner", amount=90.0, payer="alice", participants=["GRP"])
    balances = project.compute_balances([expense], people)

    assert balances["alice"] == pytest.approx(60.0)
    assert balances["bob"] == pytest.approx(-30.0)
    assert balances["charlie"] == pytest.approx(-30.0)


def test_ensure_expenses_header_inserts_when_missing(tmp_path: Path):
    exp_path = copy_sample(tmp_path, "expenses_missing_header.csv")
    with exp_path.open("w", newline="") as f:
        f.write("pizza,10,alice,grp\n")

    project.ensure_expenses_header(exp_path)
    rows = read_csv_rows(exp_path)
    assert rows[0][:4] == project.CSV_HEADERS
    assert rows[1][0] == "pizza"


def test_normalize_people_file_lowercases(tmp_path: Path):
    people_path = tmp_path / "people.txt"
    people_path.write_text("Alice\nBob\n")

    project.normalize_people_file(people_path)
    assert people_path.read_text().splitlines() == ["alice", "bob"]

