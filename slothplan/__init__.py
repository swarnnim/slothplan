"""SlothPlan — the to-do list that does less.

Local-first CLI that triages a messy to-do dump into DO TODAY (max 3),
DEFER, and DELETE using a local open-weight model, with a deterministic
rule-based fallback when the model's output can't be validated.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
