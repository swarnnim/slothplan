"""Tests for the deterministic rule-based fallback, verdict merging,
and output rendering."""

import unittest

from slothplan.triage import fallback_bucket, merge_verdicts, render


def merge(texts, verdicts):
    numbered = list(enumerate(texts, start=1))
    return merge_verdicts(verdicts, numbered)


class TestFallbackBucket(unittest.TestCase):
    def test_urgent_tasks(self):
        for text in ("Pay electricity bill, due Friday",
                     "Reply to Priya: wedding RSVP deadline tomorrow",
                     "Submit the README tonight"):
            bucket, reason = fallback_bucket(text)
            self.assertEqual(bucket, "today", text)
            self.assertTrue(reason.strip())

    def test_junk_tasks(self):
        for text in ("Delete that crypto spam email",
                     "Reorganize my Netflix watchlist"):
            bucket, _ = fallback_bucket(text)
            self.assertEqual(bucket, "delete", text)

    def test_urgent_beats_junk(self):
        # A bill mentioning junk-ish words is still a real task: urgency
        # wins so nothing real is silently dropped.
        bucket, _ = fallback_bucket("Pay bill or they delete my account")
        self.assertEqual(bucket, "today")

    def test_plain_tasks_defer(self):
        for text in ("Learn Rust someday", "Organize the bookshelf"):
            bucket, _ = fallback_bucket(text)
            self.assertEqual(bucket, "defer", text)

    def test_every_bucket_has_reason(self):
        for text in ("Pay bill due today", "Buy milk", "Crypto spam email"):
            bucket, reason = fallback_bucket(text)
            self.assertTrue(reason.strip(), text)


class TestMergeVerdicts(unittest.TestCase):
    def test_basic_assignment(self):
        result, n_fb = merge(
            ["Pay bill due today", "Learn Rust someday", "Crypto spam"],
            [("today", "urgent", False), ("defer", "waits", False),
             ("delete", "junk", False)])
        self.assertEqual([n for n, _ in result["today"]], [1])
        self.assertEqual([n for n, _ in result["defer"]], [2])
        self.assertEqual([n for n, _ in result["delete"]], [3])
        self.assertEqual(n_fb, 0)

    def test_today_capped_in_original_order(self):
        verdicts = [("today", "u", False)] * 5
        result, _ = merge(["a", "b", "c", "d", "e"], verdicts)
        self.assertEqual([n for n, _ in result["today"]], [1, 2, 3])
        self.assertEqual([n for n, _ in result["defer"]], [4, 5])
        # The overflow items carry an explanatory note.
        self.assertIn("cap", result["defer"][0][1])

    def test_fallback_items_marked_and_counted(self):
        result, n_fb = merge(
            ["Pay bill due today", "Buy milk"],
            [("today", "urgent", False), ("defer", "plain", True)])
        self.assertEqual(n_fb, 1)
        self.assertIn("rule-based fallback",
                      [r for n, r in result["defer"]][0])

    def test_every_item_assigned_exactly_once(self):
        texts = ["a", "b", "c", "d"]
        verdicts = [("today", "x", False), ("today", "x", True),
                    ("defer", "x", False), ("delete", "x", False)]
        result, _ = merge(texts, verdicts)
        assigned = sorted(n for b in result for n, _ in result[b])
        self.assertEqual(assigned, [1, 2, 3, 4])


class TestRender(unittest.TestCase):
    def test_render_shows_buckets(self):
        numbered = list(enumerate(
            ["Pay bill due today", "Learn Rust", "Crypto spam"], start=1))
        verdicts = [("today", "urgent", False), ("defer", "waits", False),
                    ("delete", "junk", False)]
        result, _ = merge_verdicts(verdicts, numbered)
        out = render(result, [t for _, t in numbered],
                     method_note="test method")
        self.assertIn("DO TODAY", out)
        self.assertIn("DEFER", out)
        self.assertIn("DELETE", out)
        self.assertIn("test method", out)
        self.assertIn("Pay bill due today", out)

    def test_render_empty_buckets(self):
        result, _ = merge(["Buy milk"], [("defer", "waits", False)])
        out = render(result, ["Buy milk"], method_note="m")
        self.assertIn("(nothing", out)


if __name__ == "__main__":
    unittest.main()
