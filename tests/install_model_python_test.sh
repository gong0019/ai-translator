#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
download_block=$(sed -n '/download_model_file() {/,/^    }/p' "$project_dir/install.sh")

if ! grep -Fq '.venv/bin/python3 -c "' <<<"$download_block"; then
    echo "Expected model downloader to use the project virtual environment Python."
    exit 1
fi

if grep -Eq '^[[:space:]]*python3 -c "' <<<"$download_block"; then
    echo "Model downloader must not use the system python3 interpreter."
    exit 1
fi
