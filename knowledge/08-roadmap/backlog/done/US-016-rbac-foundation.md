# US-016 — RBAC Foundation — Replace Single Hardcoded Admin

**Status:** Completed & Archived · 2026-07-24

## User Story


**As a** Platform Administrator,  
**I want to** manage user roles (admin, user, viewer) in the platform and have role-based access enforced on all admin endpoints,  
**So that** the system is no longer dependent on a single hardcoded admin credential and multiple team members can safely access the platform with appropriate permissions.

---

## Description

The current implementation uses a single hardcoded admin identity with no multi-user support. This story implements the foundational RBAC layer: a `Role` and `UserRole` database table, role assignment, and role-based endpoint guards on admin-only routes. It is scoped to PI-1 as a "Must" item for NFR-002. Full RBAC with fine-grained source-level permissions is a PI-2 extension.

---

## Business Value

- Removes a known security gap: the single hardcoded admin is a single point of failure and incompatible with multi-user pilot deployment.
- Satisfies the NFR-002 PI-1 slice requirement: "RBAC foundation replacing the single-hardcoded-admin model."
- Enables the pilot to onboard multiple team members with appropriate access levels.

---

## Acceptance Criteria

**Given** the RBAC foundation is implemented,  
**When** a user calls an admin-only endpoint (e.g., source registration, audit log retrieval),  
**Then:**
- The request is rejected with HTTP 403 if the requester's JWT does not carry the `admin` role.
- A user with the `user` role can query but cannot access admin endpoints.
- A user with the `viewer` role can only view query results; cannot submit new queries.
- Role assignment is done via a seeded admin user (the bootstrap admin) who can assign roles to other users via an internal admin endpoint.
- All role assignments are logged in the audit trail.
- The hardcoded admin credential is removed from application source code and configuration.

---

## Functional Requirements

- FR-006 (Permission-aware retrieval) — RBAC is the platform-level access model.
- FR-008 (Audit log) — role assignment actions logged.

---

## Non-Functional Requirements

- NFR-002 (Security) — role enforcement must use constant-time JWT claim validation; role must be checked server-side, not trusted from client input.
- NFR-010 (Maintainability) — role checks are a reusable FastAPI dependency, not repeated inline per endpoint.

---

## Dependencies

- US-017 (JWT authentication multi-user flow) — JWT tokens carry role claims; this story depends on tokens carrying a valid `role` field.
- Alembic migration for `roles` and `user_roles` tables.

---

## Assumptions

- Roles for PI-1: `admin`, `user`, `viewer`. Additional roles (e.g., `source-owner`) are PI-2 extensions.
- JWT tokens are issued by the backend's auth endpoint (US-017) and include a `role` claim.
- The bootstrap admin user is seeded at database initialisation time (not hardcoded in config).

---

## Edge Cases

- **JWT token carries an unknown role:** Treat as `viewer` (minimum privilege); log a warning.
- **Role assignment attempted by a non-admin:** Return HTTP 403.
- **Bootstrap admin user deleted:** Require at least one admin user to remain; enforce this constraint at the DB level (prevent deletion of the last admin).

---

## Technical Notes / Implementation Considerations

- **DB tables:** `roles (id, name)`, `user_roles (user_id FK, role_id FK, assigned_by, assigned_at)`.
- **FastAPI dependency:** `require_role(role: str)` → a callable that extracts the `role` claim from the JWT and raises `HTTPException(403)` if the required role is not present.
- **Admin endpoint guard:** Apply `Depends(require_role("admin"))` to all source registration, audit log, and user management endpoints.
- **Bootstrap seed:** A DB seed script (`scripts/seed_admin.py`) creates the initial admin user with a securely generated credential; run once at deployment.
- **Hardcoded admin removal:** Search `backend/app/` for the existing hardcoded admin reference and replace it with the seeded admin lookup.

---

## Definition of Done

- [x] `roles`, `users`, and `user_roles` tables created via Alembic migration (`backend/alembic/versions/0004_rbac_foundation.py`).
- [x] `require_role` FastAPI dependency implemented (`backend/app/auth.py`).
- [x] Admin-only endpoints guarded (source registration, audit log, user management).
- [x] Bootstrap admin seed script created (`scripts/seed_admin.py`).
- [x] Hardcoded admin credential replaced with DB/JWT role checks (`backend/app/services/rbac_service.py`).
- [x] Role assignment endpoint implemented and guarded (`POST /api/v1/auth/roles/assign`, `backend/app/routers/auth.py`).
- [x] Role assignment logged in audit trail (`assign_user_role`).
- [x] Unit tests: role enforcement on each endpoint type (`admin`, `user`, `viewer`, `backend/tests/test_rbac_foundation.py`).
- [x] CI passes (`python3 -m pytest backend/tests -v`, `python3 -m pytest agent/tests -v`, `cd frontend && npm run build`).


---

## Priority

**High** — Required for multi-user pilot deployment; NFR-002 PI-1 slice.

## Estimated Effort

**M (Medium)** — ~3–4 days (DB tables, dependency, endpoint guards, seed script, tests).

## Related Epics / Features

- FEAT-06 (Permission-aware retrieval — platform-level RBAC)
- FEAT-11 (Platform hardening — RBAC foundation)
- NFR-002 (Security)
