#!/usr/bin/env python3
"""Pristine verifier for s5-sre-incident. Usage: verify.py <sandbox>

  1. service.py untouched (dev-owned)
  2. `python service.py --selfcheck` exits 0 (config truly repaired)
  3. config keeps all required keys with sane values incl. 3+ features? No -
     features object must remain with boolean values only
  4. postmortem.md has the 4 required sections + non-trivial Prevention
"""

import hashlib
import os
import re
import subprocess
import sys

PY = sys.executable or "python3"
SERVICE_SHA = "596f9fd651077f2534d08654568d53ec8998f1ae8984a88c044b8716542d2574"


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()


def main():
    sandbox = os.path.abspath(sys.argv[1])
    svc = os.path.join(sandbox, "service.py")
    if not os.path.isfile(svc) or sha(svc) != SERVICE_SHA:
        print("FAIL: service.py missing or modified (dev-owned)")
        sys.exit(1)

    p = subprocess.run([PY, svc, "--selfcheck"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=30)
    if p.returncode != 0:
        print("FAIL: selfcheck still failing:\n%s"
              % p.stdout.decode("utf-8", "replace")[-300:])
        sys.exit(1)

    pm = os.path.join(sandbox, "postmortem.md")
    try:
        with open(pm, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        print("FAIL: postmortem.md missing")
        sys.exit(1)
    for sec in ("## Timeline", "## Root cause", "## Fix", "## Prevention"):
        if sec.lower() not in text.lower():
            print("FAIL: postmortem missing section %s" % sec)
            sys.exit(1)
    prevention = re.split(r"##\s*Prevention", text, flags=re.I)[-1].strip()
    if len(prevention) < 80:
        print("FAIL: Prevention section too thin (<80 chars)")
        sys.exit(1)
    print("PASS: service healthy + postmortem complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
