from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

from scripts.audit_rendered_site import audit_html, decode_css_data_url
from scripts.embed_css_dependencies import rewrite_html


class EmbedCSSDependenciesTests(unittest.TestCase):
    def test_rewrite_removes_remote_and_relative_imports_from_data_stylesheet(self) -> None:
        css = (
            '@import"https://fonts.googleapis.com/css?family=Lato";'
            '@import"./fonts/source-sans-pro/source-sans-pro.css";'
            'body{font-family:Aptos,Arial,sans-serif;background:url("data:image/svg+xml,x")}'
        )
        href = "data:text/css," + quote(css, safe="")
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "deck.html"
            page.write_text(
                f'<link rel="stylesheet" href="{href}">', encoding="utf-8"
            )
            self.assertTrue(rewrite_html(page))
            self.assertEqual(audit_html(page), [])
            rendered = page.read_text(encoding="utf-8")

        start = rendered.index("data:text/css")
        encoded = rendered[start:rendered.index('"', start)]
        decoded = decode_css_data_url(encoded)
        self.assertNotIn("@import", decoded)
        self.assertIn("font-family:Aptos", decoded)
        self.assertIn("data:image/svg+xml", decoded)

    def test_rewrite_leaves_clean_stylesheet_byte_identical(self) -> None:
        href = "data:text/css," + quote("body{color:%23172132}", safe="")
        html = f'<link rel="stylesheet" href="{href}">'
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "deck.html"
            page.write_text(html, encoding="utf-8")
            self.assertFalse(rewrite_html(page))
            self.assertEqual(page.read_text(encoding="utf-8"), html)


if __name__ == "__main__":
    unittest.main()
