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

grep -Fq '默认保留，下次安装可直接复用' "$project_dir/uninstall.sh" || {
    echo "Expected the model-removal prompt to state that models are retained by default."
    exit 1
}

grep -Fq 'read -r -p "是否删除 models/' "$project_dir/uninstall.sh" || {
    echo "Expected an explicit, robust model-retention prompt."
    exit 1
}
