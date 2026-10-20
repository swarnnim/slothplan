"""Triage logic: item parsing, verdict parsing/validation, the
deterministic rule-based fallback, and output rendering.

Honesty rule: the model's per-item verdict is parsed and validated. When
a verdict can't be parsed (or the model can't run at all), that item falls
back to transparent keyword rules — and the output SAYS SO, per item and
in the method note. Nothing is silently guessed.
"""

import re

MAX_ITEMS = 24
TODAY_CAP = 3

BUCKETS = ("today", "defer", "delete")

# --- item parsing -----------------------------------------------------------

_BULLET_RE = re.compile(
    r"^\s*(?:(?:[-*•–—]|\d{1,2}[.)]|\([a-z0-9x ]{1,2}\)|\[[ xX]\])\s+)+"
)


def parse_items(text):
    """Turn a messy to-do dump into a clean list of task strings.

    Each non-empty line is one task; `#` comment lines and leading
    bullet/number/checklist markers are stripped. Returns a list of strings.
    """
    items = []
    for line in text.splitlines():
        if line.strip().startswith("#"):
            # Comment lines are notes about the dump, not tasks.
            continue
        line = _BULLET_RE.sub("", line).strip()
        if line:
            items.append(line)
    return items


def number_items(items):
    """Pair tasks with 1-based numbers as shown to the user."""
    return list(enumerate(items, start=1))


# --- verdict parsing ---------------------------------------------------------

_VERDICT_RE = re.compile(r"^\s*([A-Za-z]+)\b\s*(.*)$", re.DOTALL)
_PAREN_RE = re.compile(r"\(\s*(.*?)\s*\)")


def parse_verdict(reply):
    """Parse one model reply into (bucket, reason) or return None.

    Accepted shape: a bucket word (today/defer/delete, case-insensitive)
    followed by a short reason, ideally in parentheses. The reason may be
    missing (placeholder is used) but the bucket word must be exact —
    anything else means the verdict is unparseable and the caller must
    fall back for that item.
    """
    m = _VERDICT_RE.match(reply.strip())
    if not m:
        return None
    word = m.group(1).lower()
    if word not in BUCKETS:
        return None
    rest = m.group(2).strip()
    pm = _PAREN_RE.search(rest)
    if pm:
        reason = pm.group(1).strip()
    else:
        reason = rest.lstrip("-–—:,.; ").strip()
    if not reason:
        reason = "(no reason given)"
    return word, reason


# --- deterministic rule-based fallback --------------------------------------

URGENT_RE = re.compile(
    r"\b(due|deadline|tonight|tomorrow|today|urgent|asap|expires?|"
    r"expiring|interview|exam|submit|overdue|bill|payment|\bpay\b|"
    r"called twice|appointment|wedding|rsvp)\b",
    re.IGNORECASE,
)

DELETE_RE = re.compile(
    r"\b(spam|crypto|junk|obsolete|watchlist|netflix|scam|"
    r"unsubscribe|delete me)\b",
    re.IGNORECASE,
)


def fallback_bucket(text):
    """Deterministic per-item keyword triage. Returns (bucket, reason)."""
    if DELETE_RE.search(text) and not URGENT_RE.search(text):
        return "delete", "matches a junk pattern — nothing of value is lost"
    if URGENT_RE.search(text):
        return ("today",
                "looks time-sensitive — it names a deadline, payment, "
                "or an urgent event")
    return "defer", "not urgent — it keeps just fine until another day"


# --- merging verdicts into the bucket contract --------------------------------


def merge_verdicts(verdicts, numbered_tasks):
    """Enforce the bucket contract over per-item verdicts.

    verdicts: list of (bucket, reason, used_fallback) aligned with
    numbered_tasks. Returns (result, n_fallback) where result maps each
    bucket to a list of (n, reason). The TODAY_CAP is enforced in original
    order; overflow 'today' verdicts are moved to 'defer' with a note.
    """
    result = {b: [] for b in BUCKETS}
    today_left = TODAY_CAP
    n_fallback = 0
    for (n, _text), (bucket, reason, used_fallback) in zip(
            numbered_tasks, verdicts):
        if used_fallback:
            n_fallback += 1
            reason = f"{reason} [rule-based fallback — model's verdict for "\
                     "this item could not be used]"
        if bucket == "today":
            if today_left > 0:
                result["today"].append((n, reason))
                today_left -= 1
            else:
                result["defer"].append(
                    (n, f"{reason} [moved from today: the {TODAY_CAP}-item "
                        "cap keeps your day lazy]"))
        else:
            result[bucket].append((n, reason))
    return result, n_fallback


# --- rendering --------------------------------------------------------------


def render(result, tasks, method_note):
    """Render the triage into human-readable text."""
    lines = [
        "=== SLOTHPLAN triage ===",
        f"method: {method_note}",
        "",
        f"DO TODAY (max {TODAY_CAP}) — your only decisions today:",
    ]
    if result["today"]:
        for n, reason in result["today"]:
            lines.append(f"  {n}. {tasks[n-1]}")
            lines.append(f"     -> {reason}")
    else:
        lines.append("  (nothing — a truly sloth day)")
    lines += ["", "DEFER — officially not today's problem:"]
    if result["defer"]:
        for n, reason in result["defer"]:
            lines.append(f"  {n}. {tasks[n-1]}")
            lines.append(f"     -> {reason}")
    else:
        lines.append("  (nothing)")
    lines += ["", "DELETE — permission granted, let it go:"]
    if result["delete"]:
        for n, reason in result["delete"]:
            lines.append(f"  {n}. {tasks[n-1]}")
            lines.append(f"     -> {reason}")
    else:
        lines.append("  (nothing)")
    lines += ["",
              "Everything deferred is still on your list, just not on "
              "today's. Go be a sloth."]
    return "\n".join(lines)
