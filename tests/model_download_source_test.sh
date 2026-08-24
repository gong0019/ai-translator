#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
download_block=$(sed -n '/download_model_file() {/,/^    }/p' "$project_dir/install.sh")

for expected in 'metadata_path' 'model_host' 'etag' '远端模型已变化或来源无法验证'; do
    grep -Fq "$expected" <<<"$download_block" || {
        echo "Expected source-aware partial download validation: $expected"
        exit 1
    }
done
