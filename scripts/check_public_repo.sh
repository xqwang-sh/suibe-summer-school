#!/usr/bin/env bash
set -euo pipefail

required=(
  "html_lectures/_quarto.yml"
  "html_lectures/styles.scss"
  "html_lectures/lecture1_payment_banks.qmd"
  "html_lectures/lecture2_capital_markets_ai.qmd"
  "docs/superpowers/specs/2026-07-12-course-site-deployment-design.md"
)

tracked="$(git ls-files)"
failed=0

for path in "${required[@]}"; do
  if ! grep -Fxq "$path" <<<"$tracked"; then
    echo "missing required tracked file: $path" >&2
    failed=1
  fi
done

forbidden='(^|/)(\.DS_Store|__pycache__|qa_screenshots[^/]*|tmp|work)(/|$)|_site\.zip$|\.pptx$|\.inspect\.ndjson$'
if grep -E "$forbidden" <<<"$tracked"; then
  echo "forbidden public path is tracked" >&2
  failed=1
fi

if [[ -n "$tracked" ]] && git grep -IEn \
  '(-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|github_pat_[A-Za-z0-9_]+|gh[oprsu]_[A-Za-z0-9]{20,}|NETLIFY_AUTH_TOKEN[[:space:]]*=)' \
  -- $(git ls-files) >/tmp/suibe-public-secret-scan.txt; then
  cat /tmp/suibe-public-secret-scan.txt >&2
  echo "possible credential found in tracked content" >&2
  failed=1
fi

exit "$failed"
