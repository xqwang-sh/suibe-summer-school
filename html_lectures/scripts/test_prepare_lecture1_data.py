from __future__ import annotations

import csv
import math
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from typing import get_type_hints

import scripts.prepare_lecture1_data as prepare_lecture1_data
from scripts.prepare_lecture1_data import DATASET_FILES, prepare


REQUIRED_MANIFEST_COLUMNS = {
    "dataset_id",
    "source_institution",
    "source_url",
    "retrieved_on",
    "definition",
    "frequency",
    "unit",
    "coverage",
    "notes",
}
NORMALIZED_COLUMNS = {
    "series",
    "economy",
    "period",
    "value",
    "unit",
    "source_id",
}
FOUR_SYSTEM_DATASETS = {
    "private_credit_gdp",
    "market_cap_gdp",
    "bond_market_gdp",
}
REQUIRED_ECONOMIES = {"China", "United States", "Euro area", "Japan"}
PAYMENT_SOURCE_FILE = "payment_adoption_sources.csv"


class PrepareLecture1DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.output_dir = Path(cls.temp_dir.name)
        cls.produced = prepare(cls.output_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def read_rows(self, filename: str) -> list[dict[str, str]]:
        with (self.output_dir / filename).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def read_fieldnames(self, filename: str) -> list[str]:
        with (self.output_dir / filename).open(newline="", encoding="utf-8") as handle:
            return csv.DictReader(handle).fieldnames or []

    def test_prepare_returns_every_expected_file(self) -> None:
        expected = {
            self.output_dir / "source_manifest.csv",
            self.output_dir / PAYMENT_SOURCE_FILE,
        }
        expected.update(self.output_dir / filename for filename in DATASET_FILES.values())
        self.assertEqual(set(self.produced), expected)
        self.assertTrue(all(path.is_file() for path in expected))

    def test_payment_sources_map_every_observation_period_to_its_report(self) -> None:
        rows = self.read_rows(PAYMENT_SOURCE_FILE)
        expected = {
            "2007": ("23rd Statistical Report", "https://www3.cnnic.cn/NMediaFile/2022/0830/MAIN1661848328683YK36NWDGG4.pdf"),
            "2008": ("23rd Statistical Report", "https://www3.cnnic.cn/NMediaFile/2022/0830/MAIN1661848328683YK36NWDGG4.pdf"),
            "2009": ("25th Statistical Report", "https://www.cnnic.cn/NMediaFile/old_attach/P020120612484949500779.pdf"),
            "2010": ("27th Statistical Report", "https://www.cac.gov.cn/files/pdf/hlwtjbg/hlwlfzzkdctjbg027.pdf"),
            "2011": ("29th Statistical Report", "https://www.cnnic.cn/n4/2022/0401/c88-803.html"),
            "2012": ("32nd Statistical Report", "https://www.cnnic.cn/NMediaFile/old_attach/P020130717505343100851.pdf"),
            "2013": ("35th Statistical Report", "https://www3.cnnic.cn/NMediaFile/old_attach/P020150203548852631921.pdf"),
            "2014": ("35th Statistical Report", "https://www3.cnnic.cn/NMediaFile/old_attach/P020150203548852631921.pdf"),
            "2015": ("37th Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/201604/P020160419390562421055.pdf"),
            "2016": ("39th Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/201706/P020170608523740585924.pdf"),
            "2017": ("41st Statistical Report", "https://www.cac.gov.cn/files/pdf/cnnic/CNNIC41.pdf"),
            "2018": ("43rd Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/201911/P020191112538996067898.pdf"),
            "2020": ("51st Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf"),
            "2021": ("51st Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf"),
            "2022": ("51st Statistical Report", "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf"),
            "2023": ("55th Statistical Report", "https://www2.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf"),
            "2024": ("55th Statistical Report", "https://www2.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf"),
        }
        actual = {row["period"]: (row["report"], row["source_url"]) for row in rows}
        self.assertEqual(len(rows), 17)
        self.assertEqual(actual, expected)
        self.assertNotIn("2019", actual)

        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        manifest_urls = set(manifest["payment_adoption"]["source_url"].split(" ; "))
        self.assertTrue({row["source_url"] for row in rows}.issubset(manifest_urls))

    def test_checked_in_payment_sources_match_fresh_generation(self) -> None:
        checked_in = Path(__file__).resolve().parents[1] / "data" / "lecture1"
        self.assertEqual(
            (checked_in / PAYMENT_SOURCE_FILE).read_bytes(),
            (self.output_dir / PAYMENT_SOURCE_FILE).read_bytes(),
        )

    def test_source_manifest_contract_is_complete(self) -> None:
        rows = self.read_rows("source_manifest.csv")
        self.assertEqual({row["dataset_id"] for row in rows}, set(DATASET_FILES))
        for row in rows:
            self.assertTrue(REQUIRED_MANIFEST_COLUMNS.issubset(row))
            for column in REQUIRED_MANIFEST_COLUMNS:
                self.assertTrue(row[column].strip(), f"{row['dataset_id']} has empty {column}")

    def test_normalized_files_are_finite_unique_and_well_formed(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        for dataset_id, filename in DATASET_FILES.items():
            rows = self.read_rows(filename)
            self.assertEqual(set(self.read_fieldnames(filename)), NORMALIZED_COLUMNS)
            if not rows:
                self.assertIn("coverage_unavailable", manifest[dataset_id]["notes"])
                continue
            self.assertEqual(set(rows[0]), NORMALIZED_COLUMNS)
            keys: set[tuple[str, str, str]] = set()
            for row in rows:
                self.assertTrue(all(row[column].strip() for column in NORMALIZED_COLUMNS))
                self.assertTrue(math.isfinite(float(row["value"])))
                key = (row["series"], row["economy"], row["period"])
                self.assertNotIn(key, keys, f"duplicate observation in {filename}: {key}")
                keys.add(key)
                self.assertIn(row["source_id"], manifest)
                self.assertEqual(row["source_id"], dataset_id)

    def test_units_are_consistent_within_each_series(self) -> None:
        for filename in DATASET_FILES.values():
            units: dict[tuple[str, str], set[str]] = defaultdict(set)
            for row in self.read_rows(filename):
                units[(row["series"], row["economy"])].add(row["unit"])
            self.assertTrue(all(len(values) == 1 for values in units.values()), filename)

    def test_four_system_datasets_have_required_economies_or_declared_exception(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        for dataset_id in FOUR_SYSTEM_DATASETS:
            rows = self.read_rows(DATASET_FILES[dataset_id])
            economies = {row["economy"] for row in rows}
            if not rows:
                self.assertIn("coverage_unavailable", manifest[dataset_id]["notes"])
                continue
            if dataset_id == "market_cap_gdp" and "Euro area" not in economies:
                self.assertEqual(economies, REQUIRED_ECONOMIES - {"Euro area"})
                self.assertIn("euro_area_unavailable", manifest[dataset_id]["notes"])
            else:
                self.assertEqual(economies, REQUIRED_ECONOMIES)

    def test_private_credit_manifest_names_all_four_fred_series(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        row = manifest["private_credit_gdp"]
        for series_id in {"QCNPAM770A", "QUSPAM770A", "QXMPAM770A", "QJPPAM770A"}:
            self.assertIn(f"https://fred.stlouisfed.org/series/{series_id}", row["source_url"])
            self.assertIn(series_id, row["notes"])

    def test_market_cap_manifest_excludes_incomparable_euro_area_aggregate(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        notes = manifest["market_cap_gdp"]["notes"]
        self.assertIn("same-basis Euro area aggregate unavailable and excluded", notes)
        self.assertNotIn("separate", notes.lower())

    def test_payment_adoption_matches_verified_cnnic_year_end_series(self) -> None:
        rows = self.read_rows(DATASET_FILES["payment_adoption"])
        by_period = defaultdict(dict)
        for row in rows:
            by_period[row["period"]][row["series"]] = float(row["value"])
        expected = {
            year: {
                "Online payment users": users,
                "Online payment utilization rate": rate,
            }
            for year, users, rate in (
                ("2007", 33.00, 15.8), ("2008", 52.00, 17.6),
                ("2009", 94.06, 24.5), ("2010", 137.19, 30.0),
                ("2011", 166.76, 32.5), ("2012", 220.65, 39.1),
                ("2013", 260.20, 42.1), ("2014", 304.31, 46.9),
                ("2015", 416.18, 60.5), ("2016", 474.50, 64.9),
                ("2017", 531.10, 68.8), ("2018", 600.40, 72.5),
                ("2020", 854.34, 86.4), ("2021", 903.63, 87.6),
                ("2022", 911.44, 85.4), ("2023", 953.86, 87.3),
                ("2024", 1028.91, 92.8),
            )
        }
        self.assertEqual(dict(by_period), expected)
        self.assertNotIn("2019", by_period)

    def test_payment_manifest_declares_scope_gap_and_noncausal_boundary(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        payment = manifest["payment_adoption"]
        source_urls = (
            "https://www3.cnnic.cn/NMediaFile/2022/0830/MAIN1661848328683YK36NWDGG4.pdf",
            "https://www.cnnic.cn/NMediaFile/old_attach/P020120612484949500779.pdf",
            "https://www.cac.gov.cn/files/pdf/hlwtjbg/hlwlfzzkdctjbg027.pdf",
            "https://www.cnnic.cn/n4/2022/0401/c88-803.html",
            "https://www.cnnic.cn/NMediaFile/old_attach/P020130717505343100851.pdf",
            "https://www3.cnnic.cn/NMediaFile/old_attach/P020150203548852631921.pdf",
            "https://www.cnnic.com.cn/IDR/ReportDownloads/201604/P020160419390562421055.pdf",
            "https://www.cnnic.com.cn/IDR/ReportDownloads/201706/P020170608523740585924.pdf",
            "https://www.cac.gov.cn/files/pdf/cnnic/CNNIC41.pdf",
            "https://www.cnnic.com.cn/IDR/ReportDownloads/201911/P020191112538996067898.pdf",
            "https://www.cnnic.com.cn/IDR/ReportDownloads/202307/P020230829505026163347.pdf",
            "https://www2.cnnic.cn/NMediaFile/2025/0428/MAIN17458061595875K4FP1NEUO.pdf",
        )
        expected = {
            "source_institution": "China Internet Network Information Center (CNNIC)",
            "source_url": " ; ".join(source_urls),
            "definition": "Users of online/network payment and their share of internet users",
            "frequency": "annual year-end",
            "unit": "million users; percent of internet users",
            "coverage": "China, year-end 2007-2024; 2019 unavailable",
            "notes": (
                "Official CNNIC report observations; terminology changes from online payment to "
                "network payment. The measure includes bank and third-party online payment, is not "
                "a causal estimate of third-party payment, and uses no interpolation for missing 2019. "
                "Period-level report provenance: payment_adoption_sources.csv."
            ),
        }
        self.assertEqual({key: payment[key] for key in expected}, expected)

    def test_payment_constant_has_explicit_nested_tuple_annotation(self) -> None:
        self.assertEqual(
            get_type_hints(prepare_lecture1_data).get("CNNIC_PAYMENT_VALUES"),
            tuple[tuple[str, float, float], ...],
        )

    def test_checked_in_payment_outputs_match_fresh_generation(self) -> None:
        checked_in = Path(__file__).resolve().parents[1] / "data" / "lecture1"
        generated_payment = self.output_dir / DATASET_FILES["payment_adoption"]
        checked_in_payment = checked_in / DATASET_FILES["payment_adoption"]
        self.assertEqual(checked_in_payment.read_bytes(), generated_payment.read_bytes())

        with (checked_in / "source_manifest.csv").open(newline="", encoding="utf-8") as handle:
            checked_in_manifest = {
                row["dataset_id"]: row for row in csv.DictReader(handle)
            }
        generated_manifest = {
            row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")
        }
        self.assertEqual(
            checked_in_manifest["payment_adoption"],
            generated_manifest["payment_adoption"],
        )

    def test_nominal_gdp_is_exact_2025_value(self) -> None:
        rows = self.read_rows("nominal_gdp.csv")
        self.assertEqual(
            [(row["period"], float(row["value"]), row["unit"]) for row in rows],
            [("2025", 140.1879, "RMB trillion")],
        )

    def test_deposits_have_two_exact_november_2025_stock_rows(self) -> None:
        rows = self.read_rows("deposits_by_holder.csv")
        values = {row["series"]: float(row["value"]) for row in rows}
        self.assertEqual(values, {
            "Household RMB deposits": 163.3084,
            "Non-financial enterprise RMB deposits": 79.3387,
        })
        self.assertEqual({row["period"] for row in rows}, {"2025-11"})
        self.assertEqual({row["unit"] for row in rows}, {"RMB trillion"})

    def test_deposit_manifest_declares_stock_benchmark_not_savings_rate(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        row = manifest["deposits_by_holder"]
        self.assertEqual(row["frequency"], "monthly")
        self.assertEqual(row["unit"], "RMB trillion")
        self.assertIn("2025-11", row["coverage"])
        self.assertIn("stock-to-annual-GDP benchmark; not a savings rate", row["notes"])
        self.assertIn(
            "https://www.pbc.gov.cn/diaochatongjisi/attachDir/2025/12/"
            "2025121517273312027.pdf",
            row["source_url"],
        )

    def test_tsf_total_contains_exact_flow_and_stock(self) -> None:
        rows = self.read_rows("tsf_total.csv")
        values = {row["series"]: float(row["value"]) for row in rows}
        self.assertEqual(values, {
            "AFRE annual flow": 35.6,
            "AFRE year-end stock": 442.1,
        })
        self.assertEqual({row["period"] for row in rows}, {"2025"})
        self.assertEqual({row["unit"] for row in rows}, {"RMB trillion"})

    def test_gdp_and_tsf_manifest_rows_declare_comparability(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        gdp = manifest["nominal_gdp"]
        self.assertIn("stats.gov.cn", gdp["source_url"])
        self.assertIn("2025", gdp["coverage"])
        tsf = manifest["tsf_total"]
        self.assertIn("pbc.gov.cn", tsf["source_url"])
        self.assertIn("flow / annual GDP", tsf["notes"])
        self.assertIn("stock / annual-GDP benchmark", tsf["notes"])

    def test_bank_efficiency_has_no_duplicate_country_years(self) -> None:
        rows = self.read_rows(DATASET_FILES["bank_efficiency"])
        self.assertTrue(rows)
        self.assertEqual({row["series"] for row in rows}, {"Bank nonperforming loans to total gross loans"})
        self.assertEqual({row["unit"] for row in rows}, {"percent"})
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        row = manifest["bank_efficiency"]
        self.assertIn("docId=1251267", row["source_url"])
        self.assertIn("docId=1259732", row["source_url"])
        self.assertIn("sources/nfra_supervisory_stats_2025q4.pdf", row["notes"])
        self.assertIn("sources/nfra_supervisory_stats_2026q1.pdf", row["notes"])

    def test_unavailable_datasets_are_header_only(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        for dataset_id in {"bank_credit_allocation", "bond_market_gdp"}:
            rows = self.read_rows(DATASET_FILES[dataset_id])
            self.assertEqual(rows, [])
            self.assertIn("coverage_unavailable", manifest[dataset_id]["notes"])

    def test_financial_sector_assets_are_only_exact_numeric_observations(self) -> None:
        rows = self.read_rows(DATASET_FILES["financial_sector_assets"])
        self.assertTrue(rows)
        self.assertNotIn("availability flag", " ".join(row["unit"] for row in rows))
        self.assertEqual({row["period"] for row in rows}, {"2025Q4", "2026Q1"})

    def test_single_period_tsf_limitations_are_declared(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        for dataset_id in {"tsf_total", "tsf_mix"}:
            periods = {row["period"] for row in self.read_rows(DATASET_FILES[dataset_id])}
            self.assertEqual(periods, {"2025"})
            self.assertIn("single_period_only", manifest[dataset_id]["notes"])
            self.assertIn("time_series_withheld", manifest[dataset_id]["notes"])

    def test_tsf_mix_manifest_describes_final_slide_23_evidence_limit(self) -> None:
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        notes = manifest["tsf_mix"]["notes"]
        self.assertIn("final Slide 23 single-period composition", notes)
        self.assertIn("evidence limitation", notes)
        self.assertNotIn("planned Slide 25 mix time series", notes)

    def test_literal_source_values_link_to_their_manifest_rows(self) -> None:
        manifest_ids = {row["dataset_id"] for row in self.read_rows("source_manifest.csv")}
        for dataset_id in {"payment_adoption", "tsf_total", "tsf_mix"}:
            rows = self.read_rows(DATASET_FILES[dataset_id])
            self.assertTrue(rows)
            self.assertEqual({row["source_id"] for row in rows}, {dataset_id})
            self.assertIn(dataset_id, manifest_ids)

    def test_afre_channels_cover_four_exhaustive_layers_from_2002_to_2021(self) -> None:
        rows = self.read_rows("afre_channels.csv")
        self.assertEqual({row["period"] for row in rows}, {str(y) for y in range(2002, 2022)})
        self.assertEqual({row["series"] for row in rows}, {
            "Bank loans",
            "Off-balance-sheet financing",
            "Market-based direct financing",
            "Other forms of financing",
        })
        self.assertEqual({row["unit"] for row in rows}, {"percent of GDP"})
        self.assertEqual(len(rows), 80)
        totals = defaultdict(float)
        for row in rows:
            totals[row["period"]] += float(row["value"])
        self.assertAlmostEqual(totals["2008"], 118.3, places=1)
        self.assertAlmostEqual(totals["2021"], 273.3, delta=0.2)
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        self.assertIn("digitized", manifest["afre_channels"]["notes"].lower())

    def test_sector_leverage_matches_public_brookings_figure_5_workbook(self) -> None:
        rows = self.read_rows("sector_leverage.csv")
        self.assertEqual({row["period"] for row in rows}, {str(y) for y in range(2000, 2024)})
        self.assertEqual({row["series"] for row in rows}, {
            "Household",
            "Nonfinancial corporations",
            "Central government",
            "Local government",
        })
        values = {(row["series"], row["period"]): float(row["value"]) for row in rows}
        self.assertEqual(values[("Household", "2000")], 10.0)
        self.assertEqual(values[("Nonfinancial corporations", "2023")], 168.0)
        self.assertEqual(values[("Local government", "2023")], 32.0)

    def test_broad_local_debt_is_vector_digitized_for_2015_to_2022(self) -> None:
        rows = self.read_rows("broad_local_debt.csv")
        self.assertEqual({row["period"] for row in rows}, {str(y) for y in range(2015, 2023)})
        self.assertEqual({row["series"] for row in rows}, {"Broad local government debt"})
        values = {row["period"]: float(row["value"]) for row in rows}
        self.assertAlmostEqual(values["2015"], 42.97, places=2)
        self.assertAlmostEqual(values["2022"], 68.47, places=2)
        manifest = {row["dataset_id"]: row for row in self.read_rows("source_manifest.csv")}
        self.assertIn("official local government debt and LGFV liabilities", manifest["broad_local_debt"]["definition"])
        self.assertIn("digitized", manifest["broad_local_debt"]["notes"].lower())


if __name__ == "__main__":
    unittest.main()
