# SlothPlan: the to-do list that does less

*My entry for the Hacktoberfest Week 3 "Slow and Steady" challenge — built for International Sloth Day, with open-weight models, zero API costs, and a philosophy I'd actually live by.*

## The problem

My to-do list has 47 items. Yours probably does too. And here's the dirty secret of productivity culture: the list isn't the work. *Triaging* the list is the work — the staring, the re-ordering, the guilt-math of "is learning Spanish more important than calling the dentist?" I have spent entire Sunday mornings reorganizing tasks instead of doing them, which is just procrastination wearing a planner's clothes.

Every to-do app on the planet answers this with more features: priorities, tags, Eisenhower matrices, AI scheduling assistants that need your calendar, your email, your soul, and a $12/month subscription. They make the triage *heavier*. Nobody built the app that does the triage for you and then — this is the important part — tells you to do less.

So for "Slow and Steady" I built exactly that: a tool that rewards laziness by doing the one piece of work you were avoiding (deciding what matters), capping your day at three things, and granting you written permission to delete the rest.

## What I built

**SlothPlan** — a command-line tool where you dump a messy to-do list and get back three buckets: **DO TODAY** (max 3, non-negotiable), **DEFER** (officially not today's problem), and **DELETE** (permission granted, let it go). Each item gets a one-line reason. The judgment comes from a local open-weight model; the guarantees come from deterministic code.

```bash
python3 -m slothplan triage -f my-messy-todos.txt
```

The twist, same as my Week 2 entry: the model, the inference engine, and all the code run on your own machine. No account. No API key. No subscription. Your to-do list — which is, let's be honest, a map of your anxieties — never touches a network.

## The demo (real transcript, unedited)

I fed it a 12-item Tuesday dump. Here is what the recorded run produced (full transcript in the repo's `demo-output.txt` — nothing cherry-picked):

```
=== SLOTHPLAN triage ===
method: rule-based fallback (--no-llm was passed; no model was run)

DO TODAY (max 3) — your only decisions today:
  1. Pay electricity bill, due Friday or they cut the power
     -> looks time-sensitive — it names a deadline, payment, or an urgent event
  2. Reply to Priya about the wedding RSVP — deadline is tomorrow
     -> looks time-sensitive — it names a deadline, payment, or an urgent event
  3. Submit the Hacktoberfest Week 3 entry README tonight
     -> looks time-sensitive — it names a deadline, payment, or an urgent event

DEFER — officially not today's problem:
  4. Call dentist to reschedule the appointment
     -> looks time-sensitive ... [moved from today: the 3-item cap keeps your day lazy]
  12. Call mom back — she called twice today
     -> looks time-sensitive ... [moved from today: the 3-item cap keeps your day lazy]

DELETE — permission granted, let it go:
  10. Delete that crypto spam email from "DOUBLE YOUR COINS"
     -> matches a junk pattern — nothing of value is lost
  11. Reorganize my Netflix watchlist
     -> matches a junk pattern — nothing of value is lost
```

That's the deterministic mode (`--no-llm`), and it's the mode I'd actually use daily: three real obligations surfaced, the dentist and mom politely bounced by the cap with an explanation, and the crypto spam and the Netflix-watchlist reorganization sentenced to death. Twelve decisions I didn't have to make.

Now the confession, because the transcript has two runs and I'm not hiding the first one: when I let the 0.5B model judge all 12 items itself, it took "rewards laziness" as a personal mission. It **deleted the electricity bill**. It called buying milk "spam". It deleted calling my mother. Every verdict parsed cleanly — 12/12, zero fallbacks — but its *judgment* was a sloth with an agenda. The transcript shows it exactly as it happened, which is the point of the architecture below: the model's opinions are suggestions; the deterministic layer holds the guarantees.

## How it works

Deliberately boring architecture, because boring ships:

- **Parsing** (stdlib only): every non-empty line is a task; `#` comments and bullet/checkbox markers are stripped. My sample file's header comment got triaged as a task in the first build — fixed, and there's a test for it now.
- **Judgment** (`slothplan/llm.py`): one verdict per task from **Qwen2.5-0.5B-Instruct** (Apache 2.0 open weights, Q4_K_M quantized) through the **llama.cpp** binary (MIT). Greedy decoding, ~3 seconds per item on two CPU cores. The model emits a single bucket word plus a short reason — a shape small enough for a 0.5B model to hold. This was a *discovery*, not the plan: my first prototype asked for one big JSON object covering all tasks, and the model hallucinated item numbers 13–20 for a 12-item list and stuffed 12 entries into a 3-item bucket. So the model judges one task at a time, and structure is enforced by code.
- **Enforcement** (`slothplan/triage.py`): every verdict is parsed and validated. Max 3 in "today" — overflow is moved to defer *with the reason printed*, so the cap is visible, not silent. Unparseable verdicts fall back to keyword rules and are **labeled as fallback in the output**. Nothing fails silently, ever.
- **Zero third-party Python dependencies.** Python 3.8, two downloaded files, and it runs. 29 unit tests, all passing.

## Why open innovation matters

This tool **cannot exist** on a closed API, for two reasons — one practical, one philosophical.

Practically: SlothPlan's entire design is a bet that a *small* model is enough. A 0.5B model is honest about what it is — opinionated, sometimes wrong, occasionally deleting your electricity bill — and the whole architecture (deterministic guardrails, labeled fallbacks, a `--no-llm` mode) is built around that honesty. You can only build that way if you can run the model locally, iterate on prompts for free at 3 a.m., and ship something whose marginal cost per triage is exactly zero. A closed API charges per token, which means every design decision bends toward fewer, bigger calls — the opposite of this architecture. And a to-do list is personal enough that "send it to someone's cloud" was never on the table.

Philosophically: the open-weights ecosystem is what lets a student with a $0 budget and a borrowed VM build something in a day that would have been a research project five years ago. Qwen2.5's weights are public under Apache 2.0. llama.cpp is MIT. My code is MIT. Anyone can audit every layer, swap in a bigger GGUF with one flag, or fork the whole thing. That composability — weights, engine, and app all inspectable and replaceable — is open innovation working exactly as advertised. The moat isn't the model; it's the trust that comes from everything being auditable.

## Honest limitations

I'd rather tell you than have you discover them:

- The bundled model is **0.5 billion parameters** — tiny on purpose, so it runs on any laptop CPU. Its verdicts are *opinions*, and sometimes bad ones (see: the electricity bill incident). Any GGUF drops in via `--model`; a bigger model would judge better.
- Reasons are sometimes missing (`(no reason given)`) — the model often emits just the bucket word despite being shown examples.
- The rule-based fallback is keyword heuristics, not understanding. It won't catch "renew the thingy before the thing expires."
- Prototype built in a day for a challenge, not a hardened product. 24 items max per run, `.txt` input, CLI only.

Bonus-points honesty: I have **no first user yet** — this was built for the challenge this week, starting Monday morning. The demo above is real output from the actual tool, and the limitations section is real too.

## Try it

Repo: https://github.com/swarnnim/slothplan
```bash
./scripts/download-llamacpp.sh
./scripts/download-model.sh
python3 -m slothplan triage -f sample_todos/messy.txt
```

If you also have a 47-item list you're avoiding: what's the one task on it you'd secretly love an app to delete for you? That's the roadmap — a bigger delete bucket.
