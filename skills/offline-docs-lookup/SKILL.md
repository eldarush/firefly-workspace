---
name: offline-docs-lookup
description: Use when you need library, tool, or platform documentation in the airgapped environment - searching Kiwix and internal mirrors instead of the public web.
---
# Offline Docs Lookup

**There is NO public internet. NEVER fabricate version-specific behavior from memory. Look it up or label it explicitly as "unverified-memory".**

## Sources in Priority Order

1. **Installed source code** - the ultimate truth for the exact installed version.
   ```bash
   # Python
   find /usr/lib/python3 ~/.local/lib -name "*.py" -path "*<package>*" | head -20
   # Node
   find node_modules/<package>/src -name "*.js" | head -10
   # Go vendor
   find vendor/<module> -name "*.go" | head -10
   ```

2. **Kiwix/WikiAll server** - base URL from `.firefly/config.json` at key `docs.kiwix_url`.
   ```bash
   KIWIX=$(cat .firefly/config.json | jq -r '.docs.kiwix_url')

   # Search
   curl -s "$KIWIX/search?pattern=<terms>&pageLength=10"

   # Suggestions for a specific book
   curl -s "$KIWIX/suggest?content=<book>&term=<term>"

   # Fetch a page
   curl -s "$KIWIX/content/<book>/<path>" | sed 's/<[^>]*>//g' | head -80
   ```
   Common book IDs: `devdocs`, `stackoverflow`, `wikipedia`.

3. **Internal doc portals** - listed at `.firefly/config.json` key `docs.extra_sources`.
   ```bash
   cat .firefly/config.json | jq '.docs.extra_sources'
   ```

4. **`--help`, man pages, `kubectl explain`**
   ```bash
   <command> --help 2>&1 | less
   man <command>
   kubectl explain <resource>.<field>
   ```

## Citation Format

Always cite source: `[book: devdocs, page: "Array.prototype.reduce"]` or `[file: vendor/github.com/foo/bar/client.go:142]`.

When installed version and mirror version conflict: the installed code wins.

## Failure Mode Table

| Symptom | Cause | Fix |
|---|---|---|
| Search returns no results | Terms too specific | Broaden: "reduce array" not "Array.prototype.reduce MDN" |
| Search returns noise | Terms too broad | Add book qualifier: `content=devdocs` |
| Kiwix returns 404 on path | Path format wrong | Use `/suggest` to find the correct path slug first |
| Kiwix server unreachable | Server down | Note it; fall back to reading installed source + `--help` |
| Mirror has old version | Version mismatch | Read installed source code directly; label mirror content as potentially stale |

## Rules

- NEVER present version-specific API behavior as fact without a source.
- MUST label any claim from memory as "unverified-memory: <claim>".
- When Kiwix is down: use installed source + `--help`. Do not guess.
- MUST cite the source for every doc reference (book + page title or file path).
- If source and docs conflict: installed source wins; note the discrepancy.
