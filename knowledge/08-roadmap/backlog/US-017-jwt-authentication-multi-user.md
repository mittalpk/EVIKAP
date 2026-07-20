# US-017 — JWT Authentication — Multi-User Token Flow

## User Story

**As a** Platform User,  
**I want to** log in with my organisational credentials and receive a JWT token that is used to authenticate all subsequent API calls,  
**So that** the platform knows who I am, can enforce my permissions, and can attribute my queries to my identity in the audit log.

---

## Description

This story replaces the current single-hardcoded-admin auth path with a proper multi-user JWT authentication flow. For PI-1 it implements local credential validation (username + password stored securely in the DB); OAuth2/SSO integration is a PI-2 extension. The JWT token carries the user's identity and role (from US-016), enabling both the permission filter (US-014) and the RBAC guards (US-016) to function correctly.

---

## Business Value

- Makes the platform usable by multiple pilot users simultaneously with individual identity tracking.
- Establishes `requester_identity` as a verified JWT claim — the foundation of all audit, permission, and compliance work.

---

## Acceptance Criteria

**Given** a user has been registered in the system (by an admin via the user management endpoint),  
**When** the user calls `POST /api/v1/auth/token` with valid credentials,  
**Then:**
- A signed JWT is returned with: `sub` (user identity/email), `role` (from US-016 RBAC), `exp` (configurable TTL, default 8 hours), `iat`.
- The JWT is signed with a secret key stored in the secrets manager (not hardcoded).
- All protected endpoints return HTTP 401 if no JWT is provided, and HTTP 403 if the JWT is valid but the role is insufficient.
- Token expiry is enforced: an expired token returns HTTP 401 (not 403).
- Token signing uses HS256; key rotation is documented (but not automated in PI-1).
- The frontend login form (basic) sends credentials to the auth endpoint and stores the token in `localStorage` (or `sessionStorage`) for subsequent API calls.

---

## Functional Requirements

- FR-006 (Permission-aware retrieval) — `requester_identity` is now a verified JWT sub claim.
- FR-008 (Audit log) — `Query.requester_identity` is populated from the JWT sub claim.

---

## Non-Functional Requirements

- NFR-002 (Security) — JWT signing key stored in secrets manager; password stored as bcrypt hash (not plaintext); token comparison uses constant-time `hmac.compare_digest`.
- NFR-010 (Maintainability) — auth logic is a reusable FastAPI dependency, not repeated per endpoint.

---

## Dependencies

- US-016 (RBAC Foundation) — role claim in the JWT comes from US-016's `user_roles` table.
- `users` DB table (add via Alembic migration in this story or US-016's migration).

---

## Assumptions

- PI-1 auth: username (email) + bcrypt-hashed password in the `users` table. OAuth2/OIDC SSO is PI-2.
- JWT TTL: 8 hours for human users; configurable via `JWT_TTL_SECONDS` env var.
- Refresh tokens are deferred to PI-2.
- The frontend stores the token in `localStorage` for PI-1 (acceptable for a controlled pilot; `httpOnly` cookie is a PI-2 security hardening).

---

## Edge Cases

- **Wrong credentials:** Return HTTP 401 with `{"detail": "Invalid credentials"}`; do not reveal whether the username or password was wrong.
- **Account locked / disabled:** Return HTTP 403 with `{"detail": "Account disabled"}`.
- **JWT signing key not configured:** Service must refuse to start (fail-closed); log a clear error: "JWT_SECRET_KEY not set — refusing to start without a signing key."
- **Token tampered (invalid signature):** Return HTTP 401.

---

## Technical Notes / Implementation Considerations

- **`users` table:** `(id, email, hashed_password, is_active, created_at)`.
- **Auth endpoint:** `POST /api/v1/auth/token` → `{"access_token": "...", "token_type": "bearer", "expires_in": 28800}`.
- **JWT library:** `python-jose` or `PyJWT`; use HS256 with `JWT_SECRET_KEY` from env.
- **Password hashing:** `passlib[bcrypt]`.
- **Auth dependency:** `get_current_user() -> User` — a FastAPI dependency that extracts and validates the JWT, looks up the user, and injects the `User` model. Applied to all protected routes.
- **Frontend login:** A minimal `LoginForm` component in `frontend/src/components/LoginForm.tsx`; stores token in `localStorage`; adds `Authorization: Bearer <token>` header to all API calls via `frontend/src/api/client.ts`.
- **Constant-time comparison:** Ensure password comparison uses `passlib`'s `CryptContext.verify()` which handles timing safety.

---

## Definition of Done

- [ ] `users` table created via Alembic migration (or included in US-016 migration).
- [ ] `POST /api/v1/auth/token` endpoint implemented and returning signed JWT.
- [ ] JWT carries `sub`, `role`, `exp`, `iat`.
- [ ] JWT signing key read from `JWT_SECRET_KEY` env var; service refuses to start if unset.
- [ ] All protected endpoints return HTTP 401 for missing/invalid tokens, HTTP 403 for insufficient role.
- [ ] Expired token returns HTTP 401.
- [ ] Frontend `LoginForm` component implemented; token stored and sent on subsequent requests.
- [ ] Unit tests: valid login, wrong password, expired token, tampered token, missing key.
- [ ] CI passes.

---

## Priority

**High** — Foundation for multi-user pilot; blocks permission enforcement and audit.

## Estimated Effort

**M (Medium)** — ~3–4 days (auth endpoint, JWT dependency, DB migration, frontend login form, tests).

## Related Epics / Features

- FEAT-06 (Permission-aware retrieval — identity verification)
- FEAT-11 (Platform hardening — auth security)
- NFR-002 (Security)
