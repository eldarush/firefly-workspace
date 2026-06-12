---
description: Map-reduce deep research over offline sources - parallel researchers, cited synthesis
argument-hint: "<research question>"
disable-model-invocation: true
---

Run deep offline research: $ARGUMENTS

This is an airgapped environment - sources are the local repo(s), Kiwix/WikiAll
(URL in .firefly/config.json docs.kiwix_url), and internal doc portals
(docs.extra_sources). Public internet does not exist.

1. **Scope**: restate the research question and the DECISION it informs (ask
   the user if unclear - research without a decision is entertainment).
   Define what a sufficient answer looks like.

2. **Decompose** into 2-4 genuinely independent tracks (e.g. current
   implementation / alternatives / operational constraints / prior art).
   If the question is simple, skip the fan-out and answer with one
   `researcher` pass.

3. **Map**: launch one `researcher` subagent per track IN PARALLEL. Each
   prompt must be self-contained: the track question, where to look (specific
   paths, Kiwix book names, doc URLs), citation requirements, and a 400-word
   memo limit.

4. **Reduce**: synthesize the memos yourself:
   - answer the original question directly, first
   - build a ranked options/decision matrix when alternatives were studied
   - keep every claim cited (source path/URL); drop uncited claims or mark
     them explicitly as inference
   - surface conflicts between sources rather than averaging them away

5. **Deliver**: answer, evidence table, gaps (what offline sources cannot
   answer), and the explicit decision now owed by the human architect.
   Offer to save the synthesis to a file the user names.
