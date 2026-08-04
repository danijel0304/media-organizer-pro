#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/media_organizer_pro"
exec python3 media_organizer_pro.py
