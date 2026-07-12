#!/usr/bin/env python3
"""Validate the source-level contract for the two summer-school decks."""

from __future__ import annotations

import argparse
import re
from itertools import zip_longest
from pathlib import Path
from urllib.parse import unquote, urlsplit


L1_TITLES = [
    "From Bank Payments to the Financial System",
    "Warm-Up: Diagnose One Payment Failure",
    "One Day in Shanghai, Four Payment Moments",
    "Before Wallets: The Bank-Based Payment System",
    "What Banks Provided—and Which Frictions Remained",
    "What Is a Third-Party Payment Institution?",
    "One Payment, Two Layers: Wallet Interface, Bank Settlement",
    "Escrow Added Trust to Online Transactions",
    "QR Codes and Social Networks Accelerated Adoption",
    "Did Third-Party Payment Expand Payment Inclusion?",
    "From Payment Records to Credit Information",
    "What Third-Party Payment Changed—and What It Did Not Replace",
    "China’s Financial System: Formal, Market and Alternative Channels",
    "A Bank Balance Sheet in One Picture",
    "What Banks Transform—and What Risks They Bear",
    "Why Did China Develop Such a Large Banking System?",
    "Financial-Sector Assets over Time",
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
]

L2_TITLES = [
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

L2_FORBIDDEN_PATTERNS = (
    "Liquidity Depends on Standardisation and Market Design",
    "Formal Exchanges and Split-Share Reform Built the Foundation",
    "Choose the contract for the financing problem",
)

L2_TITLE_METADATA = {
    "title": "From Financial Contracts to Market Information",
    "subtitle": "Bonds, Equity, PE/VC and AI in China’s Financial Development",
    "author": "Xiaoquan Wang",
    "institute": "SUIBE",
    "date": "July 14, 2026",
}
L2_ALLOWED_TOP_LEVEL_METADATA = frozenset((*L2_TITLE_METADATA, "format"))


HEADING_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_ROOT = (PROJECT_ROOT / "assets").resolve()
DECKS = {
    "lecture1": (PROJECT_ROOT / "lecture1_payment_banks.qmd", L1_TITLES),
    "lecture2": (PROJECT_ROOT / "lecture2_capital_markets_ai.qmd", L2_TITLES),
}
FORBIDDEN_PATTERNS_BY_FILENAME = {
    "lecture2_capital_markets_ai.qmd": L2_FORBIDDEN_PATTERNS,
}
MISSING = object()


def _unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _source_parts(source: str) -> tuple[str | None, str]:
    """Return the YAML title and Markdown body after front matter."""
    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, source

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        return None, source

    title = None
    for line in lines[1:closing_index]:
        match = re.match(r"^title\s*:\s*(.*?)\s*$", line)
        if match:
            title = _unquote_yaml_scalar(match.group(1))
            break
    return title, "\n".join(lines[closing_index + 1 :])


def _top_level_front_matter(source: str) -> list[tuple[str, str]]:
    """Return top-level YAML key/value text without interpreting build config."""
    lines = source.splitlines()
    if not lines or lines[0].strip() != "---":
        return []

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        return []

    items: list[tuple[str, str]] = []
    for line in lines[1:closing_index]:
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        quote: str | None = None
        index = 0
        while index < len(line):
            char = line[index]
            if quote == '"':
                if char == "\\":
                    index += 2
                    continue
                if char == quote:
                    quote = None
            elif quote == "'":
                if char == quote and index + 1 < len(line) and line[index + 1] == quote:
                    index += 2
                    continue
                if char == quote:
                    quote = None
            elif char in "\"'":
                quote = char
            elif char == ":":
                raw_key = line[:index].strip()
                if raw_key:
                    items.append(
                        (_unquote_yaml_scalar(raw_key), line[index + 1 :].strip())
                    )
                break
            index += 1
    return items


def _local_image_targets(source: str) -> list[str]:
    targets: list[str] = []
    for match in IMAGE_RE.finditer(source):
        target = match.group(1) or match.group(2)
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith(("//", "#")):
            continue
        targets.append(target)
    return targets


def validate_deck(path: Path, expected_titles: list[str]) -> list[str]:
    """Return contract violations for *path*, or an empty list when valid."""
    source = path.read_text(encoding="utf-8")
    yaml_title, body = _source_parts(source)
    actual_titles = ([yaml_title] if yaml_title is not None else []) + HEADING_RE.findall(body)
    errors: list[str] = []

    if path.name == "lecture2_capital_markets_ai.qmd":
        metadata_items = _top_level_front_matter(source)
        metadata_keys = [key for key, _ in metadata_items]
        unexpected = sorted(set(metadata_keys) - L2_ALLOWED_TOP_LEVEL_METADATA)
        for key in unexpected:
            errors.append(f"title metadata contains unapproved top-level key: {key}")

        for key, expected_value in L2_TITLE_METADATA.items():
            values = [
                _unquote_yaml_scalar(value)
                for actual_key, value in metadata_items
                if actual_key == key
            ]
            if not values:
                errors.append(f"title metadata missing required field: {key}")
            elif len(values) > 1:
                errors.append(f"title metadata duplicates required field: {key}")
            elif values[0] != expected_value:
                errors.append(
                    f"title metadata mismatch for {key}: "
                    f"expected {expected_value!r}, found {values[0]!r}"
                )

    if len(actual_titles) != len(expected_titles):
        errors.append(
            f"wrong count: expected {len(expected_titles)} slides, found {len(actual_titles)}"
        )

    for index, (expected, actual) in enumerate(
        zip_longest(expected_titles, actual_titles, fillvalue=MISSING), start=1
    ):
        if expected != actual:
            if actual is MISSING:
                detail = f"expected {expected!r}, found <missing slide>"
            elif expected is MISSING:
                detail = f"expected <no slide>, found extra {actual!r}"
            else:
                detail = f"expected {expected!r}, found {actual!r}"
            errors.append(f"title mismatch at slide {index}: {detail}")
            break

    if re.search(r"\bappendix\b", source, flags=re.IGNORECASE):
        errors.append("forbidden appendix content")
    if "../work/" in source:
        errors.append("forbidden ../work/ reference")
    if re.search(r"!\[\]\(http", source, flags=re.IGNORECASE):
        errors.append("forbidden remote image syntax ![](http")

    for pattern in FORBIDDEN_PATTERNS_BY_FILENAME.get(path.name, ()):
        if pattern in source:
            errors.append(f"forbidden source pattern: {pattern}")

    for target in _local_image_targets(source):
        filesystem_path = unquote(urlsplit(target).path)
        resolved_path = (path.parent / filesystem_path).resolve()
        if not resolved_path.is_relative_to(ASSETS_ROOT):
            errors.append(f"local asset outside assets directory: {target}")
        elif not resolved_path.is_file():
            errors.append(f"missing local asset: {target}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deck",
        choices=("lecture1", "lecture2", "all"),
        default="all",
        help="deck to validate (default: all)",
    )
    args = parser.parse_args()

    selected = DECKS if args.deck == "all" else {args.deck: DECKS[args.deck]}
    failed = False
    for path, titles in selected.values():
        errors = validate_deck(path, titles)
        print(f"{path.name}:")
        if errors:
            failed = True
            for error in errors:
                print(f"  - {error}")
        else:
            print("  OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
