"""Tests for per-item model verdict parsing."""

import unittest

from slothplan.triage import parse_verdict


class TestParseVerdict(unittest.TestCase):
    def test_canonical_shape(self):
        self.assertEqual(
            parse_verdict("defer (no deadline, start next month)"),
            ("defer", "no deadline, start next month"))

    def test_case_insensitive_word(self):
        self.assertEqual(
            parse_verdict("TODAY (it's due tonight)"),
            ("today", "it's due tonight"))

    def test_reason_without_parens(self):
        bucket, reason = parse_verdict("delete — pure junk, never do it")
        self.assertEqual(bucket, "delete")
        self.assertIn("junk", reason)

    def test_extra_prose_still_parses(self):
        # The bucket word comes first, so trailing prose is harmless.
        bucket, reason = parse_verdict(
            "today (due Friday) — this one matters")
        self.assertEqual(bucket, "today")
        self.assertIn("due Friday", reason)

    def test_missing_reason_gets_placeholder(self):
        self.assertEqual(parse_verdict("defer"),
                         ("defer", "(no reason given)"))
        self.assertEqual(parse_verdict("defer ()"),
                         ("defer", "(no reason given)"))

    def test_unknown_word_rejected(self):
        self.assertIsNone(parse_verdict("maybe (not sure)"))
        self.assertIsNone(parse_verdict("do it now (urgent)"))

    def test_empty_reply_rejected(self):
        self.assertIsNone(parse_verdict(""))
        self.assertIsNone(parse_verdict("   "))

    def test_sentence_without_bucket_word_rejected(self):
        self.assertIsNone(
            parse_verdict("I think you should do this tomorrow."))


if __name__ == "__main__":
    unittest.main()
