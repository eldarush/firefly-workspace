#!/usr/bin/env python3
"""Pristine verifier for s1-dev-bugfix: run the team spec against the
sandbox's textstats module. Usage: verify.py <sandbox>"""

import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    sandbox = os.path.abspath(sys.argv[1])
    sys.path.insert(0, sandbox)
    spec = importlib.util.spec_from_file_location(
        "pristine_tests", os.path.join(HERE, "test_textstats.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    print("PASS" if res.wasSuccessful() else "FAIL")
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
