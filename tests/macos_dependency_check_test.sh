#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
dependency_function=$(sed -n '/^install_system_dependencies() {/,/^}/p' "$project_dir/install.sh")
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT

{
    printf '%s\n' 'OSTYPE=darwin23'
    printf '%s\n' 'which() { [ "$1" = brew ]; }'
    printf '%s\n' 'brew() { printf "%s\\n" "$*" >> "'"$work_dir"'/brew.log"; return 0; }'
    printf '%s\n' "$dependency_function"
    printf '%s\n' 'install_system_dependencies'
} | bash >/dev/null

if grep -Fq 'install ' "$work_dir/brew.log" 2>/dev/null; then
    echo 'Homebrew must not install or update packages when all dependencies are already available.'
    exit 1
fi
