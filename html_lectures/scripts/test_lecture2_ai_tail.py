"""Scoped structural checks for Lecture 2 slides 26--31."""

import csv
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "lecture2_capital_markets_ai.qmd"
MANIFEST = ROOT / "data" / "lecture2" / "source_manifest.csv"
ASSET_DIR = ROOT / "assets" / "evidence"


def slide(source: str, title: str) -> str:
    match = re.search(
        rf"^## {re.escape(title)}\n(?P<body>.*?)(?=^## |\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Missing slide: {title}")
    return match.group("body")


class Lecture2AITailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = DECK.read_text(encoding="utf-8")

    def test_tail_has_exact_eight_titles_in_order(self) -> None:
        expected = [
            "AI Is Reorganising Information-Intensive Financial Work",
            "AI Changes Tasks Before It Changes Accountable Institutions",
            "Man + Machine Combines Different Information Advantages",
            "AI Wins on Scale; Humans Add Soft Information",
            "Fintech Disruption Reallocates Jobs and Skills",
            "Fintech Changes Hiring Before It Changes Firm Performance",
            "AI Adoption Creates a New Governance Stack",
            "Going Forward: Finance in 5–10 Years?",
        ]
        headings = re.findall(r"^## (.+)$", self.source, flags=re.MULTILINE)
        self.assertEqual(headings[-8:], expected)

    def test_use_cases_are_five_horizontal_rows_with_task_and_owner(self) -> None:
        body = slide(
            self.source, "AI Is Reorganising Information-Intensive Financial Work"
        )
        rows = re.findall(r"^\| \*\*(.+?)\*\* \| (.+?) \| (.+?) \|$", body, re.MULTILINE)
        self.assertEqual(len(rows), 5)
        self.assertEqual(
            [row[0] for row in rows],
            [
                "Research / origination",
                "Customer service / advice",
                "Risk / compliance",
                "Operations / knowledge",
                "Supervision / surveillance",
            ],
        )
        self.assertIn("Task change", body)
        self.assertIn("Retained responsibility", body)
        for _, task_change, retained_responsibility in rows:
            self.assertLessEqual(len(task_change.split()), 8)
            self.assertLessEqual(len(retained_responsibility.split()), 8)

    def test_automation_boundary_is_four_compact_levels(self) -> None:
        body = slide(
            self.source, "AI Changes Tasks Before It Changes Accountable Institutions"
        )
        self.assertNotIn("question-marker", body)
        rows = re.findall(
            r"^\| \*\*(.+?)\*\* \| (.+?) \| (.+?) \| (.+?) \|$",
            body,
            re.MULTILINE,
        )
        self.assertEqual([row[0] for row in rows], [
            "Augment",
            "Automate workflow",
            "Recommend",
            "Delegate action",
        ])
        for _, system_role, human_role, example in rows:
            self.assertLessEqual(len(system_role.split()), 5)
            self.assertLessEqual(len(human_role.split()), 5)
            self.assertLessEqual(len(example.split()), 6)

    def test_man_machine_uses_original_figure_and_preserves_scope(self) -> None:
        body = slide(
            self.source, "Man + Machine Combines Different Information Advantages"
        )
        self.assertIn(
            "![](assets/evidence/l2_man_machine_figure_slide.png)"
            "{fig-alt=\"Figure 3: year on the x-axis and annual beat ratio of AI-assisted "
            "analyst forecasts versus AI-only forecasts on the y-axis, with 95% "
            "confidence bounds and a 50% reference line\"}",
            body,
        )
        self.assertNotIn("editorial-grid", body)
        self.assertNotIn("final public-information ensemble beats", body)
        self.assertNotIn("How to read", body)
        for term in (
            "analyst information",
            "AI-only",
            "2001–2016",
            "year-end target-price",
            "w28800",
        ):
            self.assertIn(term, body)

    def test_man_machine_findings_separate_scale_soft_information_and_combination(self) -> None:
        body = slide(self.source, "AI Wins on Scale; Humans Add Soft Information")
        for term in ("year-end stock price", "53.7%", "57.3%", "complex", "illiquid", "intangible", "all years"):
            self.assertIn(term, body)

    def test_fintech_uses_original_figure_and_preserves_association_boundary(self) -> None:
        body = slide(self.source, "Fintech Disruption Reallocates Jobs and Skills")
        self.assertIn(
            "![](assets/evidence/l2_fintech_disruption_figure_slide.png)"
            "{fig-alt=\"Figure 6: fintech exposure percentile on the x-axis and 2007–2018 "
            "cumulative change in posting share on the y-axis, with a predicted "
            "curve and 95% confidence interval\"}",
            body,
        )
        self.assertNotIn("editorial-grid", body)
        self.assertNotIn("+1 exposure percentile", body)
        self.assertNotIn("How to read", body)
        for term in (
            "associated",
            "vacancy-share",
            "2007–2018",
            "not causal evidence",
            "layoffs",
            "employment",
            "growth",
            "w28668",
        ):
            self.assertIn(term, body)

    def test_fintech_findings_cover_jobs_skills_and_firm_adaptation(self) -> None:
        body = slide(
            self.source,
            "Fintech Changes Hiring Before It Changes Firm Performance",
        )
        for term in ("5%", "middle", "finance + software", "ROA", "inventor"):
            self.assertIn(term, body)

    def test_old_adoption_slide_and_old_synthesis_are_absent(self) -> None:
        self.assertNotIn(
            "Evidence on AI Performance Is Task- and Information-Dependent",
            self.source,
        )
        self.assertNotIn("About 75%", self.source)
        self.assertNotIn("Choose the Contract; Govern the Information Process", self.source)

    def test_closing_is_discussion_with_five_prediction_prompts(self) -> None:
        body = slide(self.source, "Going Forward: Finance in 5–10 Years?")
        for term in (
            "claim standardisation",
            "private information",
            "job / skill reallocation",
            "automation boundary",
            "accountability",
        ):
            self.assertIn(term, body)
        self.assertIn("Discuss how finance may change", body)
        self.assertIn("For discussion:", body)
        self.assertNotIn("Write one prediction", body)

    def test_manifest_includes_both_research_records(self) -> None:
        with MANIFEST.open(encoding="utf-8", newline="") as handle:
            records = {row["dataset_id"]: row for row in csv.DictReader(handle)}
        self.assertIn("man_machine_forecasts", records)
        self.assertIn("fintech_disruption", records)
        self.assertIn("w28800", records["man_machine_forecasts"]["source_url"])
        self.assertIn("w28668", records["fintech_disruption"]["source_url"])
        self.assertIn("jfineco", records["fintech_disruption"]["source_url"])

    def test_original_paper_figure_assets_are_present_and_nontrivial(self) -> None:
        for name in (
            "l2_man_machine_figure.png",
            "l2_fintech_disruption_figure.png",
        ):
            with self.subTest(name=name):
                path = ASSET_DIR / name
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 50_000)
                with tempfile.TemporaryDirectory() as directory:
                    local_copy = Path(directory) / name
                    shutil.copyfile(path, local_copy)
                    image = Image.open(local_copy)
                    self.addCleanup(image.close)
                    self.assertEqual(image.format, "PNG")
                    self.assertGreaterEqual(max(image.size), 1_600)
                    self.assertGreaterEqual(min(image.size), 1_200)

                    rgb = image.convert("RGB")
                    difference = ImageChops.difference(
                        rgb, Image.new("RGB", rgb.size, "white")
                    )
                    nonwhite = difference.convert("L").point(
                        lambda pixel: 255 if pixel > 3 else 0
                    )
                    bounds = nonwhite.getbbox()
                    self.assertIsNotNone(bounds)
                    left, top, right, bottom = bounds
                    content_area_ratio = (
                        (right - left) * (bottom - top) / (rgb.width * rgb.height)
                    )
                    self.assertGreater(content_area_ratio, 0.70)
                    self.assertLess(rgb.height - bottom, rgb.height * 0.15)

    def test_slide_display_crops_are_wide_and_pixel_faithful_to_parent(self) -> None:
        expected = {
            "l2_man_machine_figure_slide.png": (2200, 1315),
            "l2_fintech_disruption_figure_slide.png": (1840, 760),
        }
        for name, size in expected.items():
            with self.subTest(name=name):
                path = ASSET_DIR / name
                self.assertTrue(path.exists())
                if not path.exists():
                    continue
                with Image.open(path) as image:
                    self.assertEqual(image.size, size)
                    self.assertGreater(image.width / image.height, 1.5)

        if not all((ASSET_DIR / name).exists() for name in expected):
            return

        with Image.open(ASSET_DIR / "l2_man_machine_figure.png") as parent:
            with Image.open(ASSET_DIR / "l2_man_machine_figure_slide.png") as display:
                self.assertIsNone(
                    ImageChops.difference(
                        display.convert("RGB"),
                        parent.crop((0, 405, 2200, 1720)).convert("RGB"),
                    ).getbbox()
                )

        with Image.open(ASSET_DIR / "l2_fintech_disruption_figure.png") as parent:
            with Image.open(
                ASSET_DIR / "l2_fintech_disruption_figure_slide.png"
            ) as display:
                self.assertIsNone(
                    ImageChops.difference(
                        display.convert("RGB"),
                        parent.crop((0, 130, 1840, 890)).convert("RGB"),
                    ).getbbox()
                )

    def test_original_figure_manifest_records_are_auditable(self) -> None:
        with MANIFEST.open(encoding="utf-8", newline="") as handle:
            records = {row["dataset_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "man_machine_original_figure": ("Figure 3", "35"),
            "fintech_disruption_original_figure": ("Figure 6", "43"),
        }
        for dataset_id, (figure_number, pdf_page) in expected.items():
            with self.subTest(dataset_id=dataset_id):
                record = records[dataset_id]
                self.assertEqual(record["figure_number"], figure_number)
                self.assertEqual(record["pdf_page"], pdf_page)
                self.assertIn("unredrawn crop", record["crop_scope"].lower())
                self.assertTrue(record["interpretation_boundary"])

    def test_slide_display_crop_manifest_records_name_parent_and_page(self) -> None:
        with MANIFEST.open(encoding="utf-8", newline="") as handle:
            records = {row["dataset_id"]: row for row in csv.DictReader(handle)}
        expected = {
            "man_machine_slide_figure": (
                "l2_man_machine_figure.png",
                "Figure 3",
                "35",
            ),
            "fintech_disruption_slide_figure": (
                "l2_fintech_disruption_figure.png",
                "Figure 6",
                "43",
            ),
        }
        for dataset_id, (parent, figure_number, pdf_page) in expected.items():
            with self.subTest(dataset_id=dataset_id):
                self.assertIn(dataset_id, records)
                if dataset_id not in records:
                    continue
                record = records[dataset_id]
                self.assertIn(parent, record["crop_scope"])
                self.assertEqual(record["figure_number"], figure_number)
                self.assertEqual(record["pdf_page"], pdf_page)
                self.assertIn("no scaling or redrawing", record["crop_scope"].lower())


if __name__ == "__main__":
    unittest.main()
