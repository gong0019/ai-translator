#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
launcher_function=$(sed -n '/^configure_launchers() {/,/^}/p' "$project_dir/install.sh")
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
desktop_dir="$work_dir/Desktop"
mkdir -p "$desktop_dir"

env \
    OSTYPE=darwin23 \
    PROJECT_DIR="$project_dir" \
    REAL_HOME="$work_dir" \
    REAL_USER="$(id -un)" \
    TEST_DESKTOP="$desktop_dir" \
    CONFIGURE_FUNCTION="$launcher_function" \
    CYAN= GREEN= YELLOW= NC= \
    bash -c '
        get_desktop_dir() { printf "%s\n" "$TEST_DESKTOP"; }
        eval "$CONFIGURE_FUNCTION"
        configure_launchers
    ' <<< $'y\nn\n' >/dev/null

app="$desktop_dir/AI Translator.app"
plist="$app/Contents/Info.plist"
executable="$app/Contents/MacOS/AI Translator"
icon="$app/Contents/Resources/AI-Translator.icns"

test -f "$plist"
test -x "$executable"
test -f "$icon"
grep -Fq '<string>AI Translator</string>' "$plist"
grep -Fq '<string>AI-Translator.icns</string>' "$plist"
grep -Fq "exec /usr/bin/open -a Terminal \"$project_dir/run.sh\"" "$executable"
cmp "$project_dir/assets/icons/AI-Translator.icns" "$icon"
