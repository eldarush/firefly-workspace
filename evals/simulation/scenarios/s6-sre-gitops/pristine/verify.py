#!/usr/bin/env python3
"""Pristine verifier for s6-sre-gitops. Usage: verify.py <sandbox>

Recomputes ground-truth drift from the seed properties files and demands an
exactly-equal drift_report.json + a remediation.md covering every changed key.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.join(HERE, "..", "seed", "gitops")


def load_props(path):
    out = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


def main():
    sandbox = os.path.abspath(sys.argv[1])
    desired = load_props(os.path.join(SEED, "desired.properties"))
    live = load_props(os.path.join(SEED, "live.properties"))

    truth = {
        "missing_in_live": {k: v for k, v in desired.items() if k not in live},
        "unexpected_in_live": {k: v for k, v in live.items()
                               if k not in desired},
        "changed": {k: {"desired": desired[k], "live": live[k]}
                    for k in desired if k in live and desired[k] != live[k]},
        "in_sync_count": sum(1 for k in desired
                             if k in live and desired[k] == live[k]),
    }

    try:
        with open(os.path.join(sandbox, "drift_report.json"), "r",
                  encoding="utf-8") as f:
            got = json.load(f)
    except Exception as e:
        print("FAIL: drift_report.json missing/invalid: %s" % e)
        sys.exit(1)

    for key in truth:
        if got.get(key) != truth[key]:
            print("FAIL: %s wrong\n  expected %s\n  got      %s"
                  % (key, json.dumps(truth[key], sort_keys=True),
                     json.dumps(got.get(key), sort_keys=True)))
            sys.exit(1)

    try:
        with open(os.path.join(sandbox, "remediation.md"), "r",
                  encoding="utf-8") as f:
            rem = f.read().lower()
    except Exception:
        print("FAIL: remediation.md missing")
        sys.exit(1)
    for k in truth["changed"]:
        if k.lower() not in rem:
            print("FAIL: remediation.md does not cover changed key %s" % k)
            sys.exit(1)
    print("PASS: drift report exact + remediation covers all changed keys")
    sys.exit(0)


if __name__ == "__main__":
    main()
