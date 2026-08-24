#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

grep -Fq "f'{fpath}.download-meta.json'" "$project_dir/translator_cli.py" || {
    echo "Expected model scanning to skip downloads marked in progress."
    exit 1
}

for expected in 'AI Translator.app' 'Contents/Resources' 'AI-Translator.icns' 'CFBundlePackageType' 'CFBundleIconFile'; do
    grep -Fq "$expected" "$project_dir/install.sh" || {
        echo "Expected a standard macOS app bundle: $expected"
        exit 1
    }
done

grep -Fq 'exec /usr/bin/open -a Terminal' "$project_dir/install.sh" || {
    echo "Expected the macOS app launcher to open the terminal-based UI in Terminal."
    exit 1
}
