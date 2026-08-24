#!/bin/bash
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
    LINK_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    if [[ "$SOURCE" != /* ]]; then
        SOURCE="$LINK_DIR/$SOURCE"
    fi
done
DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
cd "$DIR"

# 优先使用项目独立虚拟环境
if [ -f "$DIR/.venv/bin/python3" ]; then
    PYTHON_EXEC="$DIR/.venv/bin/python3"
elif [ -f "$DIR/venv/bin/python3" ]; then
    PYTHON_EXEC="$DIR/venv/bin/python3"
else
    PYTHON_EXEC="python3"
fi

exec "$PYTHON_EXEC" "$DIR/translator_cli.py" "$@"
