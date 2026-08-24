#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
selection_block=$(sed -n '/select_and_download_models() {/,/^}/p' "$project_dir/install.sh")

grep -Fq 'prompt_for_models()' <<<"$selection_block" || {
    echo "Expected a built-in Bash model selection prompt."
    exit 1
}

grep -Fq 'read -r' <<<"$selection_block" || {
    echo "Expected model selection to accept terminal input."
    exit 1
}

grep -Fq 'tencent/Hy-MT2-1.8B-GGUF' "$project_dir/install.sh" || {
    echo "Expected the official Hy-MT2 GGUF repository to be offered."
    exit 1
}

if rg -n 'whiptail|newt|libnewt' "$project_dir/install.sh" >/dev/null; then
    echo "Model selection must not require whiptail or newt packages."
    exit 1
fi

prompt_function=$(sed -n '/    prompt_for_models() {/,/^    }/p' "$project_dir/install.sh")
selected=$(printf '1,4\n' | bash -c "$prompt_function; prompt_for_models; printf '%s' \"\$SELECTED_MODELS\"")

if [[ "$selected" != *'"3B" "HYMT"'* ]]; then
    echo "Expected menu input 1,4 to select Qwen 3B and Hy-MT2."
    exit 1
fi

selected=$(printf '1，4\n' | bash -c "$prompt_function; prompt_for_models; printf '%s' \"\$SELECTED_MODELS\"")

if [[ "$selected" != *'"3B" "HYMT"'* ]]; then
    echo "Expected full-width comma input 1，4 to select Qwen 3B and Hy-MT2."
    exit 1
fi
