from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR.parent
QUARTO_CONFIG = PROJECT_DIR / "_quarto.yml"
STYLESHEET = PROJECT_DIR / "styles.scss"
LECTURE_ONE = PROJECT_DIR / "lecture1_payment_banks.qmd"
LECTURE_TWO = PROJECT_DIR / "lecture2_capital_markets_ai.qmd"
APPROVED_SPEC = WORKSPACE_DIR / "docs/superpowers/specs/2026-07-10-lecture1-27-slide-refinement-design.md"


class PresentationShellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = QUARTO_CONFIG.read_text(encoding="utf-8")
        cls.scss = STYLESHEET.read_text(encoding="utf-8")
        cls.lecture_one = LECTURE_ONE.read_text(encoding="utf-8")
        cls.lecture_two = LECTURE_TWO.read_text(encoding="utf-8")
        cls.spec = APPROVED_SPEC.read_text(encoding="utf-8")

    @classmethod
    def lecture_one_slide(cls, title: str) -> str:
        marker = f"## {title}"
        start = cls.lecture_one.find(marker)
        if start == -1:
            return ""
        next_slide = cls.lecture_one.find("\n## ", start + len(marker))
        return cls.lecture_one[start:] if next_slide == -1 else cls.lecture_one[start:next_slide]

    def test_reveal_build_contract(self) -> None:
        required_lines = (
            "output-dir: _site",
            "theme: styles.scss",
            "slide-number: c/t",
            "transition: fade",
            "background-transition: fade",
            "hash: true",
            "embed-resources: true",
            "width: 1280",
            "height: 720",
            "center: false",
            "code-overflow: wrap",
        )
        for line in required_lines:
            with self.subTest(line=line):
                self.assertIn(line, self.config)
        self.assertIn("post-render: python3 scripts/embed_css_dependencies.py _site", self.config)

    def test_spec_is_marked_approved(self) -> None:
        self.assertRegex(self.spec, r"(?m)^Status: approved$")

    def test_palette_typography_and_source_floor(self) -> None:
        for name, value in {
            "paper": "#F7F3EA",
            "ink": "#172132",
            "brick": "#C9583E",
            "blue": "#4B718A",
            "gold": "#C59A45",
            "muted": "#6F746F",
        }.items():
            with self.subTest(token=name):
                self.assertRegex(
                    self.scss,
                    rf"\${name}:\s*{re.escape(value)}\s*;",
                )
        self.assertIn("$presentation-font-size-root: 27px;", self.scss)
        self.assertIn('Aptos, "Helvetica Neue", Arial, sans-serif', self.scss)
        self.assertNotIn('Georgia, Charter, "Times New Roman", serif', self.scss)
        self.assertNotIn("Inter", self.scss)
        source_rule = re.search(r"\.source\s*\{(?P<body>.*?)\}", self.scss, re.DOTALL)
        self.assertIsNotNone(source_rule)
        self.assertRegex(source_rule.group("body"), r"font-size:\s*13px\s*;")

    def test_comparison_tables_and_timeline_headings_are_readable(self) -> None:
        self.assertRegex(self.scss, r"(?s)\.comparison table,[^}]*font-size:\s*0\.68em")
        heading_size = re.search(
            r"(?s)\.timeline strong\s*\{[^}]*font-size:\s*(?P<size>[\d.]+)em",
            self.scss,
        )
        body_size = re.search(
            r"(?s)\.timeline p\s*\{[^}]*font-size:\s*(?P<size>[\d.]+)em",
            self.scss,
        )
        self.assertIsNotNone(heading_size)
        self.assertIsNotNone(body_size)
        self.assertEqual(float(heading_size.group("size")), 0.76)
        self.assertGreater(float(heading_size.group("size")), float(body_size.group("size")))

    def test_final_bond_market_figure_is_scoped_to_fit_with_thesis(self) -> None:
        self.assertRegex(
            self.scss,
            r"(?s)#how-fast-did-chinas-bond-market-grow\s+\.large-figure img\s*"
            r"\{[^}]*max-height:\s*315px\s*;",
        )

    def test_bank_history_timeline_titles_are_separate_from_body_paragraphs(self) -> None:
        timeline = self.lecture_one_slide("Why Did China Develop Such a Large Banking System?")
        headings = (
            "Monobank legacy",
            "Two-tier system",
            "Big Four + policy banks",
            "Other banks + markets",
        )
        self.assertEqual(timeline.count('class="timeline-heading"'), 4)
        for heading in headings:
            with self.subTest(heading=heading):
                self.assertIn(
                    f'<div class="timeline-heading"><strong>{heading}</strong></div>',
                    timeline,
                )
                self.assertNotIn(f"**{heading}**", timeline)

    def test_semantic_component_contract(self) -> None:
        classes = (
            "deck-kicker",
            "question-marker",
            "thesis",
            "editorial-grid",
            "evidence-layout",
            "mechanism",
            "dual-flow",
            "timeline",
            "comparison",
            "activity",
            "synthesis-map",
            "source",
            "takeaway",
            "figure-height-sm",
            "figure-height-md",
            "figure-height-lg",
        )
        for class_name in classes:
            with self.subTest(class_name=class_name):
                self.assertRegex(self.scss, rf"\.{class_name}(?![\w-])")

    def test_asymmetric_information_diagram_styles_are_narrowly_scoped(self) -> None:
        for selector in (
            "asym-diagram",
            "asym-unravel",
            "asym-equity-wedge",
            "asym-debt-fork",
        ):
            with self.subTest(selector=selector):
                self.assertRegex(
                    self.scss,
                    rf"(?m)^\.reveal \.slides section \.{selector}(?![\w-])",
                )
                self.assertNotRegex(self.scss, rf"(?m)^\.{selector}(?![\w-])")

        asym_selector_lines = re.findall(r"(?m)^[^@{}]*\.asym-[^{]*\{", self.scss)
        self.assertTrue(asym_selector_lines, "missing asymmetric-information SCSS selectors")
        for selector_line in asym_selector_lines:
            with self.subTest(selector=selector_line.strip()):
                self.assertNotRegex(selector_line, r"(?<![\w-])\.card(?![\w-])")
                self.assertNotRegex(selector_line, r"(?<![\w-])\.node(?![\w-])")
                self.assertNotRegex(
                    selector_line,
                    r"\.(?:rail-|instrument-|balance-sheet|history-body)[\w-]*",
                )

    def test_asymmetric_overlay_connectors_are_disabled(self) -> None:
        connector = re.search(
            r"\.reveal \.slides section \.asym-diagram \.asym-connectors\s*\{(?P<body>.*?)\}",
            self.scss,
            re.S,
        )
        self.assertIsNotNone(connector)
        self.assertRegex(connector.group("body"), r"display:\s*none")

    def test_asymmetric_arrows_are_generated_in_card_gutters(self) -> None:
        self.assertRegex(self.scss, r"\.asym-gutter-arrow-right::after[^\{]*\{")
        self.assertRegex(self.scss, r"\.asym-gutter-arrow-left::before[^\{]*\{")
        self.assertRegex(self.scss, r"content:\s*[\"']→[\"']")
        self.assertRegex(self.scss, r"content:\s*[\"']←[\"']")
        self.assertRegex(self.scss, r"right:\s*-\d+px")
        self.assertRegex(self.scss, r"left:\s*-\d+px")

    def test_asymmetric_connectors_use_exterior_orthogonal_routes(self) -> None:
        for forbidden_rotation in ("rotate(24deg)", "rotate(-24deg)", "rotate(35deg)", "rotate(155deg)"):
            with self.subTest(forbidden_rotation=forbidden_rotation):
                self.assertNotIn(forbidden_rotation, self.scss)


    def test_layouts_are_overflow_safe_and_images_are_bounded(self) -> None:
        for class_name in (
            "editorial-grid",
            "evidence-layout",
            "mechanism",
            "flow",
            "dual-flow",
            "timeline",
            "comparison",
            "activity",
            "synthesis-map",
        ):
            with self.subTest(class_name=class_name):
                self.assertRegex(
                    self.scss,
                    rf"\.{class_name}\s*\{{[^}}]*min-width:\s*0",
                )
                self.assertRegex(
                    self.scss,
                    rf"\.{class_name}\s*>\s*\*[^{{]*\{{[^}}]*min-width:\s*0",
                )
        self.assertRegex(
            self.scss,
            r"\.dual-flow\s*>\s*\*\s*>\s*\*[^\{]*\{[^}]*min-width:\s*0",
        )
        self.assertRegex(
            self.scss,
            r"\.reveal\s+img\s*\{[^}]*max-height:\s*430px",
        )
        for class_name, height in (
            ("figure-height-sm", 280),
            ("figure-height-md", 360),
            ("figure-height-lg", 430),
        ):
            with self.subTest(class_name=class_name):
                self.assertRegex(
                    self.scss,
                    rf"\.{class_name}\s+img\s*\{{[^}}]*max-height:\s*{height}px",
                )

    def test_lecture_one_semantic_layout_classes_exist_in_source_and_scss(self) -> None:
        for name in (
            "rail-stack",
            "rail-row",
            "instrument-grid",
            "instrument-card",
            "layer-stack",
            "layer-row",
            "transformation-grid",
            "transformation-card",
            "history-body",
        ):
            with self.subTest(name=name):
                self.assertIn(name, self.lecture_one)
                self.assertIn(f".{name}", self.scss)

    def test_lecture_one_title_slide_contains_only_requested_metadata(self) -> None:
        front_matter = self.lecture_one.split("---", 2)[1]
        for required in (
            'title: "From Bank Payments to the Financial System"',
            'subtitle: "What payment institutions added—and why bank balance sheets still matter"',
            'author: "Xiaoquan Wang"',
            'institute: "SUIBE"',
            'date: "July 13, 2026"',
        ):
            self.assertIn(required, front_matter)
        for removed in ("title-thesis", "title-layer-path", "Pay</strong>", "Settle</strong>", "Finance</strong>"):
            self.assertNotIn(removed, front_matter)

    def test_lecture_two_deleted_slides_are_absent(self) -> None:
        source = self.lecture_two
        for title in (
            "Liquidity Depends on Standardisation and Market Design",
            "Formal Exchanges and Split-Share Reform Built the Foundation",
        ):
            with self.subTest(title=title):
                self.assertFalse(title in source, f"deleted slide remains: {title}")

    def test_lecture_two_performing_state_notation_is_literal_and_well_formed(self) -> None:
        source = self.lecture_two
        self.assertTrue("X > D" in source, "literal performing-state notation X > D is missing")
        self.assertFalse("X D" in source, "malformed performing-state notation X D remains")

    def test_lecture_two_title_metadata_matches_third_revision(self) -> None:
        source = self.lecture_two
        for required in ('author: "Xiaoquan Wang"', 'institute: "SUIBE"'):
            with self.subTest(required=required):
                self.assertTrue(required in source, f"required metadata is missing: {required}")
        for removed in (
            "International Summer School on Cross-Border Finance",
            "Choose the contract for the financing problem",
        ):
            with self.subTest(removed=removed):
                self.assertFalse(removed in source, f"removed title metadata remains: {removed}")

    def test_before_wallets_uses_readable_rail_and_instrument_type(self) -> None:
        expected_sizes = {
            r"(?s)\.rail-label\s*\{[^}]*font-size:\s*1\.05em": "rail label",
            r"(?s)\.rail-chain\s*\{[^}]*font-size:\s*0\.92em": "rail chain",
            r"(?s)\.instrument-title\s*\{[^}]*font-size:\s*1em": "instrument title",
            r"(?s)\.instrument-card\s*>\s*p\s*\{[^}]*font-size:\s*0\.88em": "instrument body",
            r"(?s)\.instrument-title p\s*\{[^}]*font-size:\s*1em": "instrument title reset",
        }
        for pattern, label in expected_sizes.items():
            with self.subTest(label=label):
                self.assertRegex(self.scss, pattern)

    def test_title_metadata_is_left_aligned_and_readable(self) -> None:
        expectations = {
            r"(?s)#title-slide \.subtitle,[^}]*font-size:\s*0\.90em": "subtitle size",
            r"(?s)#title-slide \.quarto-title-author-name,[^}]*font-size:\s*0\.95em": "author size",
            r"(?s)#title-slide \.quarto-title-affiliation,[^}]*font-size:\s*0\.82em": "affiliation size",
            r"(?s)#title-slide \.date,[^}]*font-size:\s*0\.82em": "date size",
            r"(?s)#title-slide \.quarto-title-author,[^}]*\{[^}]*text-align:\s*left": "author alignment",
        }
        for pattern, label in expectations.items():
            with self.subTest(label=label):
                self.assertRegex(self.scss, pattern)

    def test_bank_balance_sheet_is_two_sided_with_one_item_per_row(self) -> None:
        slide = self.lecture_one_slide("A Bank Balance Sheet in One Picture")
        self.assertIn('class="balance-sheet-grid"', slide)
        self.assertIn('class="balance-sheet-side assets-side"', slide)
        self.assertIn('class="balance-sheet-side funding-side"', slide)
        self.assertEqual(slide.count('class="balance-sheet-row"'), 6)
        for item in ("Reserves", "Securities", "Loans", "Deposits", "Other funding", "Equity"):
            self.assertIn(f"<strong>{item}</strong>", slide)
        self.assertNotIn("| Reserves | Securities | Loans |", slide)

    def test_lecture_one_target_slides_have_no_anonymous_wrappers(self) -> None:
        for title in (
            "Before Wallets: The Bank-Based Payment System",
            "One Payment, Two Layers: Wallet Interface, Bank Settlement",
            "What Banks Transform—and What Risks They Bear",
            "Why Did China Develop Such a Large Banking System?",
        ):
            with self.subTest(title=title):
                self.assertNotIn("::: {}", self.lecture_one_slide(title))

    def test_lecture_one_has_exact_27_title_order_and_12_15_boundary(self) -> None:
        titles = re.findall(r"^## (.+)$", self.lecture_one, re.MULTILINE)
        self.assertEqual(len(titles), 26)
        self.assertEqual(titles[10], "What Third-Party Payment Changed—and What It Did Not Replace")
        self.assertEqual(titles[11], "China’s Financial System: Formal, Market and Alternative Channels")
        self.assertEqual(titles[-10:], [
            "Household Saving Funds a Bank-Centered System",
            "Beyond Bank Loans: AFRE / GDP by Financing Channel",
            "Private-Sector Credit / GDP: China, US, Euro Area and Japan",
            "What Does AFRE/TSF Measure?",
            "How Large Is AFRE Relative to China’s Economy?",
            "What Is China’s Financing Mix Today?",
            "Where Did China’s Leverage Accumulate?",
            "Why Official Local Debt Understates Fiscal Exposure",
            "Stock-Market Capitalization / GDP: Three Available Systems",
            "How Fast Did China’s Bond Market Grow?",
        ])
        for removed in (
            "Bank Size Is Not the Same as Bank Efficiency",
            "How Is China’s Financing Mix Structured?",
            "How Should We Diagnose a Bank-Centered System?",
            "Synthesis: Payments, Banks, Markets and Alternative Finance",
        ):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, titles)

    def test_modern_evidence_source_notes_preserve_data_boundaries(self) -> None:
        channels = self.lecture_one_slide("Beyond Bank Loans: AFRE / GDP by Financing Channel")
        self.assertIn("He & Wei (2022), Figure 1", channels)
        self.assertIn("2002–2021", channels)
        self.assertIn("vector-digitized plotted approximations", channels)

        leverage = self.lecture_one_slide("Where Did China’s Leverage Accumulate?")
        self.assertIn("Chang, Wang & Xiong (2025), Figure 5", leverage)
        self.assertIn("public workbook", leverage)
        self.assertIn("LGFV debt is included in nonfinancial corporations", leverage)

        broad_debt = self.lecture_one_slide("Why Official Local Debt Understates Fiscal Exposure")
        self.assertIn("Chang, Wang & Xiong (2025), Figure 6", broad_debt)
        self.assertIn("official debt and LGFV liabilities", broad_debt)
        self.assertIn("vector-digitized plotted approximations", broad_debt)

    def test_payment_slide_declares_long_run_scope_and_plain_transition(self) -> None:
        payment = self.lecture_one_slide("Did Third-Party Payment Expand Payment Inclusion?")
        self.assertIn("China · 2007–2024", payment)
        self.assertIn("includes bank and third-party online payment", payment)
        self.assertIn("year-end observations", payment)
        self.assertIn("2019 unavailable", payment)
        self.assertIn("not a causal estimate", payment)
        self.assertNotIn("—but not bank-only—", self.lecture_one)
        self.assertIn(
            "Lecture 2 asks what bond, equity and private-capital markets add to this bank-centered system.",
            self.lecture_one,
        )


if __name__ == "__main__":
    unittest.main()
