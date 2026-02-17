#!/usr/bin/env bash
set -e
python ./tools/csk/csk.py bootstrap --apply-candidates || true
python ./tools/csk/csk.py api-sync || true
