#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
network_function=$(sed -n '/^detect_network_region() {/,/^}/p' "$project_dir/install.sh")

run_configuration() {
    local source="$1"
    {
        printf '%s\n' "$network_function"
        printf '%s\n' 'detect_network_region'
        printf '%s\n' 'printf "RESULT:%s|%s|%s\\n" "$MODEL_HOST" "${HTTPS_PROXY-unset}" "$PIP_INDEX"'
    } | env AI_TRANSLATOR_NETWORK_SOURCE="$source" HTTPS_PROXY="http://127.0.0.1:7890" bash
}

domestic=$(run_configuration domestic)
[[ "$domestic" == *'RESULT:https://hf-mirror.com|unset|-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com'* ]] || {
    echo "Domestic selection must use HF-Mirror, Aliyun PyPI, and clear the proxy."
    exit 1
}

international=$(run_configuration international)
[[ "$international" == *'RESULT:https://huggingface.co|unset|'* ]] || {
    echo "International selection must use Hugging Face directly and clear the proxy."
    exit 1
}
