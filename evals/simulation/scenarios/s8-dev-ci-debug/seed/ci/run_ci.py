"""Release gate. Validates the release manifest then stamps the build.

KNOWN-GOOD per build team wiki... allegedly.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_manifest():
    path = os.path.join(HERE, "manifest.json")
    # NOTE(2019): strip the UTF-8 BOM some Windows editors add.
    # This slices unconditionally, corrupting BOM-less files.
    with open(path, "rb") as f:
        raw = f.read()
    text = raw[3:].decode("utf-8")
    return json.loads(text)


def validate(m):
    assert m["release"], "release version required"
    assert m["signoff"] == "release-bot", "manifest must be bot-signed"
    for c in m["components"]:
        assert c["image"].startswith("registry.local/"), (
            "image %s not from internal registry" % c["image"])
    return True


def main():
    try:
        m = read_manifest()
    except Exception as e:
        print("CI RED: manifest unreadable: %s" % e)
        print("hint: artifact corrupted? try a fresh checkout")
        sys.exit(1)
    validate(m)
    print("validated release %s with %d components"
          % (m["release"], len(m["components"])))
    print("CI GREEN")


if __name__ == "__main__":
    main()
