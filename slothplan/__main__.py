"""Command-line interface for SlothPlan."""

import argparse
import sys

from . import __version__
from .llm import ask_verdict
from .triage import (
    MAX_ITEMS, fallback_bucket, merge_verdicts, number_items, parse_items,
    parse_verdict, render,
)


def verdict_for_item(text, args):
    """Return (bucket, reason, used_fallback) for one task."""
    try:
        reply = ask_verdict(
            text, model_path=args.model, cli_path=args.llamacpp,
            max_tokens=args.max_tokens, threads=args.threads)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"[model unavailable for one item: {e}]", file=sys.stderr)
        bucket, reason = fallback_bucket(text)
        return bucket, reason, True
    parsed = parse_verdict(reply)
    if parsed is None:
        bucket, reason = fallback_bucket(text)
        return bucket, reason, True
    return parsed[0], parsed[1], False


def cmd_triage(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            text = fh.read()
    else:
        if sys.stdin.isatty():
            print("error: provide a to-do list with -f FILE or pipe it on stdin.",
                  file=sys.stderr)
            return 1
        text = sys.stdin.read()

    items = parse_items(text)
    if not items:
        print("error: no to-do items found in the input.", file=sys.stderr)
        return 1
    if len(items) > MAX_ITEMS:
        print(f"note: keeping the first {MAX_ITEMS} of {len(items)} items.",
              file=sys.stderr)
        items = items[:MAX_ITEMS]
    numbered = number_items(items)

    if args.no_llm:
        verdicts = [fallback_bucket(t) + (False,) for _, t in numbered]
        result, _ = merge_verdicts(verdicts, numbered)
        print(render(
            result, items,
            method_note="rule-based fallback (--no-llm was passed; "
                        "no model was run)"))
        return 0

    verdicts = []
    for i, (n, t) in enumerate(numbered, start=1):
        print(f"[{i}/{len(numbered)}] triaging: {t[:60]}",
              file=sys.stderr)
        verdicts.append(verdict_for_item(t, args))

    result, n_fallback = merge_verdicts(verdicts, numbered)
    if n_fallback:
        method_note = (
            "local open-weight model Qwen2.5-0.5B-Instruct (Q4_K_M, Apache "
            "2.0) via llama.cpp (greedy decoding); verdicts parsed and "
            f"validated — {n_fallback} of {len(numbered)} item(s) fell back "
            "to rule-based triage and are marked above")
    else:
        method_note = (
            "local open-weight model Qwen2.5-0.5B-Instruct (Q4_K_M, Apache "
            "2.0) via llama.cpp (greedy decoding); every verdict parsed "
            "and validated, bucket contract enforced deterministically")
    print(render(result, items, method_note=method_note))
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="slothplan",
        description=("SlothPlan — the to-do list that does less. "
                     "Triage a messy to-do dump into today (max 3), "
                     "defer, and delete, locally, with an open-weight model."),
    )
    p.add_argument("--version", action="version",
                   version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("triage", help="triage a to-do list")
    t.add_argument("-f", "--file", metavar="FILE",
                   help="text file with one to-do per line "
                        "(default: read from stdin)")
    t.add_argument("--no-llm", action="store_true",
                   help="skip the model and use only the rule-based triage")
    t.add_argument("--model", metavar="PATH",
                   help="GGUF model file (overrides SLOTHPLAN_MODEL / "
                        "built-in default)")
    t.add_argument("--llamacpp", metavar="PATH",
                   help="llama-cli binary (overrides SLOTHPLAN_LLAMACPP / "
                        "built-in default)")
    t.add_argument("--max-tokens", type=int, default=60)
    t.add_argument("--threads", type=int, default=2)
    t.set_defaults(func=cmd_triage)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
