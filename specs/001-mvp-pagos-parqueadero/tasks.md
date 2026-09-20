# Tasks: Pagos electrónicos del parqueadero vía UWallet

**Input**: `./spec.md`, `./plan.md` | **Plazo**: 7 días

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

## Día 3 — User Story 1 — frontend (pendiente)

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

- [ ] T023 Revisar checklist OWASP (`OWASP/CheatSheetSeries`) contra cada endpoint nuevo:
      autenticación, control de acceso (un usuario no puede ver pagos/historial de otro),
      validación de entrada.
- [x] T024 Confirmado con curl real: firma inválida → 400; mismo payload dos veces →
      `already_processed`, no reprocesa.
- [ ] T025 Revisar CORS, rate limiting básico en login, y que ningún log imprima secretos.
- [x] T026 Auditoría de `.env`/`.gitignore`: `git log -p --all -- '*.env'` no muestra ningún
      secreto real, solo placeholders del `.env.example` commiteado.
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
