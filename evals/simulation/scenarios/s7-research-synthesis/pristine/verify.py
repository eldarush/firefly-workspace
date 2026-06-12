#!/usr/bin/env python3
"""Pristine verifier for s7-research-synthesis. Usage: verify.py <sandbox>

Fact-checks synthesis.md:
  Q1 must credit P1 with the 14-point (or 3% vs 17%) stale-index gap
  Q2 must name P1 vs P2 on query rewriting with directionally right claims
  Q3 must give a chunk-size rec citing P1 (function-level/80) or P3
     (40-line) and mention the caveat/conflict
  Q4 must exist and be non-trivial
  every Q section must carry at least one (P#) citation
"""

import os
import re
import sys


def section(text, name):
    m = re.search(r"##\s*%s\b(.*?)(?=\n##\s*Q|\Z)" % name, text,
                  re.S | re.I)
    return m.group(1) if m else ""


def main():
    sandbox = os.path.abspath(sys.argv[1])
    path = os.path.join(sandbox, "synthesis.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        print("FAIL: synthesis.md missing")
        sys.exit(1)

    q1 = section(text, "Q1")
    if "p1" not in q1.lower() or not re.search(
            r"14|3\s*%.{0,40}17\s*%|17\s*%.{0,40}3\s*%", q1, re.S):
        print("FAIL: Q1 must credit P1 with the stale-index gap "
              "(14 points / 3%% vs 17%%)")
        sys.exit(1)

    q2 = section(text, "Q2").lower()
    if "p1" not in q2 or "p2" not in q2 or "rewrit" not in q2:
        print("FAIL: Q2 must contrast P1 and P2 on query rewriting")
        sys.exit(1)
    if not (re.search(r"p1[^.]*(hurt|-6|worse|degrad)", q2, re.S)
            or re.search(r"(hurt|-6|worse|degrad)[^.]*p1", q2, re.S)):
        print("FAIL: Q2 must state P1 found rewriting HURT (-6%% nDCG)")
        sys.exit(1)

    q3 = section(text, "Q3").lower()
    if not (("function" in q3 and ("80" in q3 or "p1" in q3))
            or ("40" in q3 and "p3" in q3)):
        print("FAIL: Q3 must give a sourced chunk-size recommendation")
        sys.exit(1)
    if "p1" not in q3 or "p3" not in q3:
        print("FAIL: Q3 must acknowledge the P1 vs P3 chunking conflict")
        sys.exit(1)

    q4 = section(text, "Q4")
    if len(q4.strip()) < 120:
        print("FAIL: Q4 proposal too thin")
        sys.exit(1)

    for name in ("Q1", "Q2", "Q3", "Q4"):
        if not re.search(r"\(P[123]\)", section(text, name)):
            print("FAIL: %s has no (P#) citations" % name)
            sys.exit(1)

    print("PASS: synthesis fact-checks out")
    sys.exit(0)


if __name__ == "__main__":
    main()
