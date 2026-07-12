import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NetlifyConfigTests(unittest.TestCase):
    def test_netlify_build_is_reproducible_and_scoped(self) -> None:
        config = (ROOT / "netlify.toml").read_text(encoding="utf-8")
        build = (ROOT / "scripts" / "netlify_build.sh").read_text(encoding="utf-8")

        self.assertIn('command = "bash scripts/netlify_build.sh"', config)
        self.assertIn('publish = "html_lectures/_site"', config)
        self.assertIn('QUARTO_VERSION = "1.6.32"', config)
        self.assertIn("set -euo pipefail", build)
        self.assertIn("quarto render html_lectures", build)
        self.assertIn("audit_rendered_site.py html_lectures/_site", build)
        self.assertIn("quarto-${QUARTO_VERSION}-linux-${QUARTO_ARCH}.tar.gz", build)


if __name__ == "__main__":
    unittest.main()
