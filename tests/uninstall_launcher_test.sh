#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

grep -Fq 'AI Translator.app' "$project_dir/uninstall.sh" || {
    echo "Expected uninstaller to remove the macOS app launcher."
    exit 1
}

grep -Fq '*.download-meta.json' "$project_dir/uninstall.sh" || {
    echo "Expected uninstaller model cleanup to remove download metadata."
    exit 1
}
