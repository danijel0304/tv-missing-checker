#!/usr/bin/env bash

set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Greška: Python 3 nije instaliran." >&2
    exit 1
fi

cd "$APP_DIR"
exec python3 app.py
