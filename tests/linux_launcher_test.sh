#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
launcher_function=$(sed -n '/^configure_launchers() {/,/^}/p' "$project_dir/install.sh")
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
desktop_dir="$work_dir/Desktop"
mkdir -p "$desktop_dir"

env \
    OSTYPE=linux-gnu \
    PROJECT_DIR="$project_dir" \
    REAL_HOME="$work_dir" \
    REAL_USER="$(id -un)" \
    TEST_DESKTOP="$desktop_dir" \
    CONFIGURE_FUNCTION="$launcher_function" \
    CYAN= GREEN= YELLOW= NC= \
    bash -c '
        get_desktop_dir() { printf "%s\n" "$TEST_DESKTOP"; }
        gio() { return 0; }
        eval "$CONFIGURE_FUNCTION"
        configure_launchers
    ' <<< $'y\nn\n' >/dev/null

launcher="$desktop_dir/AI-Translator.desktop"
test -x "$launcher"
grep -Fq "Exec=\"$project_dir/run.sh\"" "$launcher"
grep -Fq "Icon=$project_dir/assets/icons/AI-Translator.png" "$launcher"
grep -Fq 'Terminal=true' "$launcher"

if grep -Fq 'gnome-terminal' "$launcher"; then
    echo 'Linux launcher must use the desktop environment terminal instead of requiring GNOME Terminal.'
    exit 1
fi
