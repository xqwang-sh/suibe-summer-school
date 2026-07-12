from __future__ import annotations

import re
import unittest
from pathlib import Path


DECK_PATH = Path(__file__).resolve().parent.parent / "lecture2_capital_markets_ai.qmd"
RENDERED_DECK_PATH = DECK_PATH.parent / "_site" / "lecture2_capital_markets_ai.html"
POOLING_CALCULATION = "Pooling price = ½ × 120 + ½ × 60 = 90"
NEW_TITLES = (
    "Adverse Selection Can Drive Good Firms Out",
    "Moral Hazard in Equity: The Principal-Agent Problem",
    "Moral Hazard in Debt: Borrowers May Shift Risk",
)
OLD_TITLES = (
    "Adverse Selection Comes Before Contracting",
    "Moral Hazard Comes After Contracting",
)
OLD_CHAINS = (
    "Before financing -> entrepreneur knows project quality -> investors price the pool -> good projects may withdraw",
    "After financing -> owners can raise risk, underinvest or divert resources -> fixed claim value falls",
)


def slide_body(source: str, title: str) -> str:
    """Return one level-two slide body, stopping at the next slide section."""
    heading = re.compile(rf"^##[ \t]+{re.escape(title)}[ \t]*$", re.MULTILINE)
    match = heading.search(source)
    if match is None:
        raise AssertionError(f"missing slide heading: {title}")
    next_heading = re.search(r"^##[ \t]+.+?[ \t]*$", source[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(source)
    return source[match.end() : end]


def fenced_node_body(source: str, class_name: str) -> str:
    """Return the body of a semantic fenced div carrying ``class_name``."""
    node = re.search(
        rf"^(?P<fence>:{{3,}})\s*\{{[^}}]*\.{re.escape(class_name)}(?:\s|\}})[^}}]*\}}\s*$"
        rf"(?P<body>.*?)^(?P=fence)\s*$",
        source,
        re.MULTILINE | re.DOTALL,
    )
    if node is None:
        raise AssertionError(f"missing semantic node: {class_name}")
    return node.group("body")


class SlideBodyExtractorTest(unittest.TestCase):
    def test_stops_at_next_level_two_section(self) -> None:
        source = "## Target\ninside\n### Child\nstill inside\n## Next\nDO NOT LEAK\n"
        body = slide_body(source, "Target")
        self.assertIn("still inside", body)
        self.assertNotIn("DO NOT LEAK", body)

    def test_matches_title_as_literal_text(self) -> None:
        source = "## Moral Hazard (Debt)?\nbody\n## Other\n"
        self.assertIn("body", slide_body(source, "Moral Hazard (Debt)?"))


class Lecture2AsymmetricInformationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = DECK_PATH.read_text(encoding="utf-8")

    def test_three_replacement_headings_are_present_and_old_headings_are_absent(self) -> None:
        for title in NEW_TITLES:
            self.assertIn(f"## {title}", self.source)
        for title in OLD_TITLES:
            self.assertNotIn(f"## {title}", self.source)

    def test_adverse_selection_slide_locks_worked_example_and_mechanism(self) -> None:
        adverse = slide_body(self.source, NEW_TITLES[0])
        for literal in ("120", "60", "90"):
            self.assertIn(literal, adverse)
        for phrase in ("hidden type", "pooling price", "market unravel"):
            self.assertIn(phrase, adverse.lower())

    def test_pooling_calculation_is_locked_in_source(self) -> None:
        adverse = slide_body(self.source, NEW_TITLES[0])
        self.assertIn(POOLING_CALCULATION, adverse)

    def test_pooling_calculation_is_visible_in_rendered_html(self) -> None:
        rendered = RENDERED_DECK_PATH.read_text(encoding="utf-8")
        self.assertIn(POOLING_CALCULATION, rendered)

    def test_equity_moral_hazard_slide_locks_ownership_example_and_mechanism(self) -> None:
        equity = slide_body(self.source, NEW_TITLES[1])
        for literal in ("9,000", "1,000", "90%", "10%"):
            self.assertIn(literal, equity)
        for phrase in ("principal", "agent", "private benefits"):
            self.assertIn(phrase, equity.lower())

    def test_debt_moral_hazard_slide_locks_risk_shifting_mechanism(self) -> None:
        debt = slide_body(self.source, NEW_TITLES[2])
        self.assertIn("9,000", debt)
        for phrase in (
            "risk shifting",
            "asset substitution",
            "incentive incompatibility",
        ):
            self.assertIn(phrase, debt.lower())

    def test_old_generic_arrow_chains_are_absent(self) -> None:
        for chain in OLD_CHAINS:
            self.assertNotIn(chain, self.source)

    def test_three_asymmetric_information_slides_use_distinct_diagram_wrappers(self) -> None:
        adverse = slide_body(self.source, NEW_TITLES[0])
        equity = slide_body(self.source, NEW_TITLES[1])
        debt = slide_body(self.source, NEW_TITLES[2])
        self.assertIn("asym-diagram asym-unravel", adverse)
        self.assertIn("asym-diagram asym-equity-wedge", equity)
        self.assertIn("asym-diagram asym-debt-fork", debt)

    def assert_semantic_node(self, slide: str, class_name: str, *labels: str) -> None:
        node = fenced_node_body(slide, class_name).lower()
        for label in labels:
            with self.subTest(node=class_name, label=label):
                self.assertIn(label.lower(), node)

    def test_adverse_selection_diagram_locks_unraveling_nodes(self) -> None:
        adverse = slide_body(self.source, NEW_TITLES[0])
        nodes = {
            "asym-pool": ("investor pool",),
            "asym-good-firm": ("good firm", "120"),
            "asym-bad-firm": ("bad firm", "60"),
            "asym-pooling-price": (POOLING_CALCULATION,),
            "asym-good-exit": ("good firm", "exits"),
            "asym-bad-stay": ("bad firm", "stays"),
            "asym-remaining-pool": ("remaining pool", "tends toward 60"),
            "asym-unravel-loop": ("market unraveling",),
        }
        for class_name, labels in nodes.items():
            self.assert_semantic_node(adverse, class_name, *labels)
        self.assert_semantic_node(
            adverse,
            "asym-interrupt",
            "disclosure",
            "screening",
            "signalling",
            "intermediation",
            "collateral",
            "net worth",
        )
        for edge in (
            "good-to-pool", "bad-to-pool", "pool-to-price",
            "price-to-exit", "price-to-stay", "stay-to-remaining",
            "remaining-to-price",
        ):
            self.assertIn(f'asym-edge-{edge}', adverse)

    def test_equity_diagram_locks_ownership_and_incentive_wedge_nodes(self) -> None:
        equity = slide_body(self.source, NEW_TITLES[1])
        nodes = {
            "asym-principal": ("principal", "investor", "9,000", "90%"),
            "asym-agent": ("agent", "manager", "1,000", "10%"),
            "ownership-bar": ("90%", "10%"),
            "asym-hidden-actions": ("hidden action", "effort", "private benefits", "cash reporting"),
            "asym-effort-cost": ("100% of effort cost",),
            "asym-profit-share": ("10% of incremental profit",),
            "asym-behaviour": ("shirk", "consume private benefits", "hide cash"),
        }
        for class_name, labels in nodes.items():
            self.assert_semantic_node(equity, class_name, *labels)
        self.assert_semantic_node(
            equity,
            "asym-governance",
            "managerial ownership",
            "monitoring",
            "auditing",
            "boards",
            "VC control rights",
        )
        for edge in (
            "principal-to-ownership", "agent-to-ownership",
            "ownership-to-hidden", "hidden-to-wedge",
            "wedge-to-behaviour", "governance-to-hidden",
        ):
            self.assertIn(f'asym-edge-{edge}', equity)

    def test_debt_diagram_locks_decision_fork_and_payoff_nodes(self) -> None:
        debt = slide_body(self.source, NEW_TITLES[2])
        nodes = {
            "asym-lender": ("lender", "9,000 loan"),
            "asym-decision": ("post-financing decision",),
            "safe-path": ("operate the store", "predictable cash flow"),
            "risk-path": ("redirect to research", "low probability", "high payoff"),
            "asym-success": ("success", "borrower captures most upside", "principal plus interest"),
            "asym-failure": ("failure", "lender bears much of the downside"),
            "asym-risk-shifting": ("borrower prefers more risk than the lender",),
        }
        for class_name, labels in nodes.items():
            self.assert_semantic_node(debt, class_name, *labels)

        controls_start = debt.find("asym-debt-controls")
        decision_start = debt.find("asym-decision")
        self.assertGreaterEqual(controls_start, 0, "missing asym-debt-controls node")
        self.assertGreaterEqual(decision_start, 0, "missing asym-decision node")
        controls_precede_fork = controls_start < decision_start
        controls_are_inside_fork = "asym-debt-controls" in fenced_node_body(
            debt, "asym-decision"
        )
        self.assertTrue(
            controls_precede_fork or controls_are_inside_fork,
            "debt controls must be before or inside the decision fork",
        )
        self.assert_semantic_node(
            debt,
            "asym-debt-controls",
            "borrower net worth",
            "collateral",
            "use-of-proceeds restrictions",
            "covenants",
            "monitoring",
        )
        for edge in (
            "lender-to-decision", "controls-to-decision",
            "decision-to-safe", "decision-to-risk",
            "safe-to-success", "risk-to-failure",
        ):
            self.assertIn(f'asym-edge-{edge}', debt)


if __name__ == "__main__":
    unittest.main()
