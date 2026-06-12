"""textkit - small text helpers for the docs pipeline.

TODO(team): slugify() is specified in test_textkit.py and not yet
implemented. Implement it here; do not change the tests.
"""


def title_case(text):
    return " ".join(w.capitalize() for w in (text or "").split())
