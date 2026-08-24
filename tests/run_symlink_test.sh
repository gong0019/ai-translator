#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
link_dir=$(mktemp -d /private/tmp/ai-translator-run-link.XXXXXX)
link_path="$link_dir/ai-trans"
ln -s "$project_dir/run.sh" "$link_path"

trace=$(bash -x "$link_path" 2>&1 || true)

if [[ "$trace" != *"cd $project_dir"* ]]; then
    echo "Expected a symlinked global command to resolve the project directory."
    exit 1
fi
