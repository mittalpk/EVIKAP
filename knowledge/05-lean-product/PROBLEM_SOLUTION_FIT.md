# Problem/Solution Fit

**Lean Product Development — Validation Plan**
**Status:** Draft · **Version:** 1.0 · 2026-07-14
**Related:** [LEAN_CANVAS.md](LEAN_CANVAS.md) · [../PRODUCT_PROBLEM_STATEMENT.md §2](../PRODUCT_PROBLEM_STATEMENT.md#2-problem-statement)

---

## 1. Purpose

Before committing to the full build sequenced in the [Program Backlog](../06-agile-delivery/PROGRAM_BACKLOG.md), this document defines how the four riskiest assumptions from the [Lean Canvas](LEAN_CANVAS.md) will be tested cheaply, with evidence — not asserted from the Problem Statement's industry benchmarks alone.

## 2. Problem validation (is the problem real, here, at this magnitude?)

| Assumption under test | Validation method | Evidence that would falsify it |
|---|---|---|
| Knowledge fragmentation costs a meaningful, measurable amount of time in the target organization | Time-motion survey of 15–20 representative knowledge workers in the pilot business unit; instrument current search behavior for 2 weeks before any build begins | If median self-reported search/re-discovery time is materially below the industry benchmark range (1.5–2.5 hrs/day), the business case in [Problem Statement §5.4](../PRODUCT_PROBLEM_STATEMENT.md#54-expected-roi) must be revised downward before further investment |
| Duplicated engineering effort from undiscovered prior work is a real, recurring pattern | Structured interviews with 5+ engineering leads: "in the last 6 months, did your team rebuild something that already existed elsewhere in the org?" | If <20% report at least one such incident, this value driver is weaker than assumed and should be de-emphasized in the business case |
| Users currently resort to interrupting colleagues because self-service search fails them | Support-ticket / Slack-thread sampling for "where do I find X" style questions, plus the same interviews above | If such questions are rare or already well-served by an existing tool, the core UVP is weaker than assumed |

## 3. Solution validation (does this specific solution fit the validated problem?)

| Assumption under test | Validation method | Evidence that would falsify it |
|---|---|---|
| Users will trust a synthesized, cited AI answer enough to change their default behavior | Concierge-style test: manually run a small number of real user questions through a retrieval+LLM prototype (not the full product), present cited answers, gather trust/usefulness ratings | If users consistently prefer to verify manually rather than trust the citation, the UX for provenance needs redesign before further build investment |
| Semantic retrieval quality is good enough across real heterogeneous sources | Run the retrieval prototype against a representative sample of the pilot org's actual code/docs/wiki content (not synthetic data), score against a small hand-built golden set | If groundedness/relevance scores fall meaningfully short of the ≥90% target in [Problem Statement §11.3](../PRODUCT_PROBLEM_STATEMENT.md#113-ai-performance-criteria) even on hand-picked easy cases, retrieval architecture needs rework before scaling the pilot |
| Permission propagation across sources can be made correct | Design spike + security architecture review of the permission-enforcement approach for each initial source connector type, before writing production code | If the security architecture board identifies an unresolvable gap for any in-scope source type, that source type is descoped from MVP |

## 4. Validation sequencing and gates

```
Week 0-2:  Problem validation (interviews, survey, ticket sampling) -- no code written
Week 2-4:  Concierge-style solution validation (manual/prototype retrieval + LLM synthesis
           on a small real question set) -- minimal code, throwaway if invalidated
Week 4-6:  Permission-model design spike + security review
Gate:      All three validations must clear before MVP build (Program Backlog PI-1) is funded
```

This sequencing is the Lean justification for why [Epic Hypothesis](../06-agile-delivery/EPIC_HYPOTHESIS.md) funding is staged, not committed in full upfront — see that document's funding gate structure.

## 5. What "fit" looks like (exit criteria for this phase)

- Problem validation confirms fragmentation cost is within or above the directional industry benchmark range for this organization.
- Concierge test shows a majority of sampled users rate synthesized, cited answers as more useful than their current search habit.
- Security architecture review confirms a viable permission-enforcement design for at least the two highest-priority source types (code + wiki), with database as a fast-follow.

If any exit criterion fails, the correct response is to revise the Problem Statement and Lean Canvas — not to proceed to MVP build on an unvalidated assumption.
