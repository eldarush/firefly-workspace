"""Team-owned spec for textstats. READ-ONLY by policy: fix the library."""

import unittest

from textstats import top_word, unique_words, word_count


class TestWordCount(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(word_count(""), 0)

    def test_single(self):
        self.assertEqual(word_count("hello"), 1)

    def test_sentence(self):
        self.assertEqual(word_count("the quick brown fox"), 4)


class TestUniqueWords(unittest.TestCase):
    def test_case_insensitive(self):
        self.assertEqual(unique_words("Dog dog DOG cat"), ["cat", "dog"])

    def test_punctuation(self):
        self.assertEqual(unique_words("Hi! hi, HI."), ["hi"])


class TestTopWord(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(top_word("a b b c c c"), "c")

    def test_tie_alphabetical(self):
        self.assertEqual(top_word("beta alpha beta alpha"), "alpha")

    def test_empty(self):
        self.assertIsNone(top_word("   "))


if __name__ == "__main__":
    unittest.main(verbosity=2)
