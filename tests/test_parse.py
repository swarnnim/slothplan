"""Tests for item parsing and numbering."""

import unittest

from slothplan.triage import number_items, parse_items


class TestParseItems(unittest.TestCase):
    def test_plain_lines(self):
        self.assertEqual(
            parse_items("Buy milk\nCall mom\n"), ["Buy milk", "Call mom"])

    def test_blank_lines_ignored(self):
        self.assertEqual(
            parse_items("\n\nBuy milk\n  \nCall mom\n\n"),
            ["Buy milk", "Call mom"])

    def test_dash_bullets_stripped(self):
        self.assertEqual(
            parse_items("- Buy milk\n* Call mom\n• pay rent"),
            ["Buy milk", "Call mom", "pay rent"])

    def test_numbered_bullets_stripped(self):
        self.assertEqual(
            parse_items("1. Buy milk\n2) Call mom\n(3) pay rent"),
            ["Buy milk", "Call mom", "pay rent"])

    def test_checkboxes_stripped(self):
        self.assertEqual(
            parse_items("- [ ] Buy milk\n- [x] Call mom"),
            ["Buy milk", "Call mom"])

    def test_indented_lines(self):
        self.assertEqual(
            parse_items("   - Buy milk"), ["Buy milk"])

    def test_hyphenated_words_survive(self):
        # '-' inside a word must not be stripped.
        self.assertEqual(
            parse_items("Re-do the budget\nE-mail Priya"),
            ["Re-do the budget", "E-mail Priya"])

    def test_numbered_items_not_confused_with_digits(self):
        self.assertEqual(
            parse_items("Call 911 first"), ["Call 911 first"])

    def test_empty_input(self):
        self.assertEqual(parse_items("   \n\n"), [])


class TestNumberItems(unittest.TestCase):
    def test_one_based_numbering(self):
        self.assertEqual(
            number_items(["a", "b"]), [(1, "a"), (2, "b")])


if __name__ == "__main__":
    unittest.main()
