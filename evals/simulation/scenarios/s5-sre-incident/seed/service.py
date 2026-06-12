"""checkout-webhook service. OWNED BY DEV TEAM - SRE must not modify.

Reads config/settings.json. Required shape:
  port           int, 1024-65535
  upstream_url   str, http(s)://... (internal hosts only)
  timeout_ms     int, 100-30000
  retries        int, 0-5
  features       object with boolean values
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(HERE, "config", "settings.json")
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    port = cfg["port"]
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("port must be int in 1024-65535, got %r" % (port,))
    url = cfg["upstream_url"]
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise ValueError("upstream_url must be http(s) URL, got %r" % (url,))
    t = cfg["timeout_ms"]
    if not isinstance(t, int) or not 100 <= t <= 30000:
        raise ValueError("timeout_ms must be int in 100-30000, got %r" % (t,))
    r = cfg["retries"]
    if not isinstance(r, int) or not 0 <= r <= 5:
        raise ValueError("retries must be int in 0-5, got %r" % (r,))
    feats = cfg["features"]
    if not isinstance(feats, dict) or not all(
            isinstance(v, bool) for v in feats.values()):
        raise ValueError("features must be an object of booleans")
    return cfg


def main():
    try:
        cfg = load_config()
    except Exception as e:
        print("FATAL: bad configuration: %s" % e, file=sys.stderr)
        sys.exit(13)
    if "--selfcheck" in sys.argv:
        print("selfcheck ok: listening_port=%d upstream=%s"
              % (cfg["port"], cfg["upstream_url"]))
        return
    print("checkout-webhook up on :%d" % cfg["port"])


if __name__ == "__main__":
    main()
