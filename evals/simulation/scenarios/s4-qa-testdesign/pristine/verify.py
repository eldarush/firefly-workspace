#!/usr/bin/env python3
"""Pristine verifier for s4-qa-testdesign. Usage: verify.py <sandbox>

Grades the agent-authored test_csvlite.py:
  1. >=4 test methods, references parse_line, csvlite.py untouched
  2. suite PASSES against the pristine module (correct expectations)
  3. suite FAILS against each planted mutant (real detection power)
Mutation testing means weak/no-op assertions cannot sneak through.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"

MUTANTS = {
    # mutant 1: escaped quotes broken ("" no longer collapses)
    "m1": ("if i + 1 < len(line) and line[i + 1] == '\"':\n"
           "                    buf.append('\"')\n"
           "                    i += 1\n"
           "                else:\n"
           "                    in_q = False",
           "in_q = False"),
    # mutant 2: separator comparison inverted for commas in quotes
    "m2": ("if ch == '\"':\n                in_q = True",
           "if ch == '\"':\n                pass"),
}


def run_suite(workdir):
    p = subprocess.run(
        [PY, "-m", "unittest", "discover", "-s", workdir, "-t", workdir,
         "-p", "test_*.py"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    return p.returncode == 0


def main():
    sandbox = os.path.abspath(sys.argv[1])
    agent_tests = os.path.join(sandbox, "test_csvlite.py")
    if not os.path.isfile(agent_tests):
        print("FAIL: test_csvlite.py not found")
        sys.exit(1)
    with open(agent_tests, "r", encoding="utf-8") as f:
        src = f.read()
    methods = re.findall(r"def test_\w+", src)
    if len(methods) < 4 or "parse_line" not in src:
        print("FAIL: need >=4 test methods exercising parse_line "
              "(found %d)" % len(methods))
        sys.exit(1)

    with open(os.path.join(HERE, "..", "seed", "csvlite.py"),
              "r", encoding="utf-8") as f:
        pristine = f.read()

    tmp = tempfile.mkdtemp(prefix="s4-verify-")
    try:
        shutil.copy2(agent_tests, os.path.join(tmp, "test_csvlite.py"))

        with open(os.path.join(tmp, "csvlite.py"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(pristine)
        if not run_suite(tmp):
            print("FAIL: your tests fail against the CORRECT module - "
                  "expectations are wrong")
            sys.exit(1)

        for name, (old, new) in MUTANTS.items():
            mutated = pristine.replace(old, new)
            if mutated == pristine:
                print("FAIL: harness bug - mutant %s did not apply" % name)
                sys.exit(1)
            with open(os.path.join(tmp, "csvlite.py"), "w",
                      encoding="utf-8", newline="\n") as f:
                f.write(mutated)
            if run_suite(tmp):
                print("FAIL: mutant %s SURVIVED - your assertions are too "
                      "weak to catch a real bug" % name)
                sys.exit(1)
        print("PASS: suite correct + killed all mutants")
        sys.exit(0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
