# US-034 — Model / System Card Publication

## User Story

**As an** AI Solutions Architect / Compliance Officer,  
**I want to** generate and publish a versioned Model/System Card for every production deployment of the retrieval and agent-orchestration pipeline — documenting its purpose, capabilities, known limitations, evaluation scores, and last-updated date — so that any reviewer can locate a current card for any production release without engineering assistance.

---

## Description

This story implements FR-013: a CI-triggered process that, on merge to `main`, generates a Markdown Model/System Card from the latest `EvaluationRun` record and publishes it (committed to the repository under `knowledge/model-cards/` or an external registry). The card's evaluation scores must match the evaluation harness's own record for that pipeline version.

---

## Business Value

- Satisfies NFR-012 (Governance and transparency): every production pipeline version has a published card whose scores match the evaluation record.
- Makes VigilRAG's AI governance claims verifiable by non-engineers — a requirement for any regulated pilot or enterprise sign-off.
- The `EvaluationRun` history seeded in US-021/US-022 makes this story possible; the schema was designed to support it from day one.

---

## Acceptance Criteria

**Given** a merge to `main` triggers CI and the evaluation gate passes (US-023),  
**When** the Model/System Card publisher runs,  
**Then:**
- A Markdown card is generated at `knowledge/model-cards/v<pipeline_version>-card.md`.
- The card includes: pipeline version (git SHA), purpose, capabilities, known limitations, RAGAS scores (faithfulness, context_precision, context_recall), dataset version used, evaluation run ID, published date.
- The card's RAGAS scores match exactly the `EvaluationRun` record for the same `pipeline_version`.
- The card is committed to the repository (or published to a configured external URL) as a CI step.
- A `GET /api/v1/model-cards/latest` endpoint returns the most recent card's content (admin-accessible).
- A reviewer can locate the current card for any production release from the `knowledge/model-cards/` directory without engineering assistance.

---

## Functional Requirements

- FR-013 (Model/System Card publication).

---

## Non-Functional Requirements

- NFR-012 (Governance and transparency — card scores must match the evaluation harness record).

---

## Dependencies

- US-021/US-022 (`EvaluationRun` records exist and are queryable).
- US-023 (CI evaluation gate — card publisher runs after the gate passes, not before).

---

## Assumptions

- Card publication is a CI step (GitHub Actions script), not a running service.
- The card is a Markdown file committed to the repository. Publishing to an external registry (Confluence, SharePoint) is a PI-2 stretch; the committed Markdown file is sufficient for the acceptance check.
- `pipeline_version` = the git commit SHA of the merge commit.

---

## Edge Cases

- **No `EvaluationRun` record for the current `pipeline_version`:** Do not publish a card; fail the CI step with "No evaluation run found for this pipeline version — card cannot be published without a quality record."
- **Card already exists for this `pipeline_version`:** Overwrite; do not create a duplicate.

---

## Technical Notes / Implementation Considerations

- **Publisher script:** `scripts/publish_model_card.py` — reads the latest `EvaluationRun` for the current `pipeline_version`, renders a Markdown card from a Jinja2 template, and writes it to `knowledge/model-cards/`.
- **CI step (added to `ci.yml` after the evaluation gate):**
  ```yaml
  - name: Publish Model/System Card
    if: github.ref == 'refs/heads/main'
    run: |
      python scripts/publish_model_card.py --version ${{ github.sha }}
      git config user.name "VigilRAG CI"
      git add knowledge/model-cards/
      git commit -m "ci: publish model card for ${{ github.sha }}"
      git push
  ```
- **Card template sections:** Title, Pipeline Version, Published At, Purpose, Capabilities, Known Limitations, Data Sources (source types indexed), Evaluation Results (RAGAS table), Evaluation Run ID, Dataset Version, **Governance Framework Mapping** (a real mapping to NIST AI RMF or ISO/IEC 42001 function areas — e.g., "GOVERN 1.1: AI risk policies → [Compliance & Security Framework §2](...)", not a placeholder), AI Risk Tier.
- **`GET /api/v1/model-cards/latest`:** Reads the most recent card file from the filesystem (or a `model_cards` DB table); admin-only.
- **Annual governance review:** The first annual review is scheduled as a recurring calendar event (AI Solutions Architect + Compliance Officer) at the time this story is completed. The review confirms the governance-framework mapping in the published card is still current. This is NFR-012's second verification clause.

---

## Definition of Done

- [ ] `scripts/publish_model_card.py` implemented with Jinja2 template.
- [ ] Card published to `knowledge/model-cards/v<sha>-card.md` on `main` merge.
- [ ] Card scores match the `EvaluationRun` record for the same version (verified by CI).
- [ ] Card template includes a real (not placeholder) Governance Framework Mapping section (NIST AI RMF or ISO/IEC 42001 function-area mapping).
- [ ] CI step added to `ci.yml` (runs after evaluation gate, on `main` only).
- [ ] `GET /api/v1/model-cards/latest` endpoint implemented and admin-only.
- [ ] Acceptance check: reviewer can locate any production release's card from `knowledge/model-cards/` without engineering help.
- [ ] First annual governance framework mapping review scheduled as a recurring calendar event (AI Solutions Architect + Compliance Officer).
- [ ] Unit tests: card generation from a mock `EvaluationRun` record.
- [ ] CI passes.

---

## Priority

**Medium** (Stretch in PI-2 per PI planning objectives).

## Estimated Effort

**M (Medium)** — ~2–3 days (publisher script, Jinja2 template, CI step, API endpoint, tests).

## Related Epics / Features

- FEAT-19 (Model/System Card publication)
- FR-013
- NFR-012 (Governance and transparency)
