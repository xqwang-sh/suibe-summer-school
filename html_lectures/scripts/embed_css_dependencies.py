"""Remove non-embedded CSS imports from Quarto's embedded stylesheets.

Quarto 1.6 adds font imports even when a custom Reveal theme selects a system
font stack.  The rendered deck does not use those fonts, so the post-render
step removes only non-embedded ``@import`` rules from data-URI stylesheets.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import quote

try:
    from .audit_rendered_site import decode_css_data_url
except ImportError:  # Direct ``python scripts/...`` execution.
    from audit_rendered_site import decode_css_data_url


DATA_CSS_HREF = re.compile(
    r"(?P<prefix>\bhref\s*=\s*)(?P<quote>['\"])(?P<url>data:text/css[^'\"]*)(?P=quote)",
    re.IGNORECASE,
)
IMPORT_RULE = re.compile(
    r"@import\s*(?:url\(\s*)?(?P<quote>['\"]?)(?P<target>[^'\"\s);]+)"
    r"(?P=quote)\s*\)?\s*;?",
    re.IGNORECASE,
)


def _remove_nonembedded_imports(css: str) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target").strip().lower()
        return match.group(0) if target.startswith("data:") or target.startswith("#") else ""

    return IMPORT_RULE.sub(replace, css)


def rewrite_html(path: Path) -> bool:
    """Rewrite one HTML file and return whether any CSS import was removed."""
    original = path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        css = decode_css_data_url(match.group("url"))
        clean = _remove_nonembedded_imports(css)
        if clean == css:
            return match.group(0)
        encoded = "data:text/css," + quote(clean, safe="")
        delimiter = match.group("quote")
        return f"{match.group('prefix')}{delimiter}{encoded}{delimiter}"

    rendered = DATA_CSS_HREF.sub(replace, original)
    if rendered == original:
        return False
    path.write_text(rendered, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    args = parser.parse_args(argv)
    files = sorted(args.site.glob("*.html"))
    if not files:
        print(f"no HTML files found in {args.site}")
        return 1
    changed = sum(rewrite_html(path) for path in files)
    print(f"embedded CSS dependencies normalized: {changed}/{len(files)} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
