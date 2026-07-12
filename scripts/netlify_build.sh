#!/usr/bin/env bash
set -euo pipefail

QUARTO_VERSION="${QUARTO_VERSION:-1.6.32}"

if ! command -v quarto >/dev/null 2>&1; then
  case "$(uname -m)" in
    x86_64) QUARTO_ARCH="amd64" ;;
    aarch64|arm64) QUARTO_ARCH="arm64" ;;
    *) echo "Unsupported build architecture: $(uname -m)" >&2; exit 1 ;;
  esac

  QUARTO_ROOT="${TMPDIR:-/tmp}/quarto-${QUARTO_VERSION}"
  QUARTO_ARCHIVE="quarto-${QUARTO_VERSION}-linux-${QUARTO_ARCH}.tar.gz"
  mkdir -p "$QUARTO_ROOT"
  curl --fail --location --silent --show-error \
    "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/${QUARTO_ARCHIVE}" \
    --output "${QUARTO_ROOT}/${QUARTO_ARCHIVE}"
  tar -xzf "${QUARTO_ROOT}/${QUARTO_ARCHIVE}" -C "$QUARTO_ROOT" --strip-components=1
  export PATH="${QUARTO_ROOT}/bin:${PATH}"
fi

command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }
quarto --version
quarto render html_lectures
python3 html_lectures/scripts/audit_rendered_site.py html_lectures/_site
