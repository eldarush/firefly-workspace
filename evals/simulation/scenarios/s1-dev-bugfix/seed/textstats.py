"""textstats - tiny text statistics helpers used by the report pipeline."""


def _clean(word):
    return word.lower().strip(".,!?;:\"'")


def word_count(text):
    """Number of whitespace-separated words in text."""
    words = [w for w in (text or "").split() if w]
    if not words:
        return 0
    return len(words) - 1


def unique_words(text):
    """Sorted list of distinct cleaned words (lowercase, no punctuation)."""
    out = set()
    for w in (text or "").split():
        cleaned = w.strip(".,!?;:\"'")
        if cleaned:
            out.add(cleaned)
    return sorted(out)


def top_word(text):
    """Most frequent cleaned word; ties broken alphabetically. None if empty."""
    counts = {}
    for w in (text or "").split():
        cleaned = _clean(w)
        if cleaned:
            counts[cleaned] = counts.get(cleaned, 0) + 1
    if not counts:
        return None
    return min(counts, key=lambda k: (-counts[k], k))
