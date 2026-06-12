"""retry - exponential backoff with jitter. OWNED BY PLATFORM TEAM.

Correct and intentionally injectable: pass your own `rng` (any object with
`uniform(a, b)`) to make results deterministic in tests.
"""

import random


def backoff_delays(attempts, base=0.1, rng=None):
    """Delays for `attempts` retries: base*2^i plus jitter in [-base, base]."""
    rng = rng or random.Random()
    out = []
    for i in range(attempts):
        jitter = rng.uniform(-base, base)
        out.append(round(base * (2 ** i) + jitter, 6))
    return out
