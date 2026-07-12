import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "index.qmd"
RENDERED = ROOT / "_site" / "index.html"


class CourseIndexTests(unittest.TestCase):
    def test_source_is_a_course_landing_page(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("SUIBE Summer School", text)
        self.assertIn("lecture1_payment_banks.html", text)
        self.assertIn("lecture2_capital_markets_ai.html", text)
        self.assertIn("format: html", text)
        self.assertIn("embed-resources: true", text)

    def test_rendered_index_links_both_lectures(self) -> None:
        text = RENDERED.read_text(encoding="utf-8")
        self.assertIn('href="lecture1_payment_banks.html"', text)
        self.assertIn('href="lecture2_capital_markets_ai.html"', text)


if __name__ == "__main__":
    unittest.main()
