---
name: research-literature-synthesis
description: Use when synthesizing internal docs, ADRs, design docs, or Kiwix/WikiAll content into a decision-ready brief, comparing prior art, or answering "what do we know about X".
---
# Research Literature Synthesis

## AIRGAPPED CONSTRAINT

All sources are internal: repo docs, ADRs, design docs, Kiwix/WikiAll offline mirrors, and the code itself.
Do not cite URLs that require external network access.
Do not suggest querying external search engines or public documentation sites.

---

## Step 1 -- Define the Question and the Decision It Informs

Start every synthesis with this statement:
"We are answering [QUESTION] in order to decide [DECISION]."

A synthesis without a downstream decision is a reading list, not a brief.

Examples:
- "We are answering 'what retry strategies exist in our HTTP clients' to decide which retry library to standardize on."
- "We are answering 'how do Flink state backends differ in our deployment' to decide whether to migrate from RocksDB to the Gemini state backend."

---

## Step 2 -- Source Sweep with Provenance

For every source consulted, record a provenance entry before extracting any claims.

| ID | Location (path or Kiwix title)                    | Version / Date       | Credibility                              |
|----|---------------------------------------------------|----------------------|------------------------------------------|
| S1 | <REPO>/docs/adr/0042-retry-policy.md              | 2024-03-15           | ADR -- high                              |
| S2 | Kiwix: "Exponential backoff" (WikiAll mirror)     | mirror snapshot date | General reference -- medium              |
| S3 | <REPO>/src/client/retry.go, commit abc1234        | current HEAD         | Code -- authoritative for actual behavior|
| S4 | <REPO>/docs/design/retry-v2.md                    | 2023-11-01           | Design doc -- check if superseded by S1  |

Credibility order (highest first):
official vendor doc in Kiwix > ADR > code (current HEAD) > design doc > wiki page > code comment > verbal/hearsay.

---

## Step 3 -- Extraction: Quote, Do Not Paraphrase Numbers

For each relevant claim extracted from each source:
```
[S1, line 12] "All idempotent endpoints MUST retry up to 3 times with exponential backoff starting at 500ms."
[S3, line 47] Current implementation retries 5 times with a fixed 1s delay. -- DIVERGES from S1.
[S2]          "Jitter is recommended to prevent thundering-herd effects." -- general guidance, not org-specific policy.
```

Rules:
- Quote the exact wording when it matters (policy statements, thresholds, limits).
- NEVER paraphrase numbers -- "about 500ms" introduces unacceptable error.
- Tag every extracted claim with its source ID.
- Flag staleness: if a doc is more than 1 year old and the relevant code has changed, note that the doc may not reflect current behavior.

---

## Step 4 -- Synthesis Matrix

Build a matrix of claims (rows) versus sources (columns).

| Claim                          | S1 (ADR)         | S2 (Wiki) | S3 (Code)             | Status                         |
|--------------------------------|------------------|-----------|------------------------|--------------------------------|
| Max retries = 3                | YES: "up to 3"   | SILENT    | NO: implements 5       | CONFLICT                       |
| Exponential backoff            | YES              | YES       | NO: fixed 1s delay     | CONFLICT                       |
| Jitter recommended             | SILENT           | YES       | NO jitter              | GAP in implementation          |
| Retry only idempotent endpoints| YES              | SILENT    | SILENT                 | AGREEMENT (single source only) |

**Conflict resolution rule:**
- Do NOT average conflicting claims or silently pick one.
- Provisionally: newest source wins; code wins over docs for "what the system actually does right now."
- Flag every conflict explicitly for human decision.

---

## Step 5 -- Deliver the Brief

Structure the output in this order:

**Direct answer (first paragraph):**
> Based on sources S1-S4: The current retry implementation (S3) diverges from the ADR policy (S1) on both retry count (5 vs 3) and backoff strategy (fixed delay vs exponential). The ADR represents the documented intent; the code has not been updated since the ADR was ratified in March 2024.

**Evidence table:** (the synthesis matrix from Step 4)

**Conflicts:** list each conflict, name the two sources, state why it matters to the decision.

**Gaps:** list what is not documented anywhere -- these are risks to the decision.

**Confidence:** high / medium / low, with explicit reasoning.
- High: multiple independent sources agree, including current code.
- Medium: one authoritative source (ADR) but code diverges, or sources are somewhat stale.
- Low: only design docs available, no code evidence, or all sources are more than 2 years old.

**Closing the biggest gap:**
"To confirm which retry count is operationally correct, measure retry telemetry in Grafana over the last 30 days.
See research-experiment-design for how to structure that measurement."

---

## Provenance Rules (MUST)

Every paragraph in the delivered brief MUST end with a source citation, or be explicitly labeled:
- [INFERENCE]: logical conclusion drawn from cited facts (acceptable, must be labeled).
- [SPECULATION]: no direct evidence (must be labeled; minimize; flag for human review).

Uncited claims get cut from the final brief. No exceptions.