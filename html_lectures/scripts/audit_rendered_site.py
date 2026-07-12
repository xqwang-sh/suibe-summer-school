"""Audit rendered HTML for CSS dependencies that break self-containment."""

from __future__ import annotations

import argparse
import base64
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote_to_bytes


CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
CSS_IMPORT = re.compile(
    r"@import\s*(?:url\(\s*)?(?P<quote>['\"]?)(?P<target>[^'\"\s);]+)(?P=quote)",
    re.IGNORECASE,
)
CSS_URL = re.compile(
    r"url\(\s*(?P<quote>['\"]?)(?P<target>[^'\")]+)(?P=quote)\s*\)",
    re.IGNORECASE,
)


def decode_css_data_url(url: str) -> str:
    """Return decoded UTF-8 CSS from a ``data:text/css`` URL."""
    header, separator, payload = url.partition(",")
    if not separator or not header.lower().startswith("data:text/css"):
        raise ValueError("not a data:text/css URL")
    parameters = [item.lower() for item in header.split(";")[1:]]
    raw = base64.b64decode(payload, validate=True) if "base64" in parameters else unquote_to_bytes(payload)
    return raw.decode("utf-8")


def _is_embedded(target: str) -> bool:
    normalized = target.strip()
    return normalized.startswith("#") or normalized.lower().startswith("data:")


def _audit_css(css: str, location: str) -> list[str]:
    clean = CSS_COMMENT.sub("", css)
    errors: list[str] = []
    imports = list(CSS_IMPORT.finditer(clean))
    for match in imports:
        target = match.group("target").strip()
        if not _is_embedded(target):
            errors.append(f"{location}: non-embedded CSS @import: {target}")
        elif target.lower().startswith("data:text/css"):
            try:
                errors.extend(_audit_css(decode_css_data_url(target), f"{location} nested data CSS"))
            except (ValueError, UnicodeDecodeError) as exc:
                errors.append(f"{location}: invalid data:text/css @import: {exc}")

    import_spans = [match.span() for match in imports]
    for match in CSS_URL.finditer(clean):
        if any(start <= match.start() < end for start, end in import_spans):
            continue
        target = match.group("target").strip()
        if not _is_embedded(target):
            errors.append(f"{location}: non-embedded CSS url(): {target}")
    return errors


class _RenderedHTMLParser(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.errors: list[str] = []
        self._in_style = False
        self._style_parts: list[str] = []
        self._style_number = 0
        self._tag_stack: list[str] = []
        self._slides_container_depth: int | None = None
        self._slide_section_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if tag == "div" and "slides" in classes and self._slides_container_depth is None:
            self._slides_container_depth = len(self._tag_stack)
        elif tag == "section" and self._slides_container_depth is not None:
            if self._slide_section_depth:
                section_id = attributes.get("id") or "(no id)"
                self.errors.append(
                    f"{self.path}: nested <section> inside a top-level Reveal slide: {section_id}"
                )
            self._slide_section_depth += 1
        if tag == "style":
            self._in_style = True
            self._style_parts = []
        if tag == "link" and "stylesheet" in (attributes.get("rel") or "").lower().split():
            href = attributes.get("href") or ""
            if href.lower().startswith("data:text/css"):
                try:
                    css = decode_css_data_url(href)
                except (ValueError, UnicodeDecodeError) as exc:
                    self.errors.append(f"{self.path}: invalid data:text/css stylesheet: {exc}")
                else:
                    self.errors.extend(_audit_css(css, f"{self.path} data stylesheet"))
            elif not _is_embedded(href):
                self.errors.append(f"{self.path}: non-embedded stylesheet link: {href}")
        self._tag_stack.append(tag)

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self._style_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "style" and self._in_style:
            self._style_number += 1
            self.errors.extend(
                _audit_css("".join(self._style_parts), f"{self.path} style #{self._style_number}")
            )
            self._in_style = False
            self._style_parts = []
        if tag == "section" and self._slides_container_depth is not None:
            self._slide_section_depth = max(0, self._slide_section_depth - 1)
        if (
            tag == "div"
            and self._slides_container_depth is not None
            and len(self._tag_stack) - 1 == self._slides_container_depth
        ):
            self._slides_container_depth = None
            self._slide_section_depth = 0
        if self._tag_stack:
            self._tag_stack.pop()


def audit_html(path: Path) -> list[str]:
    """Return every self-containment violation found in one rendered HTML file."""
    parser = _RenderedHTMLParser(path)
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser.errors


def _html_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(path.glob("*.html")) if path.is_dir() else [path])
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    files = _html_files(args.paths)
    errors = [error for path in files for error in audit_html(path)]
    if not files:
        print("no HTML files found")
        return 1
    if errors:
        print("\n".join(errors))
        return 1
    print(f"rendered-site audit: OK ({len(files)} HTML files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
