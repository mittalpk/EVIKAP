# ADR-0003: Run the self-hosted runner as a dedicated, unprivileged system user

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Repository owner

## Context

[ADR-0002](0002-self-hosted-ci-runner.md) established a self-hosted runner on the repository owner's own development machine, with a fork-PR execution guard as the primary defense against untrusted code running on that machine. That guard blocks the *specific* threat of an outside contributor's pull request — but it does not address a narrower, still-real residual risk: every "trusted" job (a direct push, or a same-repo PR) ran as the `pkm` user, the same account used for all other work on this machine — personal projects, SSH keys, `gh` CLI credentials, browser/editor sessions.

That matters because the actual remaining threat isn't "a stranger's fork PR" (already blocked) — it's **supply-chain compromise**: a malicious or typosquatted package pulled in via `pip install -r backend/requirements.txt` or `npm ci` runs with whatever privileges the runner's OS user has. Under the original setup, that was full `pkm`-level access to the whole machine.

Separately, at the time of this decision the repository is **private** — visible only to invited collaborators, not the public. This materially narrows the fork-PR threat surface ADR-0002's guard defends against (a private repo can't receive PRs from arbitrary public forks at all), which shifts relative priority toward hardening the supply-chain/OS-user exposure instead.

## Decision

Run the self-hosted runner as a dedicated, unprivileged system user (`gha-runner`), not the repository owner's personal account. Specifically:

- Created `gha-runner` as a system user (`useradd -r -m`) with its own home directory, locked password (no interactive login — the account exists only to run the service).
- Moved the runner installation to `/home/gha-runner/actions-runner`, owned by `gha-runner:gha-runner`, unreadable by `pkm`.
- Reinstalled the systemd service to run as `gha-runner` (`svc.sh install gha-runner`) rather than the default (whichever user runs the install command).

Net effect: a compromised dependency executing inside a CI job can no longer reach `pkm`'s SSH keys, `gh` CLI token, or other projects on this machine — it's confined to whatever `gha-runner` can access, which is nothing beyond the runner's own working directory.

## Alternatives considered

- **Container-per-job isolation.** Rejected for the same reason a Docker-based runner was rejected in ADR-0002: an ephemeral container per job would wipe the pip/npm/tool caches that make repeat runs fast, reintroducing the problem that motivated moving off GitHub-hosted runners in the first place. A long-lived, non-torn-down container was considered but adds meaningful operational complexity (image maintenance, volume management) for a security improvement the dedicated-user approach already delivers at a fraction of the effort.
- **Do nothing, rely on the fork-PR guard alone.** Rejected — the fork-PR guard defends against a threat (external malicious contributor) that's now largely moot given the repo is private; it does nothing for the supply-chain threat, which is the actual live risk for a single-maintainer private repo.
- **systemd resource limits (`MemoryMax`, `CPUQuota`) without a dedicated user.** Considered as a smaller, complementary step — still worth doing, not yet implemented — but bounding *resource usage* doesn't address *credential/filesystem access*, which was the higher-value gap.

## Consequences

- **Easier:** a compromised job's blast radius is now bounded to the `gha-runner` account, not the developer's full working environment. Read access to `/home/pkm/actions-runner` from the old install is also gone — confirmed via `ls -ld` returning `Permission denied` even for `pkm`.
- **Harder:** the migration wasn't transparent — moving the runner directory broke Python's `pip` script, which has an **absolute path baked into its shebang line** at install time (`#!/home/pkm/actions-runner/.../python`). Moving the directory left that shebang pointing at a path that no longer existed under the new owner, failing every job with `bad interpreter: Permission denied`. Separately, `svc.sh install gha-runner` captures the *invoking* user's `PATH` into a `.path` file regardless of which user the service runs as — since `pkm` ran the install via `sudo`, the job environment leaked `/home/pkm/...` paths that `gha-runner` couldn't read, surfacing as `EACCES` noise on `git` and other tools. Both required wiping `_work` (forcing a fresh Python re-download) and manually resetting `.path` to a plain system `PATH`. Lesson for any future runner user change: **do not `mv` an existing runner directory to change its owning user** — treat it as a fresh install (or at minimum, wipe `_work` and reset `.path` immediately after moving).
- **Commits us to:** keeping `gha-runner`'s password locked and out of any sudoers/docker/admin group — if it's ever added to a privileged group "just to fix something," this hardening is undone. Any future runner reconfiguration should go through a clean `config.sh`/`svc.sh install` under the target user rather than moving an existing installation.

## Related

[ADR-0002](0002-self-hosted-ci-runner.md) · [Issue Log — ISSUE-013](../../08-roadmap/ISSUE_LOG.md#issue-013)
