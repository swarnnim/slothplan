"""Thin wrapper around the llama.cpp `llama-cli` binary.

The open-weight model (Qwen2.5-0.5B-Instruct GGUF, Apache 2.0) and the
llama.cpp binary (MIT) both live on the user's machine. This module runs
one single-turn greedy generation per task and returns the model's raw
verdict text; the caller parses and validates it.

DESIGN NOTE (discovered by testing, 2026-10-20): the first prototype asked
the 0.5B model to emit one JSON object covering all tasks at once. It
produced almost-valid JSON — but with unterminated strings, hallucinated
item numbers (13-20 for a 12-item list), 12 entries in a 3-item bucket,
and duplicate assignments. Two raw failed replies are quoted in notes.md.
So the model now judges ONE task at a time (a single bucket word + a short
reason — a shape a 0.5B model can hold), and the structural guarantees
(max 3 in 'today', every item assigned exactly once) are enforced by
deterministic code in triage.py.
"""

import os
import shutil
import subprocess

SYSTEM_PROMPT = (
    "You are a task triager. For each task you receive, reply with exactly "
    "one bucket word first — today, defer, or delete — then one short "
    "reason in parentheses. Example: defer (no deadline, start next month). "
    "Use 'today' only for urgent or time-sensitive tasks with a near "
    "deadline. Use 'defer' for worthwhile tasks that can wait. Use "
    "'delete' sparingly — only for junk like spam, scams, or pointless "
    "chores that are not worth doing at all. Real obligations (bills, "
    "deadlines, appointments, messages to real people, groceries) are "
    "NEVER delete. "
    "Reply with the bucket word and the reason only — no other text."
)

# Anchor line that ends the user message; the model's reply begins after it.
ANCHOR = "VERDICT:"


def default_cli_path():
    """Locate the llama-cli binary: explicit env var, then the repo's
    llamacpp dir, then PATH."""
    env = os.environ.get("SLOTHPLAN_LLAMACPP")
    if env and os.path.isfile(env):
        return env
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for cand in (
        os.path.join(here, "llamacpp", "llama-b11580", "llama-cli"),
        os.path.join(here, "llamacpp", "llama-cli"),
    ):
        if os.path.isfile(cand):
            return cand
    found = shutil.which("llama-cli")
    if found:
        return found
    raise FileNotFoundError(
        "llama-cli not found. Run scripts/download-llamacpp.sh, set "
        "SLOTHPLAN_LLAMACPP, or put llama-cli on PATH."
    )


def default_model_path():
    env = os.environ.get("SLOTHPLAN_MODEL")
    if env and os.path.isfile(env):
        return env
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local = os.path.join(here, "models", "qwen2.5-0.5b-instruct-q4_k_m.gguf")
    if os.path.isfile(local):
        return local
    raise FileNotFoundError(
        "Model not found. Run scripts/download-model.sh or set SLOTHPLAN_MODEL."
    )


def build_user_message(task):
    # One-shot examples: tiny models follow demonstrated shapes far better
    # than instructions alone.
    return (
        "EXAMPLE TASK: Fix the roof before the monsoon\n"
        "EXAMPLE VERDICT: today (the roof leaks every time it rains)\n"
        "EXAMPLE TASK: Learn Italian someday\n"
        "EXAMPLE VERDICT: defer (no deadline, start next month)\n"
        "EXAMPLE TASK: Reply to that crypto giveaway spam\n"
        "EXAMPLE VERDICT: delete (it's spam, nothing of value is lost)\n\n"
        f"TASK: {task}\n{ANCHOR}"
    )


def extract_reply(cli_output):
    """Pull the generated text out of llama-cli's stdout.

    With --no-display-prompt the prompt is not echoed, so stdout is the
    reply followed by the '[ Prompt:' timings line. If an echo is present,
    the reply begins on the line after the ANCHOR line (or a truncation
    marker, or the last '> ' line).
    """
    lines = cli_output.splitlines()
    anchor = None
    for i, line in enumerate(lines):
        if line.strip() == ANCHOR:
            anchor = i
    if anchor is None:
        for i, line in enumerate(lines):
            if "(truncated)" in line:
                anchor = i
    if anchor is None:
        for i, line in enumerate(lines):
            if line.startswith("> "):
                anchor = i
    if anchor is None:
        anchor = -1
    collected = []
    for line in lines[anchor + 1:]:
        if line.startswith("[ Prompt:"):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def ask_verdict(task, model_path=None, cli_path=None,
                max_tokens=60, threads=2, ctx_size=1024, temperature=0.0,
                timeout=300):
    """Get one triage verdict for a single task. Returns the reply text."""
    model_path = model_path or default_model_path()
    cli_path = cli_path or default_cli_path()
    cmd = [
        cli_path,
        "-m", model_path,
        "-sys", SYSTEM_PROMPT,
        "--prompt", build_user_message(task),
        "-n", str(max_tokens),
        "-t", str(threads),
        "-c", str(ctx_size),
        "--temp", str(temperature),
        "--no-display-prompt",
        "-st",  # single turn, then exit (no interactive mode)
    ]
    env = dict(os.environ)
    cli_dir = os.path.dirname(cli_path)
    env["LD_LIBRARY_PATH"] = cli_dir + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=timeout, env=env)
    if proc.returncode != 0:
        raise RuntimeError(
            f"llama-cli failed (exit {proc.returncode}): {proc.stderr[-2000:]}"
        )
    reply = extract_reply(proc.stdout)
    if not reply:
        raise RuntimeError("llama-cli produced no reply text.")
    return reply
