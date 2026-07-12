from __future__ import annotations

import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("make_figures.py")
EXPECTED_FILES = {
    "payment_adoption.svg": ("1,028.91", "92.8%"),
    "tsf_composition_2025.svg": ("60.7%", "21.5%"),
    "bond_composition_2025.svg": ("53.7", "20.7"),
    "bond_venues_2025.svg": ("171.7", "26.6"),
    "interbank_investors.svg": ("56%", "29%"),
    "bond_market_by_venue_timeseries.svg": ("2015", "2024", "155.8", "21.2"),
    "stock_connect_adt.svg": ("212.4", "Shenzhen Connect"),
    "private_funds_2025.svg": ("11.19", "80,390 funds"),
    "l2_market_cap_gdp_timeseries.svg": ("China", "United States", "Japan", "2025"),
    "l2_market_cap_gdp_latest.svg": ("79.5%", "224.0%", "171.6%", "2025"),
    "l2_equity_submarkets_market_cap.svg": (
        "Main Boards",
        "STAR Market",
        "ChiNext",
        "Beijing Stock Exchange",
        "RMB trillion",
    ),
    "l2_stock_connect_adt.svg": (
        "Northbound",
        "Southbound",
        "average daily turnover",
    ),
}

EXPECTED_SOURCE_URLS = {
    "payment_adoption.svg": "https://www.cnnic.com.cn/IDR/ReportDownloads/202505/P020250514564119130448.pdf",
    "tsf_composition_2025.svg": "https://jrj.sh.gov.cn/ZXYW178/20260116/88e3368ecfee4e639ae9aa8dd93729c3.html",
    "bond_composition_2025.svg": "https://cif.mofcom.gov.cn/cif/html/upload/20251201140144995_2025%E5%B9%B410%E6%9C%88%E4%BB%BD%E9%87%91%E8%9E%8D%E5%B8%82%E5%9C%BA%E8%BF%90%E8%A1%8C%E6%83%85%E5%86%B5.pdf",
    "bond_venues_2025.svg": "https://cif.mofcom.gov.cn/cif/html/upload/20251201140144995_2025%E5%B9%B410%E6%9C%88%E4%BB%BD%E9%87%91%E8%9E%8D%E5%B8%82%E5%9C%BA%E8%BF%90%E8%A1%8C%E6%83%85%E5%86%B5.pdf",
    "interbank_investors.svg": "https://www.nafmii.org.cn/englishnew/overseasparticipation/pandabond/resources/202504/P020250423396158840864.pdf",
    "bond_market_by_venue_timeseries.svg": "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/2025122616592613805/2025122616590775273.pdf",
    "stock_connect_adt.svg": "https://www.hkexgroup.com/Media-Centre/Insight/Insight/2026/HKEX-Insight/Stock-Connect-2025-Review?sc_lang=en",
    "private_funds_2025.svg": "https://www.amac.org.cn/sjtj/tjbg/smjj/202601/P020260126611919011850.pdf",
    "l2_market_cap_gdp_timeseries.svg": "https://api.worldbank.org/v2/country/CHN;USA;JPN/indicator/CM.MKT.LCAP.GD.ZS",
    "l2_market_cap_gdp_latest.svg": "https://api.worldbank.org/v2/country/CHN;USA;JPN/indicator/CM.MKT.LCAP.GD.ZS",
    "l2_equity_submarkets_market_cap.svg": "data/lecture2/source_manifest.csv",
    "l2_stock_connect_adt.svg": "https://www.hkexgroup.com/Media-Centre/Insight/Insight/2026/HKEX-Insight/Stock-Connect-2025-Review?sc_lang=en",
}


def load_module():
    spec = importlib.util.spec_from_file_location("make_figures", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FigureGeneratorContractTest(unittest.TestCase):
    def test_all_svgs_keep_the_same_12_by_6_75_canvas(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            module.main(output_dir)
            for name in EXPECTED_FILES:
                root = ET.parse(output_dir / name).getroot()
                canvas = (root.get("width"), root.get("height"), root.get("viewBox"))
                self.assertEqual(
                    canvas,
                    ("864pt", "486pt", "0 0 864 486"),
                    f"content-dependent canvas for {name}: {canvas}",
                )

    def test_stacked_bars_label_every_category_and_value(self) -> None:
        module = load_module()
        expected = {
            "tsf_composition_2025.svg": (
                "RMB loans to real economy", "60.7%",
                "Government bonds", "21.5%",
                "Corporate bonds", "7.7%",
                "Domestic equity of non-financial firms", "2.8%",
                "Other components", "7.3%",
            ),
            "interbank_investors.svg": (
                "Deposit-taking financial institutions", "56%",
                "Asset-management products", "29%",
                "Non-bank financial institutions", "9%",
                "Others", "6%",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            module.main(output_dir)
            for name, labels in expected.items():
                text = (output_dir / name).read_text(encoding="utf-8")
                for label in labels:
                    self.assertIn(label, text, f"{label!r} absent from {name}")

    def test_source_attributions_match_comments_baseline(self) -> None:
        module = load_module()
        self.assertEqual(module.SOURCE_URLS, EXPECTED_SOURCE_URLS)

    def test_equity_submarket_figure_discloses_limited_bse_provenance(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "l2_equity_submarkets_market_cap.svg"
            module.equity_submarkets_market_cap(output)
            text = output.read_text(encoding="utf-8")

        self.assertIn("SSE/SZSE/CSRC official year-end statistics", text)
        self.assertIn(
            "BSE 2022–23 &amp; 2025: archive + year-specific secondary corroboration",
            text,
        )
        self.assertNotIn("audited exchange/CSRC observations", text)

    def test_lecture2_figures_cover_audited_history_and_stock_connect_series(self) -> None:
        module = load_module()
        main_board_years = [
            int(row["period"])
            for row in module.read_equity_submarket_cap()
            if row["submarket"] == "Main Boards"
        ]
        earliest_main_board_year = min(main_board_years)
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            module.main(output_dir)
            outputs = {
                path.name: path.read_text(encoding="utf-8")
                for path in output_dir.iterdir()
            }

        equity_svg = outputs["l2_equity_submarkets_market_cap.svg"]
        self.assertIn(str(earliest_main_board_year), equity_svg)
        self.assertNotIn("interpolated", equity_svg.lower())
        self.assertNotIn(
            "China's equity submarkets grew on very different scales",
            equity_svg,
        )

        connect_svg = outputs["l2_stock_connect_adt.svg"]
        self.assertIn("Northbound", connect_svg)
        self.assertIn("Southbound", connect_svg)
        self.assertIn("average daily turnover", connect_svg.lower())
        self.assertIn("RMB bn", connect_svg)
        self.assertIn("HK$ bn", connect_svg)
        self.assertIn("Source: HKEX", connect_svg)
        self.assertIn("2014 covers the post-launch period from 17 Nov", connect_svg)
        self.assertNotIn("Stock Connect daily turnover rose sharply over time", connect_svg)

    def test_generated_svgs_are_byte_deterministic_across_fresh_runs(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            module.main(Path(first))
            module.main(Path(second))
            for name in EXPECTED_FILES:
                self.assertEqual(
                    (Path(first) / name).read_bytes(),
                    (Path(second) / name).read_bytes(),
                    f"non-deterministic SVG bytes for {name}",
                )

    def test_public_primitives_and_palette(self) -> None:
        module = load_module()
        self.assertEqual(module.INK, "#172132")
        self.assertEqual(module.PAPER, "#F7F3EA")
        self.assertEqual(module.BRICK, "#C9583E")
        self.assertEqual(module.BLUE, "#4B718A")
        self.assertEqual(module.GOLD, "#C59A45")
        self.assertEqual(module.MUTED, "#6F746F")
        for name in ("save_svg", "style_axis", "horizontal_bars", "stacked_share_bar"):
            self.assertTrue(callable(getattr(module, name)))

    def test_main_generates_only_the_declared_svgs_with_labels(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            module.main(output_dir)
            self.assertEqual(
                {path.name for path in output_dir.iterdir()}, set(EXPECTED_FILES)
            )
            for name, labels in EXPECTED_FILES.items():
                text = (output_dir / name).read_text(encoding="utf-8")
                self.assertIn("<svg", text)
                for label in labels:
                    self.assertIn(label, text, f"{label!r} absent from {name}")


if __name__ == "__main__":
    unittest.main()
