from __future__ import annotations

import csv
import hashlib
import importlib.util
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

from scripts.verify_decks import L1_TITLES


MODULE_PATH = Path(__file__).with_name("make_lecture1_figures.py")
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "lecture1"

EXPECTED = {
    "payment_inclusion.svg",
    "private_credit_gdp_four_systems.svg",
    "deposits_relative_to_gdp.svg",
    "afre_relative_to_gdp.svg",
    "tsf_composition.svg",
    "market_cap_gdp_available_systems.svg",
    "china_banking_insurance_assets_two_quarters.svg",
    "afre_channels.svg",
    "sector_leverage.svg",
    "broad_local_debt.svg",
}

WITHHELD = {
    "deposits_timeseries.svg",
    "credit_allocation.svg",
    "tsf_total_timeseries.svg",
    "tsf_mix_timeseries.svg",
    "bond_market_gdp_four_systems.svg",
    "market_cap_gdp_four_systems.svg",
    "financial_structure_small_multiples.svg",
}


def load_module():
    spec = importlib.util.spec_from_file_location("make_lecture1_figures", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hash_dir(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.glob("*.svg"))
    }


def copy_data(destination: Path) -> Path:
    target = destination / "lecture1"
    shutil.copytree(DATA_DIR, target)
    return target


def rewrite_rows(path: Path, transform) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        assert fieldnames is not None
        rows = transform(list(reader))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class LectureOneFigureContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()

    def generate(self, output_dir: Path, data_dir: Path = DATA_DIR) -> None:
        self.module.main(output_dir, data_dir=data_dir)

    def test_production_selector_is_the_inventory_source_of_truth(self) -> None:
        jobs = self.module.determine_figure_jobs(DATA_DIR)
        self.assertEqual(set(jobs), EXPECTED)
        self.assertTrue(all(callable(job.render) for job in jobs.values()))
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.generate(output_dir)
            self.assertEqual({path.name for path in output_dir.glob("*.svg")}, set(jobs))
            self.assertTrue(WITHHELD.isdisjoint(jobs))

    def test_removing_euro_area_private_credit_withholds_four_system_figure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "private_credit_gdp.csv",
                lambda rows: [row for row in rows if row["economy"] != "Euro area"],
            )
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("private_credit_gdp_four_systems.svg", jobs)
            output_dir = Path(directory) / "out"
            self.generate(output_dir, data_dir)
            self.assertFalse((output_dir / "private_credit_gdp_four_systems.svg").exists())

    def test_reducing_asset_data_to_one_period_withholds_two_quarter_figure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "financial_sector_assets.csv",
                lambda rows: [row for row in rows if row["period"] == "2026Q1"],
            )
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("china_banking_insurance_assets_two_quarters.svg", jobs)

    def test_adding_third_asset_period_withholds_two_quarter_figure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))

            def add_q2(rows):
                additions = [dict(row, period="2026Q2") for row in rows if row["period"] == "2026Q1"]
                return rows + additions

            rewrite_rows(data_dir / "financial_sector_assets.csv", add_q2)
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("china_banking_insurance_assets_two_quarters.svg", jobs)

    def test_unmatched_payment_period_withholds_payment_figure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))

            def add_users_only(rows):
                users = next(row for row in rows if row["series"] == "Online payment users")
                return rows + [dict(users, period="2025", value="1040.00")]

            rewrite_rows(data_dir / "payment_adoption.csv", add_users_only)
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("payment_inclusion.svg", jobs)

    def test_payment_figure_requires_exact_audited_periods(self) -> None:
        required_periods = (
            {str(year) for year in range(2007, 2019)}
            | {str(year) for year in range(2020, 2025)}
        )
        rows = self.module._read("payment_adoption", DATA_DIR)
        for series in {row["series"] for row in rows}:
            self.assertEqual(
                {row["period"] for row in rows if row["series"] == series},
                required_periods,
            )

        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "payment_adoption.csv",
                lambda copied_rows: [
                    row for row in copied_rows
                    if not (row["series"] == "Online payment users" and row["period"] == "2007")
                ],
            )
            self.assertNotIn("payment_inclusion.svg", self.module.determine_figure_jobs(data_dir))

    def test_payment_figure_carries_long_run_milestones_and_gap_note(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.generate(output_dir)
            svg = (output_dir / "payment_inclusion.svg").read_text(encoding="utf-8")
            for text in ("2007", "2014", "2018", "2020", "2024", "33", "1,028.91", "92.8%"):
                self.assertIn(text, svg)
            self.assertIn("2019: no year-end observation", svg)
            self.assertIn("Online/network payment", svg)

    def test_payment_renderer_plots_two_disconnected_segments_per_series(self) -> None:
        expected_segments = [
            tuple(range(2007, 2019)),
            tuple(range(2020, 2025)),
        ]
        recorded_calls: list[tuple[str | None, tuple[int, ...]]] = []
        original_plot = self.module.mpl.axes.Axes.plot

        def record_plot(axis, years, values, *args, **kwargs):
            recorded_calls.append((kwargs.get("color"), tuple(years)))
            return original_plot(axis, years, values, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(self.module.mpl.axes.Axes, "plot", new=record_plot):
                self.module._payment_inclusion(
                    Path(directory) / "payment_inclusion.svg",
                    "CNNIC",
                    DATA_DIR,
                )

        for color in (self.module.BLUE, self.module.BRICK):
            color_segments = [years for call_color, years in recorded_calls if call_color == color]
            self.assertEqual(color_segments, expected_segments)
            self.assertTrue(all(not ({2018, 2020} <= set(years)) for years in color_segments))

    def test_breaking_tsf_exhaustiveness_withholds_composition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))

            def break_total(rows):
                rows[0]["value"] = "59.7"
                return rows

            rewrite_rows(data_dir / "tsf_mix.csv", break_total)
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("tsf_composition.svg", jobs)

    def test_gates_require_common_periods_and_exact_market_economies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))

            def disjoin_japan(rows):
                for row in rows:
                    if row["economy"] == "Japan":
                        row["period"] = f"J-{row['period']}"
                return rows

            rewrite_rows(data_dir / "private_credit_gdp.csv", disjoin_japan)
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("private_credit_gdp_four_systems.svg", jobs)

            rewrite_rows(
                data_dir / "market_cap_gdp.csv",
                lambda rows: rows + [dict(rows[0], economy="Euro area")],
            )
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("market_cap_gdp_available_systems.svg", jobs)
            self.assertNotIn("market_cap_gdp_four_systems.svg", jobs)

    def test_every_svg_uses_fixed_canvas_and_contains_no_slide_title(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.generate(output_dir)
            for path in output_dir.glob("*.svg"):
                root = ET.parse(path).getroot()
                self.assertEqual(
                    (root.get("width"), root.get("height"), root.get("viewBox")),
                    ("864pt", "486pt", "0 0 864 486"),
                    path.name,
                )
                text = path.read_text(encoding="utf-8")
                for title in L1_TITLES:
                    self.assertNotIn(title, text, f"slide title leaked into {path.name}")

    def test_figures_carry_direct_labels_units_periods_and_sources(self) -> None:
        expected_labels = {
            "payment_inclusion.svg": (
                "China", "2024", "1,028.91", "92.8%", "Million users",
                "Percent of internet users", "CNNIC",
            ),
            "private_credit_gdp_four_systems.svg": (
                "China", "United States", "Euro area", "Japan", "2025",
                "Percent of GDP", "BIS", "FRED",
            ),
            "deposits_relative_to_gdp.svg": (
                "Household RMB deposits", "Non-financial enterprise RMB deposits",
                "2025-11", "RMB trillion", "163.3084", "79.3387",
                "116.5%", "56.6%", "stock / annual GDP", "PBOC", "NBS",
            ),
            "afre_relative_to_gdp.svg": (
                "AFRE annual flow", "AFRE year-end stock", "2025",
                "35.6", "442.1", "25.4%", "315.4%", "flow / annual GDP",
                "stock / annual GDP", "scale benchmark", "PBOC", "NBS",
            ),
            "market_cap_gdp_available_systems.svg": (
                "Available economies: China · United States · Japan", "2025",
                "Percent of GDP", "World Bank", "WDI",
            ),
            "china_banking_insurance_assets_two_quarters.svg": (
                "China", "Banking institutions assets",
                "Insurance and insurance asset-management assets",
                "NFRA observations: 2025Q4 and 2026Q1", "Separate panel scales",
                "RMB trillion", "NFRA",
            ),
            "afre_channels.svg": (
                "Bank loans", "Off-balance-sheet financing",
                "Market-based direct financing", "Other forms of financing",
                "2002", "2021", "Percent of GDP", "digitized", "He", "Wei",
            ),
            "sector_leverage.svg": (
                "Household", "Nonfinancial corporations", "Central government",
                "Local government", "2000", "2023", "Percent of GDP",
                "LGFV debt", "Chang", "Wang", "Xiong",
            ),
            "broad_local_debt.svg": (
                "Broad local government debt", "2015", "2022", "42.97%",
                "68.47%", "official local debt + LGFV liabilities", "digitized",
                "Chang", "Wang", "Xiong",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.generate(output_dir)
            for name, labels in expected_labels.items():
                text = (output_dir / name).read_text(encoding="utf-8")
                for label in labels:
                    self.assertIn(label, text, f"{label!r} absent from {name}")
                self.assertIn("Source:", text, name)

    def test_tsf_segments_directly_label_every_category_and_percentage(self) -> None:
        expected = (
            "RMB loans to real economy · 60.7%",
            "Government bonds · 21.5%",
            "Corporate bonds · 7.7%",
            "Domestic equity of non-financial enterprises · 2.8%",
            "Other components · 7.3%",
        )
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            self.generate(output_dir)
            text = (output_dir / "tsf_composition.svg").read_text(encoding="utf-8")
            for direct_label in expected:
                self.assertIn(direct_label, text)

    def test_tsf_display_period_is_derived_from_validated_common_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))

            def move_to_2026(rows):
                return [dict(row, period="2026") for row in rows]

            rewrite_rows(data_dir / "tsf_mix.csv", move_to_2026)
            output_dir = Path(directory) / "out"
            self.generate(output_dir, data_dir)
            text = (output_dir / "tsf_composition.svg").read_text(encoding="utf-8")
            self.assertIn("China · 2026", text)
            self.assertNotIn("China · 2025", text)

    def test_bank_efficiency_job_is_removed(self) -> None:
        self.assertNotIn("bank_efficiency.svg", self.module.OWNED_FILENAMES)
        self.assertNotIn("bank_efficiency.svg", self.module.determine_figure_jobs(DATA_DIR))
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            legacy = output_dir / "bank_efficiency.svg"
            legacy.write_text("legacy", encoding="utf-8")
            self.generate(output_dir)
            self.assertFalse(legacy.exists())

    def test_deposit_and_afre_jobs_reject_duplicate_or_missing_exact_series(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "deposits_by_holder.csv",
                lambda rows: rows + [dict(rows[0])],
            )
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("deposits_relative_to_gdp.svg", jobs)

        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "tsf_total.csv",
                lambda rows: [row for row in rows if row["series"] != "AFRE annual flow"],
            )
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("afre_relative_to_gdp.svg", jobs)

    def test_deposit_job_requires_exact_november_2025_observation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "deposits_by_holder.csv",
                lambda rows: [dict(row, period="2025-10") for row in rows],
            )
            jobs = self.module.determine_figure_jobs(data_dir)
            self.assertNotIn("deposits_relative_to_gdp.svg", jobs)

    def test_ratio_labels_are_derived_from_csv_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = copy_data(Path(directory))
            rewrite_rows(
                data_dir / "deposits_by_holder.csv",
                lambda rows: [dict(row, value="140.1879") for row in rows],
            )
            rewrite_rows(
                data_dir / "tsf_total.csv",
                lambda rows: [dict(row, value="140.1879") for row in rows],
            )
            output_dir = Path(directory) / "out"
            self.generate(output_dir, data_dir)
            deposits = (output_dir / "deposits_relative_to_gdp.svg").read_text(encoding="utf-8")
            afre = (output_dir / "afre_relative_to_gdp.svg").read_text(encoding="utf-8")
            self.assertGreaterEqual(deposits.count("100.0%"), 2)
            self.assertGreaterEqual(afre.count("100.0%"), 2)
            self.assertNotIn("116.5%", deposits)
            self.assertNotIn("315.4%", afre)

    def test_main_preserves_unknown_svg_and_removes_known_legacy_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            foreign = output_dir / "caller_owned.svg"
            legacy = output_dir / "financial_structure_small_multiples.svg"
            foreign.write_text("caller", encoding="utf-8")
            legacy.write_text("legacy", encoding="utf-8")
            self.generate(output_dir)
            self.assertEqual(foreign.read_text(encoding="utf-8"), "caller")
            self.assertFalse(legacy.exists())

    def test_public_primitives_and_editorial_palette(self) -> None:
        for name, color in {
            "INK": "#172132", "PAPER": "#F7F3EA", "BRICK": "#C9583E",
            "BLUE": "#4B718A", "GOLD": "#C59A45", "MUTED": "#6F746F",
        }.items():
            self.assertEqual(getattr(self.module, name), color)
        for name in ("save_svg", "line_chart", "stacked_share", "dot_plot", "two_period_bars"):
            self.assertTrue(callable(getattr(self.module, name)))

    def test_generation_is_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.generate(Path(first))
            self.generate(Path(second))
            self.assertEqual(hash_dir(Path(first)), hash_dir(Path(second)))


if __name__ == "__main__":
    unittest.main()
