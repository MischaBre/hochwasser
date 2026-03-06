# Frontend Plan (Auth + Job Management)

## Goal
Build a frontend for user registration, login, and self-service job management on top of the existing API.

## Current Backend Reality
- Auth is bearer JWT verification (Supabase issuer/JWKS), not username/password endpoints in this API.
- Frontend must authenticate against Supabase Auth and send `Authorization: Bearer <token>` to API.
- Job permissions are already enforced server-side:
  - Members can manage their own jobs.
  - Admins can manage all org jobs.
- Key endpoints already available:
  - `GET /v1/me`
  - `GET/POST/PATCH/DELETE /v1/jobs`
  - `GET /v1/jobs/{job_uuid}/status`
  - `GET /v1/jobs/{job_uuid}/outbox`
  - Admin endpoints under `/v1/admin/*`

## Scope (v1)
- Auth UI:
  - Register
  - Login
  - Logout
  - Session persistence
- Jobs UI:
  - List jobs (default enabled only)
  - Create job
  - Edit own job
  - Soft-delete own job
  - View job status
  - View job outbox entries
- Basic account area:
  - Show current user and role from `/v1/me`
- Error handling:
  - `401` (not authenticated), `403` (not allowed), `404`, validation errors

## Proposed Tech Stack
- Vue 3 + TypeScript + Vite
- Vue Router
- Pinia + Vue Query (for shared state and API state/caching)
- Tailwind CSS
- shadcn-vue style UI primitives (local `components/ui` on Tailwind)
- Supabase JS client for auth
- Lightweight schema-aligned custom validation with field-level client/server mapping

## Architecture
- `frontend/` (new app)
- Core modules:
  - `auth/` (Supabase client, auth context, route guards)
  - `api/` (typed API client with bearer token injection)
  - `features/jobs/` (list, create/edit form, details/status/outbox)
  - `pages/` (Login, Register, Dashboard, JobForm, JobDetails)
  - `components/` (shared UI primitives, layout, feedback states)
- Environment variables:
  - `VITE_API_BASE_URL` (e.g. `http://localhost:8080`)
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_PUBLISHABLE_KEY`

## Current Status
- Phase 1 complete.
- Phase 2 complete.
- Phase 3 complete.
- Phase 4 complete.
- Phase 5 complete.
- Phase 6 complete.
- Phase 7 deferred (post-MVP hardening).
- Phase 8 mostly complete (map picker follow-up pending).
- Phase 9 in progress (PR1 runtime foundation underway).

## Delivery Phases

### Phase 1: Frontend Bootstrap
- [x] Initialize Vite + Vue + TypeScript app.
- [x] Add Vue Router, base layout, auth composables, and route guards.
- [x] Configure Tailwind CSS tokens/utilities and base design primitives.
- [x] Establish shared UI component primitives under `frontend/src/components/ui`.
- [x] Add `.env.example` for frontend variables.

### Phase 2: Authentication
- [x] Implement register/login forms via Supabase Auth.
- [x] Implement auth state listener and token retrieval.
- [x] Protect app routes; redirect unauthenticated users to login.

### Phase 3: API Integration
- [x] Build API client that attaches JWT from Supabase session.
- [x] Implement global handling for `401`/`403` and validation errors.
- [x] Add `GET /v1/me` call on app load to confirm membership/role.

### Phase 4: Jobs Management UI
- [x] Jobs list page (`GET /v1/jobs`).
- [x] Create job form (`POST /v1/jobs`) with client-side validation aligned to backend schema.
- [x] Edit job form (`PATCH /v1/jobs/{job_uuid}`).
- [x] Delete action (`DELETE /v1/jobs/{job_uuid}` with optimistic UI refresh).
- [x] Job details:
  - Status panel (`/status`)
  - Outbox table with pagination (`/outbox?limit&offset`)
- [x] Field-level validation UX in job form (inline errors per input + server validation issue mapping).

### Phase 5: UX Hardening
- [x] Loading, empty, and error states for all views.
- [x] Inline messages for success/failure and validation.
- [x] Confirm dialogs for destructive actions.
- [x] Mobile-friendly responsive layout.

### Phase 6: Local Dev + Deployment Integration
- [x] Add frontend service to `docker-compose.yml`.
- [x] Set `API_CORS_ALLOW_ORIGINS` to frontend origin(s).
- [x] Verify full local flow: register -> login -> create/edit/delete/view jobs.
- [x] Document run instructions in `README.md`.

### Phase 7: Testing
- [ ] Unit tests for auth and API client behavior.
- [ ] Component tests for key forms and table states.
- [ ] Use a dedicated integration test database via `API_TEST_DATABASE_URL` (no fallback to dev DB URLs).
- [ ] Optional E2E smoke flow:
  - Login
  - Create job
  - Edit job
  - Delete job

Testing is intentionally deferred while frontend delivery is in flow. Revisit Phase 7 in a later hardening stage.

### Phase 8: Station Discovery And Enriched Job Context
- [x] Add API endpoint to fetch Pegelonline stations with search/filter and short-lived caching.
- [x] Replace manual `station_uuid` entry in job form with searchable station picker.
- [x] Keep UUID as the persisted value while showing human-readable station metadata in form.
- [x] Enrich jobs list/details with station name, water body, agency, and coordinates where available.
- [ ] Evaluate map picker as optional follow-up after searchable dropdown baseline.

### Phase 9: Public VM Deployment

Deployment direction (recommended):

- Keep Supabase managed for Postgres + Auth.
- Run alert engine and API on one VM via Docker Compose.
- Serve frontend as static production build (not Vite dev server).
- Put a reverse proxy in front (Caddy recommended) for HTTPS and domain routing.
- Restrict API CORS to real frontend domain(s) only.

#### 9.1 Architecture And Runtime Topology
- [ ] Finalize public domains:
  - `app.<domain>` for frontend
  - `api.<domain>` for API
- [ ] Keep DB/Auth external in Supabase (no public DB port on VM).
- [ ] Confirm Compose profile usage in production (`COMPOSE_PROFILES=prod`).

#### 9.2 Frontend Production Serving
- [x] Add a production frontend image/container (multi-stage build + static server).
- [x] Remove production dependency on `npm run dev`.
- [x] Ensure `VITE_API_BASE_URL` points to `https://api.<domain>`.
- [x] Keep `hochwasser-frontend` dev-only for local workflow.

#### 9.3 Reverse Proxy And TLS
- [x] Add reverse proxy service in production compose (Caddy preferred).
- [x] Route frontend and API by hostnames.
- [x] Enable automatic Let's Encrypt certificates.
- [x] Expose only `80/443` publicly.

#### 9.4 Security Hardening
- [ ] Tighten `API_CORS_ALLOW_ORIGINS` to production frontend origin(s).
- [ ] Keep secrets only in VM `.env` (never in git).
- [ ] Set strong non-default values for all credentials.
- [ ] Configure VM firewall (`22`, `80`, `443` only).
- [ ] Use SSH keys and disable password login where possible.

#### 9.5 Operations And Reliability
- [x] Add a deployment runbook for first deploy and updates.
- [x] Add uptime checks for `/health` and `/health/live`.
- [ ] Extend runbook with explicit rollback procedure and verification drill.
- [ ] Define backup/restore expectations (Supabase backups + config backup).
- [ ] Document log access and incident triage steps.

#### 9.6 CI/CD And Release Workflow
- [x] Add a simple release path (manual script with env validation + smoke checks).
- [ ] Deploy from tagged versions or protected `main` only.
- [x] Include `docker compose pull/build/up -d` and quick post-deploy smoke checks.

#### 9.7 Legal Notice And Liability Clarification
- [ ] Add a visible legal notice section in public docs and frontend footer/imprint page.
- [ ] State clearly that station/water-level data is sourced from official public providers (for example Pegelonline) and is not owned by this project.
- [ ] State clearly that this service is informational support only and does not replace official warnings, emergency alerts, or civil protection guidance.
- [ ] State clearly that no guarantee is given for availability, correctness, completeness, timeliness, or alert delivery.
- [ ] State clearly that operators/maintainers are not liable for damages caused by delayed, missing, or incorrect alerts.
- [ ] Add jurisdiction-specific review item: have the final legal wording reviewed by qualified legal counsel before public launch.

#### 9.8 Public Landing Page And Visual Theme
- [ ] Add a public landing page (outside authenticated app views) explaining what the service does, who it is for, and how to get started.
- [ ] Define and implement an intentional visual theme (typography, color tokens, spacing, icon style) that feels distinctive and trustworthy.
- [ ] Add responsive hero, feature highlights, and clear CTA paths (login/register/status/docs).
- [ ] Update browser metadata for public launch: final page title and favicon.
- [ ] Favicon design direction: stylized Pegelmessstange in black/yellow palette (clean, recognizable at small sizes) with PNG plus `.ico` fallback.
- [ ] Add a visible "Buy me a coffee" support link to profile `micbrey` in the frontend (for example footer or profile/account area).
- [ ] Redesign authenticated dashboard landing view to focus on job overview cards instead of session/account blocks.
- [ ] Show reduced key info per job card (station, limit, status, last update) with quick links to details/edit.
- [ ] Add optional live Pegel trend chart per job card (or compact sparkline fallback) aligned with the alert email chart style.
- [ ] Ensure the landing page links to legal notice/imprint and data source disclosure.
- [ ] Validate accessibility basics (contrast, keyboard navigation, focus states, reduced-motion support).

#### Phase 9 Exit Criteria
- [ ] Public HTTPS frontend and API reachable by domain.
- [ ] Auth works end-to-end from public frontend against public API.
- [ ] Alert engine runs continuously with healthy status.
- [ ] CORS is locked to intended origins.
- [ ] Rollback procedure tested once.
- [ ] Legal notice is published and reviewed.
- [ ] Public landing page is live with final visual theme.

## Definition of Done
- User can register and login from frontend.
- Authenticated user can create and manage own jobs.
- Role and identity are visible via `/v1/me`.
- API errors are handled clearly in UI.
- Works in local Docker setup with correct CORS.
- Basic tests pass and `README.md` is updated.

## Risks / Notes
- Registration/login depends on Supabase project configuration (email provider, redirect URLs, etc.).
- API auto-provisions members depending on `API_AUTO_PROVISION_MEMBERS`; if disabled, login can succeed but API access may still be denied.
- Ensure frontend and API origins are consistent with CORS settings.

## Out of Scope (for v1)
- Full admin console for member role changes and audit logs.
- Advanced design system/theming.
- Internationalized UI copy.
