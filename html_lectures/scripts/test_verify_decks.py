from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPTS_DIR / "verify_decks.py"


class ValidatorExistenceTest(unittest.TestCase):
    def test_validator_module_exists(self) -> None:
        self.assertTrue(MODULE_PATH.is_file(), "verify_decks.py has not been implemented")


@unittest.skipUnless(MODULE_PATH.is_file(), "validator not implemented yet")
class ValidatorBehaviorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("verify_decks", MODULE_PATH)
        assert spec is not None and spec.loader is not None
        cls.validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.validator)

    def write_deck(self, root: Path, body: str) -> Path:
        deck = root / "deck.qmd"
        deck.write_text(body, encoding="utf-8")
        return deck

    def test_lecture1_contract_matches_rebalanced_payment_financial_system_arc(self) -> None:
        self.assertEqual(len(self.validator.L1_TITLES), 27)
        self.assertEqual(
            self.validator.L1_TITLES[11],
            "What Third-Party Payment Changed—and What It Did Not Replace",
        )
        self.assertEqual(
            self.validator.L1_TITLES[12],
            "China’s Financial System: Formal, Market and Alternative Channels",
        )
        self.assertEqual(
            self.validator.L1_TITLES[-5:],
            [
                "What Is China’s Financing Mix Today?",
                "Where Did China’s Leverage Accumulate?",
                "Why Official Local Debt Understates Fiscal Exposure",
                "Stock-Market Capitalization / GDP: Three Available Systems",
                "How Fast Did China’s Bond Market Grow?",
            ],
        )
        self.assertEqual(
            self.validator.L1_TITLES[18],
            "Beyond Bank Loans: AFRE / GDP by Financing Channel",
        )
        for removed in (
            "Bank Size Is Not the Same as Bank Efficiency",
            "How Is China’s Financing Mix Structured?",
            "How Should We Diagnose a Bank-Centered System?",
            "Synthesis: Payments, Banks, Markets and Alternative Finance",
        ):
            self.assertNotIn(removed, self.validator.L1_TITLES)

    def test_lecture1_source_does_not_reference_old_allen_screenshots(self) -> None:
        source = (MODULE_PATH.parent.parent / "lecture1_payment_banks.qmd").read_text(
            encoding="utf-8"
        )
        for filename in (
            "allen_private_hybrid_credit_comparison.png",
            "allen_hybrid_financing_sources.png",
            "allen_hybrid_output.png",
        ):
            self.assertNotIn(filename, source)

    def test_lecture2_contract_matches_asymmetric_information_revision(self) -> None:
        expected = [
            "From Financial Contracts to Market Information",
            "Some Financing Problems Do Not Fit an Ordinary Bank Loan",
            "Financial Contracts Are Contingent Claims",
            "Cash-Flow Rights and Control Rights Divide the States",
            "Adverse Selection Can Drive Good Firms Out",
            "Moral Hazard in Equity: The Principal-Agent Problem",
            "Moral Hazard in Debt: Borrowers May Shift Risk",
            "Cash Flow, Information and Control Determine Contract Choice",
            "China Implements These Contracts Through Distinct Markets",
            "Bonds Fit Predictable Cash Flow and Limited Control Needs",
            "Two Core Venues Serve Different Instruments and Investors",
            "China’s Bond Market Grew—But Remained Predominantly Interbank",
            "Institutions Anchor the Interbank Bond Market",
            "A Large Bond Market Is Not Mainly Corporate Debt",
            "Reforms Expanded Access, Pricing and Default Discipline",
            "Bond Yields Mix Fundamentals with Liquidity and Support Expectations",
            "Equity Has a Primary and a Secondary Market",
            "China’s Equity Market Expanded in Waves",
            "China’s IPO System Moved from Approval to Registration",
            "New Equity Venues Serve Issuers the Main Boards Do Not Fit",
            "Four Equity Submarkets Grew at Different Speeds",
            "Stock Connect Turned Market Opening into Trading Infrastructure",
            "Private Contracts Finance Information Before Public Prices Exist",
            "China’s PE/VC System Connects Funds, Managers, Firms and Exits",
            "Private Funds Are Large but Category Boundaries Matter",
            "Exit Institutions Shape Willingness to Fund Innovation",
            "AI Is Reorganising Information-Intensive Financial Work",
            "AI Changes Tasks Before It Changes Accountable Institutions",
            "Man + Machine Combines Different Information Advantages",
            "AI Wins on Scale; Humans Add Soft Information",
            "Fintech Disruption Reallocates Jobs and Skills",
            "Fintech Changes Hiring Before It Changes Firm Performance",
            "AI Adoption Creates a New Governance Stack",
            "Going Forward: Finance in 5–10 Years?",
        ]
        self.assertEqual(len(expected), 34)
        self.assertEqual(self.validator.L2_TITLES, expected)

    def test_lecture2_title_metadata_is_exact_and_rejects_mutations(self) -> None:
        source = self.validator.DECKS["lecture2"][0].read_text(encoding="utf-8")

        mutations = {
            "extra display field": source.replace(
                'date: "July 14, 2026"',
                'date: "July 14, 2026"\ncourse: UNAPPROVED',
                1,
            ),
            "quoted extra display field": source.replace(
                'date: "July 14, 2026"',
                'date: "July 14, 2026"\n"course": UNAPPROVED',
                1,
            ),
            "dotted extra display field": source.replace(
                'date: "July 14, 2026"',
                'date: "July 14, 2026"\ncourse.name: UNAPPROVED',
                1,
            ),
            "quoted duplicate approved field": source.replace(
                'title: "From Financial Contracts to Market Information"',
                'title: "From Financial Contracts to Market Information"\n'
                '"title": "UNAPPROVED DUPLICATE"',
                1,
            ),
            "wrong subtitle": source.replace(
                'subtitle: "Bonds, Equity, PE/VC and AI in China’s Financial Development"',
                'subtitle: "UNAPPROVED"',
                1,
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            for label, mutated_source in mutations.items():
                with self.subTest(label=label):
                    deck = Path(directory) / "lecture2_capital_markets_ai.qmd"
                    deck.write_text(mutated_source, encoding="utf-8")
                    errors = self.validator.validate_deck(deck, self.validator.L2_TITLES)
                    self.assertTrue(
                        any("title metadata" in error for error in errors), errors
                    )

    def test_lecture2_forbidden_patterns_reject_deleted_slides_and_title_slogan(self) -> None:
        forbidden_patterns = (
            "Liquidity Depends on Standardisation and Market Design",
            "Formal Exchanges and Split-Share Reform Built the Foundation",
            "Choose the contract for the financing problem",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for forbidden in forbidden_patterns:
                with self.subTest(forbidden=forbidden):
                    deck = root / "lecture2_capital_markets_ai.qmd"
                    deck.write_text(
                        '---\ntitle: "Good"\n---\n\n## Also Good\n\n' + forbidden + "\n",
                        encoding="utf-8",
                    )
                    errors = self.validator.validate_deck(deck, ["Good", "Also Good"])
                    self.assertTrue(
                        any("forbidden" in error and forbidden in error for error in errors),
                        errors,
                    )

    def test_lecture2_equity_reforms_are_chronological_and_papers_are_present(self) -> None:
        source = self.validator.DECKS["lecture2"][0].read_text(encoding="utf-8")
        markers = [
            "**1993–2000 · Administrative allocation / approval**",
            "**March 2001–2018 · Merit review and sponsor responsibility**",
            "**2019–2022 · STAR and ChiNext registration pilots**",
            "**2023 onward · Full registration across markets**",
        ]
        positions = [source.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        equity_slides = [
            "## China’s IPO System Moved from Approval to Registration",
            "## New Equity Venues Serve Issuers the Main Boards Do Not Fit",
            "## Four Equity Submarkets Grew at Different Speeds",
            "## Stock Connect Turned Market Opening into Trading Infrastructure",
        ]
        slide_positions = [source.index(marker) for marker in equity_slides]
        self.assertEqual(slide_positions, sorted(slide_positions))
        self.assertIn("w28800", source)
        self.assertIn("w28668", source)

    def test_lecture2_equity_submarket_slide_discloses_limited_bse_provenance(self) -> None:
        source = self.validator.DECKS["lecture2"][0].read_text(encoding="utf-8")
        self.assertIn("SSE/SZSE/CSRC official year-end statistics", source)
        self.assertIn(
            "BSE 2022–23 and 2025 combine the BSE archive with year-specific "
            "secondary corroboration",
            source,
        )
        self.assertNotIn(
            "Source/definition: SSE, SZSE, BSE and CSRC year-end total market "
            "capitalisation",
            source,
        )

    def test_lecture2_contract_and_equity_module_matches_third_revision_content(self) -> None:
        source = self.validator.DECKS["lecture2"][0].read_text(encoding="utf-8")
        required = (
            "Performing state · (X > D)",
            "![](assets/figures/l2_stock_connect_adt.svg)",
            "Opening worked through infrastructure: eligible securities, order routing, clearing, custody and quotas converted legal access into daily trading.",
            "Administrative allocation / approval",
            "Merit review and sponsor responsibility",
            "STAR and ChiNext registration pilots",
            "Full registration across markets",
            "New venues segment issuers by information, technology and maturity rather than making one listing standard fit every firm.",
            "![](assets/figures/l2_equity_submarkets_market_cap.svg)",
        )
        for item in required:
            with self.subTest(item=item):
                self.assertIn(item, source)

        for superseded in (
            "## ChiNext Added a Market for Growth and Innovation",
            "## Stock Connect Opened the Market Through Infrastructure",
            "## STAR Combined a Hard-Technology Board with Registration",
            "## The Beijing Stock Exchange Created a Venue for Innovative SMEs",
            "## Full Registration Shifted Responsibility toward Disclosure",
        ):
            with self.subTest(superseded=superseded):
                self.assertNotIn(superseded, source)

    def test_lecture2_stock_connect_and_ipo_sources_are_authoritative_and_bounded(self) -> None:
        source = self.validator.DECKS["lecture2"][0].read_text(encoding="utf-8")
        for item in (
            "HKEX, *Stock Connect 2025 Review*",
            "Northbound in RMB bn; Southbound in HKD bn",
            "2014 is the post-launch period from 17 November",
            "CSRC, *Stock Issuance and Listing*",
            "Quota management (1993–95) and indicator management (1996–2000)",
            "CSRC, *Deepening Issuance-System Reform through the Sponsorship System*",
            "CSRC, *Consultation on Full Registration-System Rules*",
            "CSRC, *Full Registration-System Rules Issued*",
        ):
            with self.subTest(item=item):
                self.assertIn(item, source)

    def test_lecture2_deleted_material_is_absent(self) -> None:
        source = self.validator.DECKS["lecture2"][0].read_text(encoding="utf-8")
        for deleted in (
            "China Is Large in Absolute Terms but Not by Every Relative Measure",
            "Final Synthesis: Contracts, Prices, Information and Responsibility",
            "Quant",
            "Zhangjiang",
            "Government VC",
            "Five Questions for Lecture 2",
            "Five Questions About China’s Bond Market",
            "Six Questions About China’s Equity Market",
            "Five Questions About PE/VC",
            "Five Questions About Quant and AI",
            "What Does the Bond Market Add?",
            "What Does the Equity Market Add?",
            "What Does PE/VC Add?",
        ):
            self.assertNotIn(deleted, source)

    def test_yaml_title_is_slide_one_and_only_level_two_headings_follow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            deck = self.write_deck(
                Path(directory),
                '---\ntitle: "Title Slide"\n---\n\n## Slide Two\n\n### Not a slide\n',
            )
            self.assertEqual(
                self.validator.validate_deck(deck, ["Title Slide", "Slide Two"]), []
            )

    def test_reports_count_and_first_title_mismatch_with_one_based_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            deck = self.write_deck(
                Path(directory),
                "---\ntitle: Actual Title\n---\n\n## Actual Two\n",
            )
            errors = self.validator.validate_deck(
                deck, ["Expected Title", "Expected Two", "Expected Three"]
            )
            self.assertTrue(any("wrong count" in error for error in errors), errors)
            self.assertTrue(
                any(
                    "slide 1" in error
                    and "Expected Title" in error
                    and "Actual Title" in error
                    for error in errors
                ),
                errors,
            )
            self.assertEqual(
                sum("title mismatch" in error for error in errors),
                1,
                "only the first title mismatch should be reported",
            )

    def test_reports_missing_tail_as_first_title_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            deck = self.write_deck(
                Path(directory),
                "---\ntitle: One\n---\n\n## Two\n",
            )
            errors = self.validator.validate_deck(deck, ["One", "Two", "Three"])
            self.assertTrue(
                any(
                    "title mismatch" in error
                    and "slide 3" in error
                    and "Three" in error
                    and "missing" in error
                    for error in errors
                ),
                errors,
            )

    def test_reports_extra_tail_as_first_title_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            deck = self.write_deck(
                Path(directory),
                "---\ntitle: One\n---\n\n## Two\n\n## Three\n",
            )
            errors = self.validator.validate_deck(deck, ["One", "Two"])
            self.assertTrue(
                any(
                    "title mismatch" in error
                    and "slide 3" in error
                    and "Three" in error
                    and "extra" in error
                    for error in errors
                ),
                errors,
            )

    def test_reports_forbidden_source_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            deck = self.write_deck(
                Path(directory),
                "---\ntitle: Good\n---\n\n## Also Good\n\n"
                "Appendix material\n\n![](http://example.com/chart.png)\n"
                "![](../work/chart.png)\n",
            )
            errors = self.validator.validate_deck(deck, ["Good", "Also Good"])
            self.assertTrue(any("appendix" in error for error in errors), errors)
            self.assertTrue(any("../work/" in error for error in errors), errors)
            self.assertTrue(any("remote image" in error for error in errors), errors)

    def test_local_images_must_exist_beneath_project_assets(self) -> None:
        project_root = MODULE_PATH.parent.parent
        with tempfile.TemporaryDirectory(dir=project_root) as directory:
            root = Path(directory)
            (root / "existing.svg").write_text("<svg/>", encoding="utf-8")
            deck = self.write_deck(
                root,
                "---\ntitle: Good\n---\n\n## Also Good\n\n"
                "![asset](../assets/figures/l1_bank_assets_nfra.svg)\n"
                "![outside](existing.svg)\n"
                "![absent](../assets/missing.png)\n",
            )
            errors = self.validator.validate_deck(deck, ["Good", "Also Good"])
            self.assertFalse(
                any("l1_bank_assets_nfra.svg" in error for error in errors), errors
            )
            self.assertTrue(
                any("existing.svg" in error and "outside assets" in error for error in errors),
                errors,
            )
            self.assertTrue(
                any("missing.png" in error and "missing" in error for error in errors),
                errors,
            )

    def test_cli_can_select_one_deck(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lecture1 = root / "lecture1_fixture.qmd"
            lecture1.write_text(
                '---\ntitle: "Lecture 1 Fixture"\n---\n\n## Lecture 1 Slide Two\n',
                encoding="utf-8",
            )
            lecture2 = root / "lecture2_fixture.qmd"
            lecture2.write_text(
                '---\ntitle: "Lecture 2 Fixture"\n---\n\n## Lecture 2 Slide Two\n',
                encoding="utf-8",
            )
            decks = {
                "lecture1": (lecture1, ["Lecture 1 Fixture", "Lecture 1 Slide Two"]),
                "lecture2": (lecture2, ["Lecture 2 Fixture", "Lecture 2 Slide Two"]),
            }
            output = io.StringIO()
            with (
                patch.object(self.validator, "DECKS", decks),
                patch.object(sys, "argv", [str(MODULE_PATH), "--deck", "lecture1"]),
                redirect_stdout(output),
            ):
                exit_code = self.validator.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("lecture1_fixture.qmd", output.getvalue())
        self.assertNotIn("lecture2_fixture.qmd", output.getvalue())


if __name__ == "__main__":
    unittest.main()
