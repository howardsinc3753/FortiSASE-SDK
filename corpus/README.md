# Corpus — FortiSASE knowledge base

Source-of-truth for the FortiSASE SME. Organized by the tier system in [`../CLAUDE.md`](../CLAUDE.md).

```
corpus/
├── raw/
│   ├── fortinet-docs/      # TIER 1 — official docs.fortinet.com (the 3 cited SME docs live here)
│   ├── fortinet-corporate/ # TIER 3 — datasheets / Ordering Guide / positioning
│   ├── fortinet-github/    # TIER 2 — fortinetdev Terraform provider notes, official code
│   └── announcements/      # TIER 3 — press / keynotes (positioning, not technical detail)
├── community/              # TIER 4 — third-party / reseller, each file carries a caveat:
└── indexed/                # built search index over raw/ (not yet generated)
```

## Rules
- **Cite the tier** on every answer. Higher tier wins conflicts (Ordering Guide > reseller SKU; docs > memory).
- Tier-1 docs carry inline `(Source: <url>)` and flag **UNVERIFIED** items — preserve both when quoting.
- Community/reseller files (Tier 4) must have a `caveat:` field; never present them as fact.
- The three headline SME docs in `raw/fortinet-docs/` are research-compiled (June 2026) and version-stamped; refresh them when FortiSASE ships a new Feature release.

## What's here now
- `raw/fortinet-docs/01-architecture-and-onramps.md`
- `raw/fortinet-docs/02-automation-and-apis.md`
- `raw/fortinet-docs/03-releases-and-licensing.md`

Other folders are placeholders ready for drop-ins (raw HTML→MD doc captures, the Ordering Guide PDF→MD, community references).
