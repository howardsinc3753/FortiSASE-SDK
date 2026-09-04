---
description: Search the FortiSASE corpus and return a cited, tier-labeled answer
argument-hint: <topic or question>
---

Answer the FortiSASE question: **$ARGUMENTS**

Procedure (per `CLAUDE.md` tier rules):
1. Search [`corpus/raw/fortinet-docs/`](../../corpus/raw/fortinet-docs/) first, then `api/reference/`, then `corpus/community/`.
2. Quote the relevant snippet. Cite **both** the corpus file path and the inline `(Source: <url>)`.
3. Label the **tier** (1 official docs / 2 dev+code / 3 datasheet+positioning / 4 community).
4. If the corpus flags the item **UNVERIFIED**, say so — don't launder it into fact.
5. If it's not in the corpus, say "not in corpus" and offer to research it (WebSearch/WebFetch against docs.fortinet.com), then optionally save the result back into the corpus.
6. If sources conflict, surface the conflict and lead with the higher tier (Ordering Guide beats reseller SKUs; docs beat memory).

Lead with the answer; Daniel is technical. Keep it tight.
