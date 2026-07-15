# ADR-0005: Move self-hosted CI to a dedicated Linux Mint machine

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Repository owner

## Context

[ADR-0004](0004-remove-self-hosted-runner.md) removed self-hosted CI from the WSL machine and reverted to GitHub-hosted runners. That removal was itself the correct fix to a real problem: the WSL runner was registered on the repository owner's **daily-use development machine**, not a dedicated box — meaning any compromised dependency in `pip install`/`npm ci` ran with the full privileges of that machine's primary account (mitigated partially by [ADR-0003](0003-dedicated-runner-user.md)'s unprivileged `gha-runner` user, but the machine itself still held the owner's SSH keys, other projects, and daily work).

A generalized runbook exists (`~/docs/self-hosted-github-runner-setup.md`, written from a real self-hosted runner build for the NexVocab repo) whose first principle is exactly this: **use a dedicated machine, not your daily-use dev box.** The repository owner has a machine available to serve as that dedicated box, running **Linux Mint 22.3 ("Zena", Ubuntu 24.04/noble-based)** — this is the *exact* distro the generalized runbook was written from, including its documented gotchas.

**Correction to this ADR's own history:** this decision was initially drafted assuming the dedicated machine was an Intel MacBook running macOS, based on it being described as "the MacBook" without confirming the installed OS. SSH access revealed a Debian-family Linux userland (`/usr/lib/python3/dist-packages`, missing `sw_vers`), and direct confirmation established it's Linux Mint — the MacBook's *hardware*, running Mint instead of macOS. The macOS-specific content (Homebrew, `sysadminctl`/`dscl`, `launchd`, `pmset`) below was replaced before any of it was executed on the actual machine; nothing macOS-specific was ever applied.

## Decision

Stand up a self-hosted runner on the dedicated Linux Mint machine, following the hardened, previously-battle-tested pattern from the generalized runbook — which requires no distro adaptation this time, since it was written for this exact OS:

- **Dedicated OS account** (`gha-runner-omeganexus`), created via `useradd -r -m`, password locked (`passwd -l`) — no interactive login, only used by systemd's `User=` directive to run the service.
- **No Docker** — `ci.yml` doesn't use Docker in any step, so the Docker-group root-equivalence caveat from the runbook doesn't apply; skipped rather than installed unnecessarily.
- **Python 3.12 already present system-wide** (Mint 22.3's default `python3`) — no deadsnakes PPA needed, unlike the runbook's Mint 21.x example. **Node 20 via NodeSource**, since Mint's own apt-packaged Node version doesn't match what the frontend build targets.
- **`actions/setup-python`/`actions/setup-node` removed from `ci.yml` entirely** — this is the runbook's documented, previously-hit failure mode for Linux Mint specifically (`The version 'X.Y' ... was not found for <Distro> <Version>` — these actions match against a `versions-manifest.json` that doesn't recognize Mint by name, even though it's ABI-compatible with the Ubuntu release it's based on). Workflow steps reference the system-installed `python3.12`/`node` directly instead.
- **Python steps always use a venv** (`python3.12 -m venv .venv`), never a bare system `pip install` — the runbook's second documented gotcha: without a venv, pip can resolve compiled-extension packages (`cryptography`, pulled in transitively via `pyjwt`) against the distro's own `/usr/lib/python3/dist-packages`, which can be built against a different Python ABI than the one actually running, causing a hard crash on import (`pyo3_runtime.PanicException`) rather than an install-time error.
- **`.path` reset applied proactively** at initial setup — `runsvc.sh` replaces `PATH` entirely from this file's contents, a gotcha already paid for once on the WSL machine ([ISSUE-013](../../08-roadmap/ISSUE_LOG.md#issue-013)) and independently documented in the runbook for exactly this reason.
- **`ci.yml` updated**: `backend-test`, `agent-test`, `frontend-validate` target `runs-on: [self-hosted, omeganexus-mint]`; the fork-PR execution guard from [ADR-0002](0002-self-hosted-ci-runner.md) is restored; no `actions/cache` inputs, for the same reason as [ISSUE-012](../../08-roadmap/ISSUE_LOG.md#issue-012) — this runner is persistent, so local pip/npm caches survive between jobs without GitHub's remote cache round-trip (moot here anyway, since `setup-python`/`setup-node` — the actions that offer that input — aren't used at all).
- **SSH hardening and always-on power settings** per the runbook (§8–9), Linux-native this time (`systemd-logind`, `ufw`, `sshd_config` — no macOS translation needed).

## Alternatives considered

- **Stay on GitHub-hosted (ADR-0004's end state).** Rejected as a long-term answer for the same reason noted there — it doesn't address the CI-minute constraint that motivated self-hosting in the first place, only defers it.
- **Repeat the WSL setup exactly, accept the daily-driver risk.** Rejected — this is precisely the anti-pattern the generalized runbook opens with, and precisely what [ADR-0004](0004-remove-self-hosted-runner.md) was written to undo.
- **Keep chasing macOS-specific setup after discovering the machine runs Mint.** Rejected immediately once confirmed — there is no macOS host to configure; continuing down that path would have meant executing commands that could not possibly succeed, discovered as `sudo: sysadminctl: command not found`-class failures instead of before they were attempted.

## Consequences

- **Easier:** the exact runbook this decision follows already has its Linux Mint gotchas documented and fixed from a real prior build (NexVocab) — no live discovery needed for the distro-specific failure modes this time, only for anything genuinely new to this repo's setup.
- **Harder:** `ci.yml`'s Python/Node steps are now less standard (no `actions/setup-python`/`actions/setup-node`, manual venv management) — a maintainability cost accepted specifically because the alternative (those actions) doesn't work on this distro at all, not a stylistic preference.
- **Commits us to:** keeping this machine's dedicated status meaningful (no unrelated software installed on it, `gha-runner-omeganexus` used only for this runner), and re-verifying `/etc/os-release` before assuming any future machine change is a drop-in replacement — this ADR's own history is the concrete argument for why that assumption isn't safe to skip.

## Verification

- [ ] Runner shows `online` in `mittalpk/OmegaNexus` → Settings → Actions → Runners
- [ ] A real `workflow_dispatch` run completes successfully end-to-end on the new runner
- [ ] `gha-runner-omeganexus` confirmed to have no SSH access and is not in `sudo`/`docker` groups
- [ ] `ufw status verbose` shows deny-by-default with only the intended LAN-restricted SSH rule (if SSH is kept enabled at all)
- [ ] Sleep/power settings confirmed to keep the machine online while plugged in

## Related

[ADR-0002](0002-self-hosted-ci-runner.md) · [ADR-0003](0003-dedicated-runner-user.md) · [ADR-0004](0004-remove-self-hosted-runner.md) · `~/docs/self-hosted-github-runner-setup.md` (generalized runbook, outside this repo — written from this exact distro) · [Issue Log — ISSUE-012, ISSUE-013](../../08-roadmap/ISSUE_LOG.md)
