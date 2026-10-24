#!/usr/bin/env bash
# Extraction on the script text (reference condition): every route and model, both languages.
# Usage, from code/voice-form:  bash eval/run_extract_all.sh tune   (or heldout)
# The fix set is frozen before a held-out run; a later fix means a new round with both sets re-run.
set -u
SET="${1:-tune}"
PY="${PY:-python}"
for L in mr hi; do
  "$PY" -u -m voiceform eval-extract --lang "$L" --route rules --set "$SET"
  "$PY" -u -m voiceform eval-extract --lang "$L" --route direct --model qwen/qwen3-1.7b --set "$SET"
  "$PY" -u -m voiceform eval-extract --lang "$L" --route direct --model gemma-2-2b-it --set "$SET"
  "$PY" -u -m voiceform eval-extract --lang "$L" --route translate --model qwen/qwen3-1.7b --set "$SET"
done
