#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

for expected in 'AI_TRANSLATOR_DOWNLOAD_MODE' '仅显示下载链接' '下载链接：' 'curl -L -C -'; do
    grep -Fq "$expected" "$project_dir/install.sh" || {
        echo "Expected manual download support: $expected"
        exit 1
    }
done

manual_function=$(sed -n '/    show_manual_download() {/,/^    }/p' "$project_dir/install.sh")
output=$(PROJECT_DIR="$project_dir" bash -c "$manual_function; show_manual_download Model model.gguf https://example.invalid/model.gguf")

[[ "$output" == *'https://example.invalid/model.gguf'* && "$output" == *'curl -L -C -'* ]] || {
    echo "Expected the manual download helper to print a URL and resumable curl command."
    exit 1
}
