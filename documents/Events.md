# Eventos del Sistema

En la siguiente documentacion se describen los flujos de eventos del sistema:

## Evento 1: NEWTLE (desde tópico TLE)

Este no es un evento en si, pero puede comportarse como uno, es la llegada de un nuevo TLE por el tópico.

* Recibe el mensaje.
* Actualiza el TLE en su caché o base de datos interna.
* Genera nuevas actividades posibles.
* Asigna automáticamente actividades a antenas según:
    * Compatibilidad (frecuencia, órbita, tiempo).
    * Estado de servicio de la antena.
    * Prioridad y conflictos.
* Guarda el resultado como planificación nueva en la base de datos.
* Y publica un evento new_plann o directamente lo envía al Plan Sender.

## Evento 2: new_plann (desde tópico EVENTS)

Evento que acusa la llegada de nueva planificacion en estado new y sin asignar a ninguna antena.

 * Consulta en la base de datos las nuevas actividades asociadas.
 * Asigna automáticamente actividades a antenas según:
    * Compatibilidad (frecuencia, órbita, tiempo).
    * Estado de servicio de la antena.
    * Prioridad y conflictos.
 * Guarda el resultado como planificación nueva en la base de datos.
 * Y publica un evento new_plann o directamente lo envía al Plan Sender. 

## Evento 3: send_plann (desde tópico EVENTS)

Evento que establece el envio de planificacion a las antenas.

* Consultar la planificacion lista para ser enviada.
* Validar los datos.
* Armar los mensajes para ser enviado a las diferentes unidades.
* Revalidar superposición con otras actividades.
* Guardar el cambio del estado de la planificacion a `SENDED`.

Requiere lógica de comparación con el estado anterior

## Evento 4: change_plann (desde tópico EVENTS)

Significa que una planificación ya existente fue modificada manual o automáticamente.

* Revisar los cambios hechos.
* Ver si la asignación anterior sigue siendo válida.
* Reasignar si:
    * Cambió el satélite.
    * Cambió el horario.
    * Cambió el recurso (antena, frecuencia, etc).
* Revalidar superposición con otras actividades.
* Guardar y propagar la planificación corregida (puede ser parcial).

Requiere lógica de comparación con el estado anterior

## Evento 5: change_config (desde tópico EVENTS)

Puede ser cambio de:

* Estado de antena (de baja, fuera de servicio, cambio de banda/frecuencia).
* Capacidades (p.ej., ya no puede trackear satélites LEO).

Qué deberías hacer:

* Recalcular asignaciones futuras si afecta alguna actividad *nificada.
* Cancelar asignaciones que ya no son válidas.
* Redistribuir las actividades si hay otras antenas disponibles.
* Propagar los cambios.

Este evento puede disparar un replanificado parcial.

## Otros eventos

| Evento              | Acción esperada del Planificador              |
| ------------------- | --------------------------------------------- |
| `satellite_removed` | Quitar actividades planificadas del satélite. |
| `priority_update`   | Reordenar asignaciones según nuevo orden.     |
| `manual_override`   | No tocar planificación marcada como manual.   |
| `window_closed`     | Eliminar o cancelar planificación vencida.    |
| `antenna_reserve`   | Agregar o eliminar una reserva de antena.     |


