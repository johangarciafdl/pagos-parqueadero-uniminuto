# Feature Specification: Pagos electrónicos del parqueadero vía UWallet

**Feature Branch**: `001-mvp-pagos-parqueadero`

**Created**: 2026-09-15

**Status**: Draft

**Input**: Documento "Implementación de pagos electrónicos desde la plataforma UWallet para el
servicio de parqueadero de UNIMINUTO" + decisiones de arquitectura tomadas con el equipo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pagar el valor pendiente del día (Priority: P1)

Un usuario institucional entra desde UWallet (o el login mock durante desarrollo), ve el valor
pendiente de parqueadero según su vehículo/tarjeta, elige un método (tarjeta, Nequi, PSE,
transferencia) y confirma el pago. El sistema muestra el resultado (aprobado/pendiente/
rechazado) y genera un comprobante.

**Why this priority**: Es el flujo central del proyecto; sin esto no hay producto.

**Independent Test**: Con un usuario de prueba y un vehículo con valor pendiente, completar un
pago en modo sandbox de Wompi y verificar que el estado final coincide con el reportado por el
webhook, no con lo que devuelve el navegador.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con un vehículo registrado y valor pendiente > 0, **When**
   selecciona un método de pago y confirma, **Then** el sistema crea una transacción en estado
   `pendiente`, redirige/abre el checkout de Wompi, y al recibir el webhook actualiza el estado a
   `aprobado` o `rechazado`.
2. **Given** una transacción `aprobada`, **When** el usuario consulta su comprobante, **Then** ve
   concepto, valor, fecha, lugar y referencia única.
3. **Given** un webhook de Wompi con firma inválida, **When** llega al endpoint, **Then** el
   sistema lo rechaza (HTTP 400) y no modifica ningún estado de pago.

---

### User Story 2 - Comprar y gestionar un plan mensual (Priority: P2)

Un usuario consulta los planes mensuales disponibles (precio, tipo de vehículo, duración,
condiciones), compra uno con los mismos métodos electrónicos, y el sistema lo activa
automáticamente al confirmarse el pago. Puede consultar su plan vigente y renovarlo.

**Why this priority**: Segunda fuente de valor del documento original, pero depende del motor de
pagos de la Historia 1.

**Independent Test**: Comprar un plan en sandbox y verificar que `subscriptions` queda activo con
fecha de inicio/fin correctas solo tras la confirmación del webhook.

**Acceptance Scenarios**:

1. **Given** un plan disponible, **When** el usuario lo compra y el pago es aprobado, **Then** se
   crea una suscripción activa con `fecha_inicio = hoy` y `fecha_fin = hoy + duración`.
2. **Given** una suscripción próxima a vencer, **When** el usuario la renueva, **Then** la nueva
   vigencia se extiende desde la fecha de vencimiento anterior (no desde hoy), evitando perder
   días pagados.

---

### User Story 3 - Consultar historial y comprobantes (Priority: P3)

El usuario ve una bitácora de sus pagos/recargas anteriores con filtros por fecha, estado y tipo
de movimiento, y puede volver a consultar/descargar un comprobante.

**Why this priority**: Valor de transparencia y soporte, no bloquea el flujo de pago pero es
requisito explícito del documento.

**Independent Test**: Con datos de prueba de al menos 3 transacciones en distintos estados,
aplicar un filtro por rango de fechas y por estado y verificar que los resultados coinciden.

**Acceptance Scenarios**:

1. **Given** un usuario con transacciones previas, **When** filtra por estado `rechazado`,
   **Then** solo ve las transacciones rechazadas, ordenadas por fecha descendente.

---

### User Story 4 - FAQ y soporte (Priority: P4)

El usuario consulta preguntas frecuentes por categoría y, si no encuentra respuesta, radica una
solicitud que recibe un número de caso y puede seguir su estado.

**Why this priority**: Mejora de experiencia, no bloquea el core de pagos; es la última en
implementarse si el tiempo se agota.

**Independent Test**: Crear una solicitud de soporte y verificar que aparece con estado `abierta`
y un número de caso único.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado, **When** radica una solicitud de soporte, **Then** el sistema
   genera un número de caso único y el estado inicial es `abierta`.

---

### Edge Cases

- ¿Qué pasa si el usuario cierra el navegador después de pagar pero antes de que llegue el
  webhook? → El estado se resuelve igual cuando llegue el webhook; el historial refleja el estado
  real en cualquier momento posterior.
- ¿Qué pasa si llegan dos webhooks duplicados para la misma referencia? → El procesamiento debe
  ser idempotente (una referencia de transacción solo se procesa una vez).
- ¿Qué pasa si el usuario no tiene vehículo/tarjeta registrada? → Debe poder registrar uno antes
  de poder pagar; el sistema no asume datos por defecto.
- ¿Qué pasa si vence un plan mientras el usuario está usando el parqueadero? → El valor del día se
  cobra como pago normal (tarifa diaria) si no hay plan vigente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE identificar al usuario mediante una sesión institucional (mock JWT
  en desarrollo, reemplazable por el token real de UWallet sin cambiar lógica de negocio).
- **FR-002**: El sistema DEBE mostrar el valor pendiente de pago según el vehículo/tarjeta del
  usuario autenticado.
- **FR-003**: El sistema DEBE permitir pagar mediante tarjeta, Nequi, PSE o transferencia a través
  de Wompi.
- **FR-004**: El sistema DEBE registrar cada transacción con fecha, hora, lugar, método, valor,
  referencia y estado (`pendiente`, `aprobado`, `rechazado`, `cancelado`).
- **FR-005**: El sistema DEBE actualizar el estado final de una transacción únicamente a partir de
  un webhook de Wompi con firma verificada, nunca desde una llamada del cliente.
- **FR-006**: El sistema DEBE permitir listar, comprar y activar planes mensuales, con vigencia y
  renovación.
- **FR-007**: El sistema DEBE exponer un historial filtrable (fecha, estado, tipo) por usuario.
- **FR-008**: El sistema DEBE ofrecer FAQ por categoría y un formulario de soporte con número de
  caso y estado de seguimiento.
- **FR-009**: El sistema DEBE hashear contraseñas del login mock con bcrypt/argon2 y nunca
  almacenarlas ni loggearlas en texto plano.
- **FR-010**: El sistema DEBE generar tokens de acceso de corta duración y permitir su expiración/
  revocación.

### Key Entities

- **User**: usuario institucional (id, nombre, correo/documento, rol). Extiende el modelo `User`
  del template base.
- **Vehicle/Card**: vehículo o tarjeta asociada a un usuario (tipo: carro/moto, placa o número).
- **PaymentMethod / PaymentStatus** (catálogos): normalizan métodos (tarjeta, Nequi, PSE,
  transferencia) y estados (pendiente, aprobado, rechazado, cancelado).
- **Payment**: transacción de pago o recarga, referencia única, monto, método, estado, timestamps.
- **Plan**: plan mensual (precio, tipo de vehículo, duración, condiciones).
- **Subscription**: relación usuario–plan con fecha de inicio y fin.
- **ParkingLog**: bitácora de uso/pago, base del historial.
- **SupportTicket**: solicitud de soporte con número de caso y estado.
- **FAQ**: pregunta/respuesta categorizada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario puede completar un pago de principio a fin (ver valor → pagar → ver
  comprobante) en menos de 2 minutos en el flujo de sandbox.
- **SC-002**: El 100% de las actualizaciones de estado de pago provienen del webhook verificado,
  0% desde el cliente.
- **SC-003**: El historial refleja correctamente el 100% de las transacciones de prueba al
  aplicar filtros de fecha/estado.
- **SC-004**: Cero secretos (llaves Wompi, `SECRET_KEY`) presentes en el repositorio Git.

## Assumptions

- UWallet real es una caja negra sin API disponible; se simula con login propio diseñado para ser
  reemplazado luego por el SSO real.
- Las tarifas fijas diarias ($5.000 carro, $2.800 moto) y los planes se administran desde la base
  de datos, no hardcodeadas.
- El ambiente de pagos será el sandbox de Wompi durante el desarrollo; pasar a producción requiere
  solo cambiar llaves de entorno.
- El despliegue objetivo es una plataforma cloud gratuita (Render/Railway) con Postgres gestionado
  (Neon/Supabase), no infraestructura institucional de UNIMINUTO en esta fase.
