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

grep -Fq "metadata.get('model_host') != model_host" <<<"$download_block" || {
    echo "Expected a changed download node to invalidate the partial file."
    exit 1
}

if grep -Fq '跨下载节点断点续传' <<<"$download_block"; then
    echo "Must not resume a partial file after changing download nodes."
    exit 1
fi

grep -Fq 'except KeyboardInterrupt:' <<<"$download_block" || {
    echo "Expected Ctrl+C to stop model download without a traceback."
    exit 1
}
