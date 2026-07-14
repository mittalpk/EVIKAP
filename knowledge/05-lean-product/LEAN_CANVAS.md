# Lean Canvas

**Lean Product Development — Business Model on One Page**
**Status:** Draft · **Version:** 1.0 · 2026-07-14

---

| Problem | Solution | Unique Value Proposition | Unfair Advantage | Customer Segments |
|---|---|---|---|---|
| 1. Knowledge workers can't find authoritative answers across fragmented internal systems (repos, wikis, DBs)<br>2. AI agents can't be safely given broad access to internal knowledge<br>3. No instrumented visibility into what fragmentation actually costs | 1. Unified cross-source semantic retrieval with citations<br>2. Governed multi-agent reasoning layer with a hard trust boundary<br>3. Auditable provenance for every AI-mediated answer | The only knowledge layer that lets you extend AI agents into your internal knowledge **without** choosing between "useful" and "governed" — one query interface, permission-safe by construction, cited by default | A working, security-reviewed trust-boundary architecture (agent has zero source-system credentials) already validated in a working codebase — most competitors bolt governance on after the fact | Mid-to-large tech-enabled enterprises (500+ employees, 100+ engineers) already deploying or evaluating internal AI agents and feeling knowledge fragmentation pain |

| Key Metrics | | High-Level Concept | | Channels |
|---|---|---|---|---|
| Median time-to-answer reduction | | "A permission-aware Google for everything your company already knows — safe enough to hand to your AI agents" | | Direct engagement with AI platform / developer-productivity teams already running an internal AI-agent initiative; land via a single pilot business unit, expand internally |
| Weekly active users / query volume | | | | |
| Groundedness rate (evaluation harness) | | | | |
| Cost per query | | | | |

| Cost Structure | | Revenue Streams |
|---|---|---|
| LLM inference (planning + synthesis calls) | | *(Internal platform in initial delivery — not externally monetized; see Section "Revenue model note" below)* |
| Vector/relational data storage and indexing compute | | Future: internal chargeback to business units by query volume, or licensing as a platform product once validated across multiple business units |
| Platform/AI engineering team (build + ongoing evaluation/observability operation) | | |
| Cloud infrastructure (compute, cache, observability) | | |

## Revenue model note

Initial delivery is scoped as an **internal enterprise platform**, not an externally sold product (see [Problem Statement §10.2](../PRODUCT_PROBLEM_STATEMENT.md#102-out-of-scope-initial-delivery)). Value is captured as recovered productivity (Section "Key Metrics" and [Problem Statement §5.4](../PRODUCT_PROBLEM_STATEMENT.md#54-expected-roi)), not direct revenue. The Lean Canvas revenue-stream box is intentionally sparse at this stage — externally licensable multi-tenant delivery is a roadmap item (see [Problem Statement §10.3](../PRODUCT_PROBLEM_STATEMENT.md#103-future-roadmap)), not a Day 1 assumption. Treating this honestly as a cost-avoidance/productivity investment, not a revenue product, is itself a scope decision: it keeps the MVP focused on proving time-to-answer impact rather than building billing/multi-tenancy infrastructure the business case doesn't yet need.

## Riskiest assumptions (ranked)

1. **Users will trust and adopt a synthesized AI answer over their current habit of asking a colleague or searching one system they know.** (Highest risk — behavioral, not technical.)
2. **Semantic retrieval quality will be good enough, across genuinely heterogeneous enterprise sources, to be trustworthy without heavy manual curation.**
3. **Permission propagation across heterogeneous source systems can be made correct and provably auditable**, not just "probably fine."
4. **The productivity cost of fragmentation, once actually measured in the pilot organization, is large enough to justify sustained investment** (the Section 2.3 industry benchmarks are directional, not validated for any specific org).

These four map directly to the validation plan in [PROBLEM_SOLUTION_FIT.md](PROBLEM_SOLUTION_FIT.md).
