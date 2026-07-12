"""Contract tests for Lecture 2's audited equity-submarket data."""

from __future__ import annotations

import csv
import importlib.util
import unittest
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
MODULE_PATH = SCRIPT_DIR / "prepare_lecture2_data.py"
MANIFEST_PATH = PROJECT_DIR / "data" / "lecture2" / "source_manifest.csv"
EXPECTED_VALUES_PATH = SCRIPT_DIR / "fixtures" / "lecture2_equity_expected.csv"

EXPECTED_SUBMARKETS = {
    "Main Boards",
    "STAR Market",
    "ChiNext",
    "Beijing Stock Exchange",
}
EXPECTED_PERIODS = {
    "Main Boards": set(range(2005, 2026)),
    "STAR Market": set(range(2019, 2026)),
    "ChiNext": set(range(2010, 2026)),
    "Beijing Stock Exchange": set(range(2021, 2026)),
}
AUDITED_MAIN_BOARD_VALUES = {
    "2005": "3.243033",
    "2006": "8.940388",
    "2007": "32.729127",
    "2008": "12.154111",
    "2009": "24.249383",
    "2010": "25.805734",
    "2011": "20.732432",
    "2012": "22.162634",
    "2013": "22.398517",
    "2014": "35.069602",
    "2015": "47.538800",
    "2016": "45.543143",
    "2017": "51.57972630",
    "2018": "39.44644398",
    "2019": "52.29493065",
    "2020": "65.44089178",
    "2021": "71.95423200",
    "2022": "61.71335891",
    "2023": "59.77793736",
    "2024": "66.67507987",
    "2025": "79.970453",
}
AUDITED_MAIN_BOARD_COMPONENTS_RMB_100M = {
    "2005": ("23096.13", "9334.20"),
    "2006": ("71612.38", "17791.50"),
    "2007": ("269838.87", "57452.40"),
    "2008": ("97251.91", "24289.20"),
    "2009": ("184655.23", "57838.60"),
    "2010": ("179007.24", "79050.10"),
    "2011": ("148376.22", "58948.10"),
    "2012": ("158698.44", "62927.90"),
    "2013": ("151165.27", "72819.90"),
    "2014": ("243974.02", "106722.00"),
    "2015": ("295194.20", "180193.80"),
    "2016": ("284607.63", "170823.80"),
    "2017": ("331324.82", "184472.4430"),
    "2018": ("269515.01", "124949.4298"),
    "2019": ("346882.06", "176067.2465"),
    "2020": ("421830.88", "232578.0378"),
    "2021": ("463392.78", "256149.54"),
    "2022": ("405635.80", "211497.7891"),
    "2023": ("401509.81", "196269.5636"),
    "2024": ("460879.99", "205870.8087"),
    "2025": ("544575", "255129.53"),
}
OFFICIAL_DOMAINS = ("sse.com.cn", "szse.cn", "bse.cn", "csrc.gov.cn")
LIMITED_BSE_SOURCES = {
    "equity_bse_2022_2023": "finance.sina.cn",
    "equity_bse_2025": "bj.people.com.cn",
}


def host_is_official(host: str) -> bool:
    """Accept only an official host or its dot-delimited subdomain."""
    return any(host == domain or host.endswith(f".{domain}") for domain in OFFICIAL_DOMAINS)


def read_expected_values() -> list[dict[str, str]]:
    with EXPECTED_VALUES_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_module():
    """Load the production module only after asserting that it exists."""
    if not MODULE_PATH.exists():
        raise AssertionError(f"missing production module: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("prepare_lecture2_data", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EquitySubmarketDataTests(unittest.TestCase):
    def test_official_host_validation_rejects_lookalike_domains(self) -> None:
        self.assertTrue(host_is_official("sse.com.cn"))
        self.assertTrue(host_is_official("docs.static.szse.cn"))
        self.assertFalse(host_is_official("not-sse.com.cn"))
        self.assertFalse(host_is_official("sse.com.cn.example.org"))

    def test_equity_submarket_cap_is_unique_official_year_end_data(self) -> None:
        rows = load_module().read_equity_submarket_cap()

        self.assertEqual({row["submarket"] for row in rows}, EXPECTED_SUBMARKETS)
        keys = [(row["submarket"], row["period"]) for row in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(row["unit"] == "RMB trillion" for row in rows))
        self.assertTrue(
            all(row["scope"] == "year-end total market capitalization" for row in rows)
        )
        self.assertTrue(all(Decimal(row["value"]) > 0 for row in rows))
        self.assertTrue(all(row["source_id"] for row in rows))

    def test_equity_submarket_cap_has_complete_launch_aware_coverage(self) -> None:
        rows = load_module().read_equity_submarket_cap()
        observed = {
            submarket: {
                int(row["period"]) for row in rows if row["submarket"] == submarket
            }
            for submarket in EXPECTED_SUBMARKETS
        }

        self.assertEqual(observed, EXPECTED_PERIODS)
        self.assertGreaterEqual(len(observed["Main Boards"]), 5)
        self.assertGreaterEqual(min(observed["STAR Market"]), 2019)
        self.assertGreaterEqual(min(observed["ChiNext"]), 2009)
        self.assertGreaterEqual(min(observed["Beijing Stock Exchange"]), 2021)
        self.assertEqual(sum(map(len, observed.values())), 49)

    def test_main_boards_begin_in_2005_and_match_every_audited_value(self) -> None:
        rows = load_module().read_equity_submarket_cap()
        main = [row for row in rows if row["submarket"] == "Main Boards"]

        self.assertEqual(min(int(row["period"]) for row in main), 2005)
        self.assertEqual(
            [int(row["period"]) for row in main],
            sorted({int(row["period"]) for row in main}),
        )
        self.assertTrue(all(row["source_id"] for row in main))
        self.assertEqual(
            {row["period"]: row["value"] for row in main},
            AUDITED_MAIN_BOARD_VALUES,
        )

    def test_values_are_exact_rmb_100m_to_trillion_conversions(self) -> None:
        rows = load_module().read_equity_submarket_cap()
        observed = {(row["submarket"], row["period"]): row["value"] for row in rows}
        expected_rows = read_expected_values()
        expected = {
            (row["submarket"], row["period"]): row["expected_rmb_trillion"]
            for row in expected_rows
            if row["submarket"] != "Main Boards"
        }
        expected.update(
            {
                ("Main Boards", period): value
                for period, value in AUDITED_MAIN_BOARD_VALUES.items()
            }
        )

        self.assertEqual(observed, expected)
        for row in expected_rows:
            self.assertEqual(
                Decimal(row["source_rmb_100m"]) / Decimal("10000"),
                Decimal(row["expected_rmb_trillion"]),
                (row["submarket"], row["period"]),
            )

    def test_main_board_totals_equal_sse_plus_szse_components(self) -> None:
        produced = {
            row["period"]: Decimal(row["value"])
            for row in load_module().read_equity_submarket_cap()
            if row["submarket"] == "Main Boards"
        }

        self.assertEqual(len(AUDITED_MAIN_BOARD_COMPONENTS_RMB_100M), 21)
        for period, (sse_value, szse_value) in AUDITED_MAIN_BOARD_COMPONENTS_RMB_100M.items():
            component_sum = Decimal(sse_value) + Decimal(szse_value)
            self.assertEqual(
                produced[period], component_sum / Decimal("10000"), period
            )

    def test_reader_rejects_an_unexpected_schema(self) -> None:
        module = load_module()
        fixture = SCRIPT_DIR / "_temporary_bad_lecture2_data.csv"
        self.addCleanup(fixture.unlink, missing_ok=True)
        fixture.write_text("submarket,period,value\nMain Boards,2019,1\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "unexpected columns"):
            module.read_equity_submarket_cap(fixture)

    def test_manifest_audits_every_observation_with_declared_provenance(self) -> None:
        rows = load_module().read_equity_submarket_cap()
        with MANIFEST_PATH.open(encoding="utf-8", newline="") as handle:
            manifest = list(csv.DictReader(handle))
        referenced_ids = {row["source_id"] for row in rows}
        entries = [row for row in manifest if row["dataset_id"] in referenced_ids]

        self.assertEqual({row["dataset_id"] for row in entries}, referenced_ids)
        self.assertEqual(len(entries), len(referenced_ids))
        for entry in entries:
            self.assertEqual(entry["retrieved_on"], "2026-07-10")
            self.assertIn("total market capitalization", entry["definition"].lower())
            self.assertIn("RMB 100 million", entry["notes"])
            urls = entry["source_url"].split(" | ")
            self.assertTrue(urls)
            hosts = [(urlparse(url).hostname or "").lower() for url in urls]
            if entry["dataset_id"] in LIMITED_BSE_SOURCES:
                self.assertTrue(any(host_is_official(host) for host in hosts), entry["dataset_id"])
                self.assertIn(LIMITED_BSE_SOURCES[entry["dataset_id"]], hosts)
                self.assertIn("not direct official-source coverage", entry["notes"].lower())
                self.assertIn("no stable year-specific official", entry["notes"].lower())
            else:
                self.assertTrue(
                    all(host_is_official(host) for host in hosts),
                    (entry["dataset_id"], urls),
                )

        bse_2021_entries = [
            row for row in entries if row["dataset_id"] == "equity_bse_2021"
        ]
        self.assertEqual(len(bse_2021_entries), 1)
        self.assertEqual(
            bse_2021_entries[0]["source_url"],
            "https://www.bse.cn/annual/200011660.html",
        )

        main_entries = [row for row in entries if row["dataset_id"].startswith("equity_main_boards_")]
        self.assertEqual(len(main_entries), 11)
        for entry in main_entries:
            institution = entry["source_institution"].lower()
            self.assertIn("shanghai", institution)
            self.assertIn("shenzhen", institution)
            self.assertIn("combined", entry["definition"].lower())


if __name__ == "__main__":
    unittest.main()
