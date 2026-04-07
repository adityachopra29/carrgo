# Auth System Plan for Carrgo

## Context

Carrgo currently has no authentication — all API endpoints are public and all data is shared. This plan adds email+password JWT auth so each broker sees only their own loads and carriers. The backend already has `python-jose` and `passlib[bcrypt]` in requirements and auth config placeholders (`secret_key`, `algorithm`, `access_token_expire_minutes`) in `config.py`.

## Use Cases

- **Broker registration**: New broker signs up with email, password, name, company name
- **Broker login**: Returns JWT, stored in localStorage, attached to all API calls
- **Data isolation**: Each broker only sees their own loads and carriers (multi-tenant by user_id FK)
- **Session validation**: On page load, frontend validates stored token via `GET /api/auth/me`
- **Logout**: Clears token from localStorage, redirects to login

---

## Backend Changes

### 1. New: `backend/app/models/user.py`

User model with fields: `id` (UUID), `email` (unique, indexed), `hashed_password`, `full_name`, `company_name`, `is_active`, `created_at`. Relationships to Load and Carrier.

Register in `backend/app/models/__init__.py`.

### 2. New: `backend/app/auth.py`

Single module with:
- `hash_password()` / `verify_password()` using passlib bcrypt
- `create_access_token()` using python-jose with settings from config
- `get_current_user` FastAPI dependency — `OAuth2PasswordBearer`, decodes JWT, queries user, raises 401

### 3. New: `backend/app/schemas/user.py`

- `UserRegister` (email, password min 8, full_name, company_name)
- `UserLogin` (email, password)
- `UserResponse` (id, email, full_name, company_name, created_at)
- `TokenResponse` (access_token, token_type, user)

### 4. New: `backend/app/api/auth.py`

Router with prefix `/auth`:
- `POST /api/auth/register` — create user, return token (auto-login)
- `POST /api/auth/login` — verify credentials, return token
- `GET /api/auth/me` — return current user (protected)

Register in `backend/app/api/__init__.py`.

### 5. Add `user_id` FK to Load and Carrier models

- `backend/app/models/load.py` — add `user_id: Mapped[str]` with FK to `users.id`, add relationship
- `backend/app/models/carrier.py` — add `user_id`, change `mc_number` unique constraint to composite `(mc_number, user_id)`

### 6. Protect existing routes

Add `current_user: User = Depends(get_current_user)` to all handlers in:
- `loads.py` — filter by `user_id`, set `user_id` on create
- `carriers.py` — filter by `user_id`, set `user_id` on create/import
- `campaigns.py` — verify load ownership before operating

**Public endpoints (no auth)**:
- `POST /api/webhooks/vapi` — called by Vapi externally
- `GET /api/events/{load_id}` — SSE, left public for simplicity

### 7. DB reset

Since `create_all` is used (no Alembic), delete `carrgo.db` and restart. Update `seed.py` to create a default user and assign carriers to it.

---

## Frontend Changes

### 8. Update types (`frontend/src/types/index.ts`)

Add `User` and `AuthResponse` interfaces.

### 9. Update API client (`frontend/src/lib/api.ts`)

- Read token from `localStorage`, attach `Authorization: Bearer <token>`
- On 401 response, clear token and redirect to `/login`

### 10. New: `frontend/src/lib/auth-context.tsx`

React context provider (`"use client"`):
- State: `user`, `token`, `isLoading`
- On mount: check localStorage for token, validate via `GET /api/auth/me`
- Methods: `login()`, `register()`, `logout()`

### 11. Route restructure

```
app/
  layout.tsx                   ← root: AuthProvider + Toaster only
  login/page.tsx               ← new: login form (no sidebar)
  register/page.tsx            ← new: register form (no sidebar)
  (authenticated)/
    layout.tsx                 ← new: AuthGuard + Sidebar + main wrapper
    page.tsx                   ← existing dashboard (moved)
    loads/                     ← existing (moved)
    carriers/                  ← existing (moved)
```

### 12. New: `frontend/src/components/layout/auth-guard.tsx`

Client component: shows spinner while `isLoading`, redirects to `/login` if no user, renders children if authenticated.

### 13. New: Login and Register pages

- `app/login/page.tsx` — email + password form, shadcn/ui Card/Input/Button
- `app/register/page.tsx` — full name, company, email, password, confirm password

### 14. Update Sidebar

Add user name display and logout button at bottom.

---

## Key Design Decisions

- **Simple JWT in localStorage** — no refresh tokens for now
- **Auto-login on registration** — register returns a token immediately
- **Composite unique constraint** on `(mc_number, user_id)` so different brokers can track the same carrier
- **DB reset required** — no Alembic migrations wired yet
- **24-hour token expiry** — matches existing `access_token_expire_minutes` config

---

## Implementation Order

1. Backend model + auth utilities (steps 1-4)
2. Add user_id FK, protect routes, reset DB (steps 5-7)
3. Frontend auth infra (steps 8-10)
4. Frontend route restructure + pages (steps 11-14)

---

## Verification

1. Start backend → `POST /api/auth/register` with test user → receive token
2. `GET /api/auth/me` with Bearer token → returns user
3. Create load with token → load has `user_id` set
4. List loads without token → 401
5. Register second user → cannot see first user's loads
6. Frontend: open app → redirected to login → login → see dashboard → create load → see it in list → logout → redirected to login
7. Webhook endpoint still works without auth
