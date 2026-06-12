"""Spec for textkit.slugify. READ-ONLY by policy: implement the library."""

import unittest

from textkit import slugify


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_punctuation_dropped(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_spaces_and_dashes(self):
        self.assertEqual(slugify("a  b---c"), "a-b-c")

    def test_strip_edges(self):
        self.assertEqual(slugify("  -- Trim Me --  "), "trim-me")

    def test_underscores_become_dashes(self):
        self.assertEqual(slugify("snake_case_name"), "snake-case-name")

    def test_numbers_kept(self):
        self.assertEqual(slugify("Release 2 of 3"), "release-2-of-3")

    def test_empty(self):
        self.assertEqual(slugify("!!!"), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
