# SlothPlan — the to-do list that does less

My entry for the **Hacktoberfest 2026 Week 3 "Slow and Steady" challenge**:
build something with open-weight models that *rewards laziness*.

Paste a messy to-do dump. A local open-weight model triages it into
**DO TODAY** (max 3 items), **DEFER**, and **DELETE**, with a one-line
reason per item. It rewards laziness by doing the triage you were avoiding:
fewer decisions, scheduled rest, zero guilt. Fully offline, $0, stdlib-only
Python.

## Quick start

```bash
./scripts/download-llamacpp.sh   # llama.cpp binary (MIT), one-time
./scripts/download-model.sh      # Qwen2.5-0.5B-Instruct Q4_K_M (Apache 2.0), ~397 MB, one-time
python3 -m slothplan triage -f sample_todos/messy.txt
```

Or pipe a list on stdin:

```bash
cat my-todos.txt | python3 -m slothplan triage
```

Skip the model entirely (deterministic keyword rules):

```bash
python3 -m slothplan triage --no-llm -f sample_todos/messy.txt
```

## How it works

Deliberately boring architecture, because boring ships:

- **Parsing** (`slothplan/triage.py`, stdlib only): each non-empty line is
  one task; `#` comments and bullet/number/checklist markers are stripped.
- **Judgment** (`slothplan/llm.py`): each task gets one verdict from
  **Qwen2.5-0.5B-Instruct** (Apache 2.0 open weights, Q4_K_M quantized) run
  through the **llama.cpp** binary (MIT). Greedy decoding, ~3s per item on
  two CPU cores. The model emits a single bucket word (`today` / `defer` /
  `delete`) plus a short reason — a shape small enough for a 0.5B model to
  hold reliably. (An earlier prototype asked for one big JSON object; the
  model produced hallucinated item numbers and 12 entries in a 3-item
  bucket. See `notes.md`.)
- **Enforcement** (`slothplan/triage.py`): every verdict is parsed and
  validated. The structural guarantees — at most 3 items in "today", every
  item in exactly one bucket — are enforced by deterministic code, not by
  the model. Verdicts that can't be parsed fall back to transparent keyword
  rules **and are labeled as such in the output**; nothing fails silently.
- **Zero third-party Python dependencies.** If you have Python 3.8 and the
  two downloaded files, it runs. Environment overrides: `SLOTHPLAN_MODEL`,
  `SLOTHPLAN_LLAMACPP`.

## Example

```
=== SLOTHPLAN triage ===
method: local open-weight model Qwen2.5-0.5B-Instruct (Q4_K_M, Apache 2.0)
via llama.cpp (greedy decoding); every verdict parsed and validated,
bucket contract enforced deterministically

DO TODAY (max 3) — your only decisions today:
  2. Reply to Priya about the wedding RSVP — deadline is tomorrow
  ...
DELETE — permission granted, let it go:
  10. Delete that crypto spam email from "DOUBLE YOUR COINS"
  ...
```

The full, unedited transcript of the recorded demo is in `demo-output.txt`.

## Honest limitations

I'd rather tell you than have you discover them:

- The bundled model is **0.5 billion parameters** — tiny on purpose, so it
  runs on any laptop CPU. On the sample list it parsed 12/12 verdicts, but
  its *judgments* are opinionated: on the recorded run it deferred the
  electricity bill ("no deadline, start next month" — for a bill due
  Friday), called buying milk "spam", and deleted "call mom back". The
  deterministic layer (3-item cap, per-item fallback, `--no-llm` mode)
  exists precisely because a tiny model can't be trusted with structure.
  Treat verdicts as suggestions, not orders.
- Reasons are sometimes missing (`(no reason given)`) — the model often
  emits just the bucket word.
- The rule-based fallback is keyword heuristics, not understanding.
- Prototype built in a day for a challenge, not a hardened product.

## Tests

```bash
python3 -m unittest discover -s tests   # 29 tests, all passing
```

Covers item parsing, verdict parsing, fallback bucketing, bucket-contract
enforcement, and rendering.

## Repo layout

```
slothplan/        # __main__ (CLI), llm (model wrapper), triage (logic)
sample_todos/     # messy.txt — the demo input
scripts/          # download-llamacpp.sh, download-model.sh, demo.sh
tests/            # 29 unit tests
README.md  LICENSE (MIT)  .gitignore
demo-output.txt   # recorded real output of scripts/demo.sh (unedited)
dev-post-draft.md # the DEV submission post (for the publishing agent)
notes.md          # builder's log — NOT for publication
```

NOT shipped (local-only, gitignored): `llamacpp/`, `models/`, `__pycache__/`.
The two download scripts recreate them anywhere.

## License

MIT — see LICENSE.
