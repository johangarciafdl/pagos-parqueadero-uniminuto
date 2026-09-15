# Tasks: Pagos electrónicos del parqueadero vía UWallet

**Input**: `./spec.md`, `./plan.md` | **Plazo**: 7 días

## Día 1 — Setup + Foundational

- [ ] T001 Levantar `compose.yml` local (Postgres + backend + frontend) y confirmar
      `docker compose up -d` funciona.
- [ ] T002 Configurar `.env` a partir de `.env.example`: `SECRET_KEY`, credenciales Postgres,
      `WOMPI_PUBLIC_KEY`/`WOMPI_PRIVATE_KEY`/`WOMPI_EVENTS_SECRET` (sandbox), `BACKEND_CORS_ORIGINS`.
- [ ] T003 [P] Confirmar que el login/registro de ejemplo del template funciona end-to-end
      (usuario semilla del template) antes de tocar nada.
- [ ] T004 `git init`, `.gitignore` (incluye `.env`, `node_modules/`, `__pycache__/`,
      `.venv/`), primer commit "chore: bootstrap desde full-stack-fastapi-template + spec-kit".
- [ ] T005 Reemplazar el modelo `Item` de `backend/app/models.py` por las entidades nuevas del
      `plan.md` (Vehicle, PaymentMethodCatalog, PaymentStatusCatalog, Payment, Plan,
      Subscription, ParkingLog, SupportTicket, FAQ) + generar migración Alembic.
- [ ] T006 Sembrar catálogos (`PaymentMethodCatalog`, `PaymentStatusCatalog`) y tarifas base
      ($5.000 carro, $2.800 moto) en `backend/app/initial_data.py`.

**Checkpoint**: proyecto corre local con la base de datos nueva migrada.

---

## Día 2 — User Story 1 (Pago/recarga) — backend

- [ ] T007 [US1] `backend/app/api/routes/payments.py`: endpoint `POST /payments/` que crea
      `Payment(status=pending)` y calcula la firma de integridad de Wompi.
- [ ] T008 [US1] `backend/app/api/routes/webhooks.py`: `POST /webhooks/wompi` público, valida
      firma HMAC con `WOMPI_EVENTS_SECRET`, actualiza `Payment.status` de forma idempotente
      (chequear `wompi_reference` ya procesada) y crea `ParkingLog`.
- [ ] T009 [US1] `GET /payments/{id}` y `GET /payments/pending` (valor pendiente del usuario
      autenticado, según su vehículo).
- [ ] T010 [US1] Registrar routers nuevos en `backend/app/api/main.py`.

**Checkpoint**: se puede crear un pago y simular un webhook con `curl`/Postman y ver el estado
actualizarse en la base de datos.

---

## Día 3 — User Story 1 — frontend

- [ ] T011 [US1] Regenerar cliente OpenAPI (`frontend/openapi-ts.config.ts` + script del
      template) para tener tipos de los endpoints nuevos.
- [ ] T012 [US1] Página "Pago/recarga" (dashboard principal): muestra usuario, vehículo, valor
      pendiente, selector de método, resumen antes de pagar.
- [ ] T013 [US1] Integración con el Widget/Checkout de Wompi usando la firma que entrega el
      backend.
- [ ] T014 [US1] Vista de resultado (aprobado/pendiente/rechazado) + comprobante con referencia.

**Checkpoint**: flujo de pago completo en sandbox, de principio a fin, en el navegador.

---

## Día 4 — User Story 2 (Planes mensuales)

- [ ] T015 [US2] `backend/app/api/routes/plans.py`: `GET /plans`, `POST /plans/{id}/subscribe`
      (crea `Subscription` inactiva hasta confirmar pago, reutiliza el mismo flujo de Payment).
- [ ] T016 [US2] Activación automática de la suscripción al recibir el webhook aprobado
      (extender `webhooks.py`).
- [ ] T017 [US2] `GET /subscriptions/me` (plan vigente) + lógica de renovación (extiende desde
      `end_date` anterior, no desde hoy).
- [ ] T018 [US2] Frontend: página "Planes mensuales" (listado, detalle, compra, plan vigente).

**Checkpoint**: comprar un plan activa una suscripción real tras el webhook.

---

## Día 5 — User Story 3 (Historial) + User Story 4 (FAQ/soporte)

- [ ] T019 [US3] `backend/app/api/routes/history.py`: `GET /history` con filtros de fecha,
      estado y tipo, paginado.
- [ ] T020 [US3] Frontend: página "Historial" con filtros y descarga/consulta de comprobante.
- [ ] T021 [US4] `backend/app/api/routes/faq.py` (CRUD simple) y `support.py` (crear ticket con
      `case_number` único, listar por usuario, cambiar estado).
- [ ] T022 [US4] Frontend: página "FAQ y soporte" con categorías y formulario.

**Checkpoint**: los 4 módulos del documento original están navegables end-to-end.

---

## Día 6 — Endurecimiento de seguridad (constitución, principio I)

- [ ] T023 Revisar checklist OWASP (`OWASP/CheatSheetSeries`) contra cada endpoint nuevo:
      autenticación, control de acceso (un usuario no puede ver pagos/historial de otro),
      validación de entrada.
- [ ] T024 Confirmar que `webhooks.py` rechaza firmas inválidas y es idempotente (test manual con
      el mismo payload dos veces).
- [ ] T025 Revisar CORS, rate limiting básico en login, y que ningún log imprima secretos.
- [ ] T026 Auditoría de `.env`/`.gitignore`: confirmar que nunca se commiteó un secreto
      (`git log -p -- .env` debe estar vacío).
- [ ] T027 Backup/restore rápido de Postgres documentado en `docs-development-reference.md`.

---

## Día 7 — Despliegue

- [ ] T028 Provisionar Postgres gestionado (Neon/Supabase) y correr migraciones Alembic contra
      esa base.
- [ ] T029 Desplegar backend + frontend en Render/Railway, variables de entorno vía el panel del
      proveedor (nunca en el repo).
- [ ] T030 Cambiar llaves de Wompi de sandbox a las reales solo si ya se validó el flujo completo
      en sandbox desplegado.
- [ ] T031 Prueba end-to-end en el ambiente desplegado: pago, plan, historial, soporte.
- [ ] T032 Documentar en el README cómo correr el proyecto local (Docker Compose) y cómo se
      reemplazaría el mock de login por el SSO real de UWallet.

---

## Notas

- Si el tiempo se agota, el orden de recorte es: Día 5 (FAQ/soporte) > Día 4 (planes) — nunca
  recortar Día 6 (seguridad): un pago inseguro es peor que un módulo faltante.
- Cada día termina con un commit; no dejar cambios sin commitear de un día para otro.
