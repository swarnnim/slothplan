#!/bin/bash
# Recorded demo: triage the sample messy to-do dump. Output is saved to
# demo-output.txt EXACTLY as produced — do not edit the file afterwards.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="demo-output.txt"
: > "$OUT"
{
  echo "=== SlothPlan demo — $(date -u '+%Y-%m-%d %H:%M UTC') ==="
  echo "Model: Qwen2.5-0.5B-Instruct (Q4_K_M, open weights, Apache 2.0)"
  echo "Engine: llama.cpp (MIT). 100% local, greedy decoding."
  echo "Input: sample_todos/messy.txt (12 items)"
  echo ""
  echo "--- run 1: full triage with the local model ---"
  python3 -m slothplan triage -f sample_todos/messy.txt
  echo ""
  echo "--- run 2: deterministic rule-based fallback (--no-llm) ---"
  python3 -m slothplan triage --no-llm -f sample_todos/messy.txt
} 2>&1 | tee "$OUT"
echo ""
echo "Demo saved to $OUT"
