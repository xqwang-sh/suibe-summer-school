from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from scripts.audit_rendered_site import audit_html, decode_css_data_url


PROJECT_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = PROJECT_DIR / "_site"


class RenderedSiteAuditTests(unittest.TestCase):
    def test_nested_section_inside_top_level_slide_is_rejected(self) -> None:
        html = (
            '<div class="reveal"><div class="slides">'
            '<section id="slide-1"><section class="card">nested</section></section>'
            '</div></div>'
        )
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "deck.html"
            page.write_text(html, encoding="utf-8")
            errors = audit_html(page)

        self.assertTrue(any("nested <section>" in error for error in errors), errors)

    def test_percent_encoded_css_is_decoded_and_remote_import_is_rejected(self) -> None:
        css = '@import"https://fonts.googleapis.com/css?family=Lato"; body { color: #123; }'
        href = "data:text/css," + quote(css, safe="")
        html = f'<link rel="stylesheet" href="{href}">'
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "deck.html"
            page.write_text(html, encoding="utf-8")
            errors = audit_html(page)

        self.assertTrue(any("fonts.googleapis.com" in error for error in errors), errors)

    def test_base64_css_is_decoded_and_relative_import_is_rejected(self) -> None:
        css = '@import"./fonts/source-sans-pro/source-sans-pro.css";'
        payload = base64.b64encode(css.encode("utf-8")).decode("ascii")
        href = f"data:text/css;base64,{payload}"
        self.assertEqual(decode_css_data_url(href), css)
        html = f'<link rel="stylesheet" href="{href}">'
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "deck.html"
            page.write_text(html, encoding="utf-8")
            errors = audit_html(page)

        self.assertTrue(any("source-sans-pro.css" in error for error in errors), errors)

    def test_embedded_or_fragment_css_urls_are_allowed(self) -> None:
        css = (
            '.icon { background-image: url("data:image/svg+xml,%3Csvg/%3E"); }'
            '.mask { filter: url("#mask"); }'
        )
        href = "data:text/css," + quote(css, safe="")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "deck.html"
            page.write_text(
                f'<link rel="stylesheet" href="{href}">', encoding="utf-8"
            )
            self.assertEqual(audit_html(page), [])

    def test_current_rendered_decks_are_css_self_contained(self) -> None:
        html_files = sorted(SITE_DIR.glob("*.html"))
        self.assertEqual(len(html_files), 2)
        errors = [error for path in html_files for error in audit_html(path)]
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
