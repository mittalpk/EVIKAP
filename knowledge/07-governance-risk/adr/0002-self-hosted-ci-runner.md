# ADR-0002: Move CI job execution to a self-hosted runner

**Status:** Accepted
**Date:** 2026-07-14
**Deciders:** Repository owner

## Context

The GitHub-hosted Actions minutes for the account running this repository reached 90% of the monthly included allowance (2,702 of 3,000 minutes) with 18 days left in the billing cycle, driven by the CI pipeline (`.github/workflows/ci.yml`) running on every push and pull request across an active development period. Continuing on GitHub-hosted runners means either paying for overage or a hard usage cap blocking further CI runs — neither is acceptable for a project meant to demonstrate continuous, working CI/CD practice.

GitHub-hosted Actions minutes are billed; **self-hosted runner minutes are not** — GitHub only meters and bills compute time on its own infrastructure. Moving job execution to a machine already owned and available (this repository's development machine, a WSL2 Linux environment with Docker, Python, and Node already installed) removes the cost constraint entirely rather than just reducing it.

## Decision

Run the `backend-test`, `agent-test`, and `frontend-validate` jobs on a self-hosted runner registered on the local development machine, labeled `[self-hosted, linux, x64]`. The trivial `filter` job (path-filter evaluation only, no dependency installation or test execution) stays on `ubuntu-latest` — it consumes negligible minutes and keeping it hosted means the pipeline doesn't depend on the self-hosted runner being online just to determine which jobs to run.

**Security boundary, non-negotiable:** self-hosted runners execute workflow code with this machine's local privileges and network access. A fork pull request could otherwise run arbitrary code on it. Every self-hosted job's `if:` condition is `github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository` — true for direct pushes and for pull requests from branches within this same repository, false for any fork PR. A workflow run triggered by a fork PR shows these jobs as **skipped**, never executed. This is enforced per-job in the workflow file itself, not left to convention, and is paired with GitHub's own default protection (manual approval required to run any workflow on a first-time contributor's fork PR) — that default is not to be disabled for convenience.

Also added: a `concurrency` group with `cancel-in-progress: true`, so a superseded push cancels the previous run instead of both running to completion — good hygiene regardless of hosting, since local compute isn't infinite either.

## Alternatives considered

- **Reduce trigger frequency instead** (drop the `push: main` trigger, run CI only on PR). Rejected as insufficient on its own — it reduces but doesn't eliminate the cost problem, and removing the `push: main` safety net loses coverage for the case where a change reaches `main` without going through a PR (accidental admin override, for instance) — a real risk while GitHub's own branch-protection *rules* aren't yet configured (see [ADR-0001](0001-adopt-adrs-and-branch-protected-workflow.md), which notes this as an open gap). Kept as a secondary lever (concurrency cancellation) rather than the primary fix.
- **Always-on cloud VM** (e.g., Oracle Cloud's free-tier ARM shape). Rejected for *now*, not permanently — it's genuinely free and always available, unlike a runner tied to a development machine that's only online when that machine is. But it requires provisioning and maintaining infrastructure from scratch, which isn't justified before confirming a self-hosted runner actually solves the problem day to day. Documented below as the defined graduation trigger.
- **Pay for GitHub-hosted overage.** Rejected — this is a portfolio/demo-scale project; paying to run CI at this stage isn't proportionate, and a free alternative exists.

## Consequences

- **Easier:** CI runs no longer consume billed minutes, at all, regardless of push frequency — removes the constraint that motivated this decision entirely rather than partially.
- **Harder:** CI availability now depends on this machine being on and the runner service running. A push made while the machine is off queues until the runner reconnects (GitHub's default job-queue timeout is 24 hours) rather than running immediately. Acceptable for a project with no real-time deployment SLA; would not be acceptable if this repository ever needs to gate a live production deploy on CI passing quickly.
- **Commits us to:** keeping the runner registered, updated, and running as a systemd service (survives reboots without manual restart — confirmed feasible, systemd is active on this machine); periodically rotating the runner's registration if GitHub requires re-authentication; and never relaxing the fork-PR guard above, even if that means an external contribution has to wait for manual approval before its CI can run.

## Graduation trigger (documented now, so the decision to move isn't made reactively later)

Move from this machine to an always-on cloud VM if **any** of the following becomes true:
- CI queue wait time (push → job start) regularly exceeds ~30 minutes because the development machine is asleep/offline when a push happens.
- The project moves from single-maintainer to accepting regular external contributions, making fork-PR-gated CI a routine friction point rather than a rare edge case.
- The machine's availability needs to support something with an actual uptime expectation (e.g., a real pilot deployment gating on CI, per [Technology Architecture — Enterprise profile](../../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6-deployment-profiles)).

This mirrors the same "start cheap, define the trigger, don't guess" pattern already used for the vector-database graduation decision in [Technology Architecture §6a](../../04-solution-architecture/TECHNOLOGY_ARCHITECTURE.md#6a-vector-database-graduation-path).

## Related

[ADR-0001](0001-adopt-adrs-and-branch-protected-workflow.md) · [ADR-0003](0003-dedicated-runner-user.md) (follow-on hardening — dedicated OS user for the runner) · [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) · [`ENGINEERING_STANDARDS.md` §7](../ENGINEERING_STANDARDS.md#7-cicd)
