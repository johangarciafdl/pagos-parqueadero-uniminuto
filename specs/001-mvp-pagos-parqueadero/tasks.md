# Tasks: Pagos electrónicos del parqueadero vía UWallet

**Input**: `./spec.md`, `./plan.md` | **Plazo**: 7 días

## Cambio de arquitectura post-MVP: autenticación por ID + QR (reemplaza FR-001)

El login mock por correo institucional (Día 1-6) se reemplazó por una sesión sin
contraseña identificada por el ID/carné del estudiante, con un QR persistente
(token de alta entropía, no el ID en texto plano) para reingresar. Motivo: un
login por Microsoft/UWallet real requiere que un administrador de TI de la
universidad registre la aplicación en el tenant de Azure/Entra — algo fuera del
alcance de un estudiante — y el correo+contraseña propio no representa ninguna
identidad institucional real. El login por correo/contraseña se mantiene *solo*
para el administrador (`/staff`). Ver `backend/app/api/routes/kiosk.py` y
`frontend/src/routes/login.tsx`. Verificado end-to-end en producción real
(Render + Neon): registro → QR → reingreso por ID → reingreso por QR.

## Día 1 — Setup + Foundational

- [x] T001 Postgres real levantado (contenedor local); pendiente probar el `compose.yml`
      completo con Traefik (se validó backend+DB directo, más simple para desarrollo diario).
- [x] T002 `.env` local configurado y probado (no commiteado); `.env.example` con placeholders
      de Postgres, JWT y Wompi (sandbox) sí está en el repo.
- [x] T003 [P] Login del template verificado end-to-end con el superusuario semilla.
- [x] T004 `git init`, `.gitignore`, primer commit, repo remoto creado y sincronizado en
      https://github.com/johangarciafdl/pagos-parqueadero-uniminuto.
- [x] T005 Modelo `Item` reemplazado por el dominio completo del plan (incluye además
      `VehicleType`/`PaymentMethod`/`PaymentStatus` como catálogos en BD, más fieles al
      esquema original de 6 tablas que lo previsto). Migración inicial generada y aplicada
      contra Postgres real (no escrita a mano).
- [x] T006 Catálogos y tarifas ($5.000 carro, $2.800 moto) sembrados en `core/db.py`
      (idempotente), verificado vía API.

**Checkpoint**: ✅ proyecto corre local con la base de datos nueva migrada.

---

## Día 2 — User Story 1 (Pago/recarga) — backend

- [x] T007 [US1] `payments.py`: `POST /payments/` calcula el monto SIEMPRE en el servidor
      (catálogo/plan), nunca confía en un monto del cliente salvo en `RECHARGE`, y devuelve la
      firma de integridad de Wompi.
- [x] T008 [US1] `webhooks.py`: `POST /webhooks/wompi` público, valida firma HMAC, es
      idempotente ante reintentos, y crea `ParkingLog`.
- [x] T009 [US1] `GET /payments/{id}` y `GET /payments/pending`.
- [x] T010 [US1] Routers registrados en `api/main.py` (incluye también `vehicles.py`, necesario
      para poder probar pagos, que no estaba explícito en el plan original).

**Checkpoint**: ✅ verificado con curl contra Postgres real: firma inválida → 400; firma válida →
pago aprobado; reintento del mismo webhook → idempotente; vehículo pagado ya no aparece en
`/payments/pending`. Suite de tests del backend: 47 passed.

---

## Día 3 — User Story 1 — frontend

- [x] T011 [US1] Cliente OpenAPI regenerado (`npx openapi-ts`) contra el backend real; nombres
      de servicios/métodos verificados (`PaymentsService`, `VehiclesService`, etc.).
- [x] T012 [US1] Página "Pago/recarga" (`routes/_layout/index.tsx`): saludo, registrar
      vehículo, valor pendiente por vehículo, selector de método.
- [x] T013 [US1] `hooks/useWompiCheckout.ts`: abre el Widget Checkout de Wompi con la firma del
      backend; nunca confía en el resultado del widget, siempre refresca desde el backend.
- [ ] T014 [US1] Vista de comprobante detallada (por ahora el historial ya muestra
      referencia/estado; falta una vista dedicada de "comprobante" si se requiere para la
      sustentación).

**Checkpoint**: ✅ Verificado con Playwright (headless Chrome) contra el backend y Postgres
reales: login → dashboard carga sin errores de consola, todas las llamadas a la API devuelven
200, y el estado vacío ("Registra un vehículo...") se renderiza correctamente. Nota operativa
importante: `pytest`/`scripts/test.sh` borran todos los usuarios al terminar (fixture
`conftest.py`); **nunca correr la suite de tests apuntando al `DATABASE_URL` de desarrollo**,
usar una base de datos de pruebas separada o aceptar que hay que re-sembrar (`python -m
app.initial_data`) después.

---

## Día 4 — User Story 2 (Planes mensuales)

- [x] T015 [US2] `plans.py`: `GET /plans` público, `POST /plans` y `PATCH /plans/{id}`
      (solo superusuario, para administrar el catálogo desde ya).
- [x] T016 [US2] Activación/renovación automática de la suscripción integrada en
      `webhooks.py::_activate_or_renew_subscription` (renueva desde `end_date` anterior, no
      desde hoy, para no perder días pagados).
- [x] T017 [US2] `GET /plans/subscriptions/me` (plan vigente).
- [ ] T018 [US2] Frontend: página "Planes mensuales" (listado, detalle, compra, plan vigente).

**Checkpoint**: backend listo y con la lógica de renovación correcta; falta probar el flujo
completo con webhook simulado (igual que se hizo para US1) y el frontend.

---

## Día 5 — User Story 3 (Historial) + User Story 4 (FAQ/soporte)

- [x] T019 [US3] `history.py`: `GET /history` con filtros de fecha/estado, paginado; además
      `GET /history/log` (bitácora cruda de auditoría).
- [ ] T020 [US3] Frontend: página "Historial" con filtros y descarga/consulta de comprobante.
- [x] T021 [US4] `faq.py` (CRUD, solo superusuario para escribir) y `support.py` (ticket con
      `case_number` único vía `secrets.token_hex`, listar por usuario, cambiar estado).
- [ ] T022 [US4] Frontend: página "FAQ y soporte" con categorías y formulario.

**Checkpoint**: backend de los 4 módulos completo; falta el frontend completo (Días 3-5) y datos
semilla de ejemplo para planes/FAQ.

---

## Día 6 — Endurecimiento de seguridad (constitución, principio I)

- [x] T023 Auditoría de autenticación/autorización en todas las rutas: todo endpoint que
      expone datos de un usuario exige `CurrentUser` y filtra por `user_id`/`owner_id` (pagos,
      vehículos, historial, tickets); los únicos endpoints sin JWT son catálogos públicos
      (planes, FAQ, métodos de pago) y el webhook (protegido por firma HMAC, no por JWT).
      100% de las consultas van por SQLModel/SQLAlchemy parametrizado (cero SQL crudo).
- [x] T024 Confirmado con curl real: firma inválida → 400; mismo payload dos veces →
      `already_processed`, no reprocesa.
- [x] T025 CORS restringido a `settings.FRONTEND_HOST` (un solo origen, no wildcard). Rate
      limiting agregado en `/login/access-token` (solo cuenta fallos, 5/min por IP, verificado
      con curl: intento 6 → 429). Ningún log imprime contraseñas/tokens/llaves (revisado
      manualmente en `crud.py`, `security.py`, `wompi.py`).
- [x] T026 Auditoría de `.env`/`.gitignore`: `git log -p --all -- '*.env'` no muestra ningún
      secreto real, solo placeholders del `.env.example` commiteado.
- [ ] T027 Backup/restore rápido de Postgres documentado en `docs-development-reference.md`.

---

## Día 7 — Despliegue

- [x] T028 Postgres gestionado en **Neon**. Migraciones Alembic aplicadas y catálogos/tarifas/
      superusuario sembrados contra la base real (verificado consultando las tablas directamente).
- [x] T029 Backend + frontend desplegados en **Render** como un solo servicio Docker:
      https://parqueadero-uniminuto.onrender.com — variables de entorno puestas en el dashboard
      de Render (`DATABASE_URL`, credenciales del superusuario, llaves de Wompi), nunca en el repo.
      `render.yaml` versionado en la raíz del proyecto para reproducir la configuración.
- [x] T030 Llaves de Wompi **sandbox** reales (no placeholders) configuradas; URL de eventos del
      webhook registrada en el dashboard de Wompi apuntando a
      `https://parqueadero-uniminuto.onrender.com/api/v1/webhooks/wompi`.
- [x] T031 Prueba end-to-end en producción real: `/api/v1/utils/health-check/` → 200, frontend
      (`/`) → 200, `GET /vehicles/types` devuelve las tarifas reales desde Neon, login con el
      superusuario real devuelve un token válido. Planes/historial/soporte comparten el mismo
      backend ya verificado en local, pendiente solo un recorrido manual completo en el navegador
      contra la URL de producción.
- [ ] T032 Documentar en el README cómo correr el proyecto local (Docker Compose) y cómo se
      reemplazaría el mock de login por el SSO real de UWallet.

### Problemas reales encontrados y resueltos en el despliegue (útil para la sustentación)

1. **`backend/Dockerfile` dependía de archivos que no existen en este repo** (`package.json`/
   `bun.lock` y `uv.lock`/`pyproject.toml` en la raíz): venía del monorepo original de
   `fastapi/full-stack-fastapi-template`, que sí los tiene. Se reescribió la etapa de frontend
   para usar `node:22-slim` + `npm ci` sobre `frontend/` directamente, y se corrigieron las rutas
   de los bind mounts de `uv sync` a `backend/uv.lock`/`backend/pyproject.toml`.
2. **Render no vuelve a leer `render.yaml` en cada "Manual Deploy"**: los cambios a
   `dockerCommand` en el archivo no se aplicaban al servicio ya creado hasta corregirlo
   directamente vía la API de Render (`PATCH /v1/services/:id`). Para cambios de configuración
   (no solo código), hay que usar un "Blueprint Sync" explícito o la API, no basta con pushear.
3. **`dockerCommand` con `&&` no se interpretó como cadena de shell** en ningún formato probado
   (ni plano ni envuelto en `sh -c "..."`) — Render lo trataba como un único nombre de programa
   literal (`sh: 1: <comando completo>: not found`). Se resolvió moviendo la lógica a
   `backend/scripts/start.sh` (sin `&&` ni comillas anidadas) y usando `dockerCommand: bash
   scripts/start.sh`, una cadena de dos palabras sin ambigüedad posible de parseo.
4. **`fastapi run` no escuchaba en el puerto que Render asigna dinámicamente** (`$PORT`): se
   corrigió pasando `--host 0.0.0.0 --port "$PORT"` dentro de `start.sh`.
5. El MCP de Render (`mcp.render.com/mcp`) no es compatible con el flujo de autenticación de
   Claude Code ("Incompatible auth server: does not support dynamic client registration"); en su
   lugar se usó la API REST de Render directamente con una API key personal para diagnosticar y
   corregir el servicio sin depender de capturas de pantalla.

---

## Notas

- Si el tiempo se agota, el orden de recorte es: Día 5 (FAQ/soporte) > Día 4 (planes) — nunca
  recortar Día 6 (seguridad): un pago inseguro es peor que un módulo faltante.
- Cada día termina con un commit; no dejar cambios sin commitear de un día para otro.
