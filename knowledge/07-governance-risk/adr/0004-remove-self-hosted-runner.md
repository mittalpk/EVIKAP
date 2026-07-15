# ADR-0004: Remove the self-hosted CI runner, return to GitHub-hosted

**Status:** Accepted (this ADR's own decision — removing self-hosting from the WSL *daily-driver* machine specifically — remains valid; see [ADR-0005](0005-linux-mint-self-hosted-runner.md) for the follow-up decision to self-host again, this time on a genuinely dedicated machine, which changes `ci.yml` again but does not undo the reasoning here)
**Date:** 2026-07-15
**Deciders:** Repository owner
**Supersedes:** [ADR-0002](0002-self-hosted-ci-runner.md), [ADR-0003](0003-dedicated-runner-user.md)

## Context

[ADR-0002](0002-self-hosted-ci-runner.md) moved CI job execution to a self-hosted runner on the repository owner's development machine to eliminate GitHub Actions minute consumption after hitting 90% of the monthly included allowance. [ADR-0003](0003-dedicated-runner-user.md) followed up by isolating that runner under a dedicated, unprivileged OS user rather than the owner's personal account.

The repository owner subsequently directed that the self-hosted runner be removed from this repository. This ADR does not second-guess that direction — it records the reversal and what it costs, consistent with this project's practice of documenting decisions (and their undoing) rather than silently reverting.

Notably, by the time this decision was implemented, the runner had already gone offline on GitHub's side on its own (`GET /repos/mittalpk/OmegaNexus/actions/runners` returned zero registered runners, and the local systemd service was inactive) — so no live deregistration was required; only local cleanup (stopping/uninstalling the service, deleting the dedicated OS user) and reverting `ci.yml`.

## Decision

- Reverted `.github/workflows/ci.yml`: all three test/build jobs (`backend-test`, `agent-test`, `frontend-validate`) run on `ubuntu-latest` again instead of `[self-hosted, linux, x64]`.
- Restored the `cache: 'pip'` / `cache: 'npm'` inputs on `actions/setup-python` / `actions/setup-node` — these were deliberately removed in [ISSUE-012](../../08-roadmap/ISSUE_LOG.md#issue-012) because they were actively harmful on a *persistent* self-hosted runner (uploading a machine-wide, multi-GB cache), but they're the *correct* configuration again on ephemeral GitHub-hosted runners, where each job gets a ephemeral, empty cache directory and the upload/download round-trip is exactly what makes repeat installs fast.
- Removed the fork-PR execution guard (`if: ... github.event.pull_request.head.repo.full_name == github.repository`) from each job — that guard existed specifically to protect a self-hosted machine from executing untrusted fork-PR code; GitHub-hosted runners are already ephemeral, isolated VMs per job, so the guard is dead complexity with no self-hosted machine left to protect.
- Kept the `concurrency` group, the explicit `permissions` block, and the `python -m pytest` invocation fix ([ISSUE-011](../../08-roadmap/ISSUE_LOG.md#issue-011)) — none of these are self-hosted-specific; they're correct regardless of where jobs run, and reverting them would reintroduce problems that were never about hosting choice.
- Locally: stopped and uninstalled the `gha-runner`-owned systemd service, and deleted the `gha-runner` system user and its home directory (runner binaries, registration, and warmed Python/pip/npm caches) per the repository owner's explicit choice of full cleanup over partial.

## Consequences

- **Easier:** no machine dependency for CI to run — a push triggers a job immediately on GitHub's infrastructure regardless of whether the development machine is on. No OS-level attack surface (dedicated user, docker-group exposure, etc.) to reason about for this repository anymore.
- **Harder:** GitHub Actions minutes are billed again. The original problem ADR-0002 solved (90% of the monthly allowance consumed) has not been re-solved — reverting this decision without also addressing minute consumption (e.g., by keeping the `push: main` trigger lean, or by re-visiting self-hosting later under different constraints) means that pressure returns the next time development activity is high.
- **Commits us to:** if minute pressure returns, re-evaluate self-hosting on its own merits rather than assuming ADR-0002/0003's exact setup is the right answer a second time — the operational cost (this ADR exists because the *previous* setup was judged not worth maintaining) is real evidence to weigh, not just the cost figures from the original decision.

## Related

[ADR-0002](0002-self-hosted-ci-runner.md) (superseded) · [ADR-0003](0003-dedicated-runner-user.md) (superseded) · [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) · [Issue Log](../../08-roadmap/ISSUE_LOG.md)
