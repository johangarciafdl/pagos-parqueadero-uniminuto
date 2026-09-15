# Implementation Plan: Pagos electrónicos del parqueadero vía UWallet

**Spec**: `./spec.md` | **Constitution**: `../../.specify/memory/constitution.md`

## Stack técnico (decidido)

- **Backend**: FastAPI + SQLModel + PostgreSQL + Alembic, sobre la base de
  `fastapi/full-stack-fastapi-template` (ya copiado a `backend/`).
- **Frontend**: React + Vite + TypeScript + shadcn/ui + Tailwind (ya copiado a `frontend/`).
- **Pagos**: API REST de Wompi (sandbox) vía `httpx`, sin SDK de terceros.
- **Infra local**: Docker Compose (`compose.yml`, ya copiado) con Postgres + backend + frontend.
- **Despliegue**: Render/Railway (app) + Neon/Supabase (Postgres gestionado).
- **Spec-driven dev**: spec-kit (`.specify/`, `.claude/skills/speckit-*`).

## Mapeo del template base -> nuestro dominio

El template trae de fábrica (reutilizar tal cual, ya probado por la comunidad):

- `backend/app/core/security.py`: hashing de contraseñas (bcrypt vía passlib) + creación/
  verificación de JWT. **Reutilizar sin cambios.**
- `backend/app/core/config.py`: settings vía `pydantic-settings` leyendo `.env`. **Extender** con
  `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_EVENTS_SECRET`, `WOMPI_BASE_URL`.
- `backend/app/core/db.py`: engine/sesión SQLModel. **Reutilizar sin cambios.**
- `backend/app/api/deps.py`: dependencia `get_current_user` a partir del JWT. **Reutilizar**, y
  agregar aquí el punto de extensión `AuthProvider` (constitución, principio II).
- `backend/app/models.py`: modelo `User` base + ejemplo `Item` (a eliminar). **Reemplazar `Item`
  por nuestras entidades** (ver Data Model abajo).
- `backend/app/api/routes/login.py`: login por email/password + JWT. **Es nuestro "mock
  UWallet"**: se mantiene como adaptador `MockAuthProvider`; en el futuro, un
  `UWalletSSOProvider` implementa la misma interfaz de `deps.py` sin tocar rutas de negocio.
- `frontend/src/`: cliente generado por OpenAPI (`openapi-ts`), componentes shadcn/ui, rutas con
  TanStack Router. **Reutilizar la base de auth/routing**, agregar páginas para los 4 módulos.

## Data Model (extiende `backend/app/models.py`)

- `Vehicle(id, user_id, plate, type[car|moto])`
- `PaymentMethodCatalog(id, code, name)` — catálogo: tarjeta, nequi, pse, transferencia
- `PaymentStatusCatalog(id, code, name)` — catálogo: pending, approved, declined, cancelled
- `Payment(id, user_id, vehicle_id, amount, method_id, status_id, wompi_reference UNIQUE,
  concept, created_at, updated_at)`
- `Plan(id, name, vehicle_type, price, duration_days, conditions)`
- `Subscription(id, user_id, plan_id, start_date, end_date, active)`
- `ParkingLog(id, payment_id, user_id, action, created_at)` — bitácora inmutable
- `SupportTicket(id, user_id, case_number UNIQUE, subject, message, status, created_at)`
- `FAQ(id, category, question, answer)`

Todas las FK con `ondelete="CASCADE"` donde aplique (patrón que ya usa el template).
Cada tabla nueva = una migración Alembic (`alembic revision --autogenerate`).

## Integración Wompi (User Story 1)

1. `POST /api/v1/payments/` (nuestro backend): crea `Payment` en estado `pending`, arma la
   firma de integridad (`SHA256(reference + amount_in_cents + currency + integrity_secret)`)
   requerida por el widget de Wompi, y la devuelve al frontend.
2. Frontend abre el Widget/Checkout de Wompi con esa firma (nunca se genera la firma en el
   cliente).
3. `POST /api/v1/webhooks/wompi` (público, sin JWT): valida el header de firma del evento con
   `WOMPI_EVENTS_SECRET` (HMAC-SHA256). Si es válida y la transacción no fue procesada antes
   (idempotencia por `wompi_reference`), actualiza `Payment.status` y crea el `ParkingLog`.
4. El frontend hace polling corto (o refresco manual) sobre `GET /api/v1/payments/{id}` para
   reflejar el estado real, nunca asume éxito solo porque el checkout se cerró.

## Seguridad (checklist OWASP aplicado)

- Inyección: SQLModel/SQLAlchemy parametrizado en el 100% de las consultas.
- Auth roto: JWT corto + refresh, bcrypt para passwords (ya en el template).
- Exposición de datos: `.env` fuera de git, `SECRET_KEY`/llaves Wompi solo en variables de
  entorno, CORS restringido a los orígenes del frontend.
- SSRF/Webhook spoofing: verificación obligatoria de firma HMAC antes de procesar cualquier
  webhook de Wompi.
- Logging: nunca loggear contraseñas, tokens ni llaves privadas.

## Estructura de carpetas final

```
backend/app/
  core/           (reutilizado del template: security, config, db)
  models.py       (User del template + entidades nuevas de este plan)
  crud.py         (funciones CRUD por entidad)
  api/routes/
    login.py      (reutilizado - mock auth)
    payments.py   (nuevo - US1)
    webhooks.py   (nuevo - US1, sin auth, valida firma)
    plans.py      (nuevo - US2)
    history.py    (nuevo - US3)
    support.py    (nuevo - US4)
    faq.py        (nuevo - US4)
frontend/src/
  routes/
    login, dashboard (pago/recarga), plans, history, support
  components/     (shadcn/ui + componentes propios)
```
