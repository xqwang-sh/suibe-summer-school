"""Read and validate the audited Lecture 2 equity-submarket dataset."""

from __future__ import annotations

import csv
from pathlib import Path


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "lecture2"
    / "equity_submarket_cap.csv"
)
REQUIRED_COLUMN_ORDER = [
    "submarket",
    "period",
    "value",
    "unit",
    "scope",
    "source_id",
]
REQUIRED_COLUMNS = set(REQUIRED_COLUMN_ORDER)
SUBMARKET_ORDER = {
    "Main Boards": 0,
    "STAR Market": 1,
    "ChiNext": 2,
    "Beijing Stock Exchange": 3,
}
AUDITED_HISTORICAL_MAIN_BOARDS = {
    "2005": ("3.243033", "equity_main_boards_2005_2006"),
    "2006": ("8.940388", "equity_main_boards_2005_2006"),
    "2007": ("32.729127", "equity_main_boards_2007_2016"),
    "2008": ("12.154111", "equity_main_boards_2007_2016"),
    "2009": ("24.249383", "equity_main_boards_2007_2016"),
    "2010": ("25.805734", "equity_main_boards_2007_2016"),
    "2011": ("20.732432", "equity_main_boards_2007_2016"),
    "2012": ("22.162634", "equity_main_boards_2007_2016"),
    "2013": ("22.398517", "equity_main_boards_2007_2016"),
    "2014": ("35.069602", "equity_main_boards_2007_2016"),
    "2015": ("47.538800", "equity_main_boards_2007_2016"),
    "2016": ("45.543143", "equity_main_boards_2007_2016"),
    "2017": ("51.57972630", "equity_main_boards_2017_history"),
    "2018": ("39.44644398", "equity_main_boards_2018_history"),
}


def read_equity_submarket_cap(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Return equity-submarket observations after enforcing the CSV schema."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            raise ValueError(f"unexpected columns: {set(reader.fieldnames or ())}")
        return list(reader)


def prepare_equity_submarket_cap(path: Path = DATA_PATH) -> None:
    """Merge only directly audited historical Main Boards observations."""
    rows = [
        row
        for row in read_equity_submarket_cap(path)
        if not (
            row["submarket"] == "Main Boards"
            and row["period"] in AUDITED_HISTORICAL_MAIN_BOARDS
        )
    ]
    rows.extend(
        {
            "submarket": "Main Boards",
            "period": period,
            "value": value,
            "unit": "RMB trillion",
            "scope": "year-end total market capitalization",
            "source_id": source_id,
        }
        for period, (value, source_id) in AUDITED_HISTORICAL_MAIN_BOARDS.items()
    )
    rows.sort(key=lambda row: (SUBMARKET_ORDER[row["submarket"]], int(row["period"])))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMN_ORDER)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    prepare_equity_submarket_cap()
