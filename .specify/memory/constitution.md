# UWallet Parqueadero UNIMINUTO Constitution

## Core Principles

### I. Seguridad primero (NON-NEGOTIABLE)
Toda decisión de diseño se evalúa primero contra el checklist de OWASP/CheatSheetSeries.
JWT de corta duración (access token ≤ 30 min) + refresh token con rotación; contraseñas con
bcrypt/argon2, nunca en texto plano ni loggeadas. El backend nunca confía en el estado de un
pago reportado por el navegador: el estado final de una transacción solo se actualiza mediante
el webhook de Wompi, verificado con su firma HMAC. Ningún secreto (llaves de Wompi,
`SECRET_KEY` de JWT, credenciales de base de datos) se commitea al repositorio; viven solo en
variables de entorno / `.env` (excluido por `.gitignore`). Toda entrada de usuario se valida con
Pydantic/SQLModel; el ORM parametriza todas las consultas (cero SQL crudo concatenado).

### II. Autenticación desacoplada del proveedor
El login institucional se implementa primero como un mock propio (usuarios de prueba + JWT),
pero detrás de una interfaz de "proveedor de identidad" (`AuthProvider`) que abstrae cómo se
obtiene la identidad del usuario. Migrar del mock al SSO real de UWallet debe requerir solo
implementar un nuevo adaptador, sin tocar la lógica de negocio de pagos, planes o historial.

### III. Base de datos evolutiva y versionada
Se parte de las 6 tablas del sistema físico actual (`types`, `status`, `methods`, `users`, `cards`,
`payments`) y se extienden con `sessions`, `vehicles`, `plans`, `subscriptions`, `logs` y
`support_tickets`. Todo cambio de esquema pasa por una migración versionada (Alembic); nunca
se edita el esquema directamente en la base de datos de un ambiente compartido.

### IV. Trazabilidad total
Cada pago, recarga, cambio de estado de transacción y activación de plan queda registrado como
un log inmutable (fecha, hora, usuario, monto, método, estado, referencia). El módulo de
historial es una vista de solo lectura sobre esos logs, nunca la fuente de verdad editable.

### V. Simplicidad y velocidad de entrega (YAGNI)
El proyecto se entrega en una semana. Se reutiliza `fastapi/full-stack-fastapi-template` como
base de backend (FastAPI + SQLModel + PostgreSQL + Alembic + JWT + Docker Compose + pytest) y
`shadcn/ui` + Tailwind + React/Vite para el frontend, en vez de reconstruir infraestructura ya
resuelta y probada por la comunidad. No se agregan módulos, microservicios ni abstracciones que
no estén en el alcance de los 4 módulos definidos (pago/recarga, planes mensuales, historial,
FAQ/soporte).

## Requisitos técnicos y de seguridad

- Backend: Python 3.11+, FastAPI, SQLModel/SQLAlchemy, PostgreSQL, Alembic.
- Frontend: React + Vite + TypeScript, shadcn/ui, Tailwind CSS.
- Pagos: integración directa con la API REST de Wompi vía `httpx` (sandbox → producción); sin
  SDKs de terceros sin verificar (no existe uno confiable con buen respaldo de comunidad).
- Referencia de seguridad obligatoria: OWASP/CheatSheetSeries (inyección, auth, sesiones, JWT).
- Despliegue: Docker Compose local; nube gratuita (Render/Railway) + Postgres gestionado
  (Neon/Supabase) para el ambiente accesible por URL.
- Control de versiones: Git + GitHub, commits pequeños y descriptivos, `.env` nunca versionado.

## Flujo de trabajo

Desarrollo guiado por especificación (spec-kit): cada módulo pasa por spec → plan → tasks antes
de implementarse, para mantener trazabilidad entre lo pedido en el documento del proyecto y lo
construido. Dado el plazo de una semana, el ciclo se aplica una vez a nivel de MVP completo
(no por módulo) para no perder velocidad, y se reabre solo si aparece un cambio de alcance.

## Governance

Esta constitución prevalece sobre preferencias de estilo individuales. Cualquier excepción
(por ejemplo, aplazar un control de seguridad por falta de tiempo) debe quedar documentada
explícitamente en `tasks.md` como deuda técnica con su riesgo, no omitirse en silencio.

**Version**: 1.0.0 | **Ratified**: 2026-09-15 | **Last Amended**: 2026-09-15
