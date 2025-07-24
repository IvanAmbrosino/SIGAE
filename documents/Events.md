# Eventos del Sistema

En la siguiente documentacion se describen los flujos de eventos del sistema:

## TOPICO TLE

### Evento 1: NEWTLE (desde tópico TLE)

**Modulos destino**: ``AntennaAdapter``, ``PlannerModule``

Este no es un evento en si, pero puede comportarse como uno, es la llegada de un nuevo TLE por el tópico.

* Recibe el mensaje.
* Actualiza el TLE en su caché o base de datos interna.
* Genera nuevas actividades posibles.
* Asigna automáticamente actividades a antenas según:
    * Compatibilidad (frecuencia, órbita, tiempo).
    * Estado de servicio de la antena.
    * Prioridad y conflictos.
* Guarda el resultado como planificación nueva en la base de datos.
* Y publica un evento ``SENDPLANN`` o directamente lo envía al Plan Sender.

**Formato del Mensaje**
```json
    {
    "namespace": "com.example.tle",
    "type": "record",
    "name": "TLEData",
    "fields": [
        { "name": "message_type", "type": "string" },
        { "name": "norad_id", "type": "string" },
        { "name": "satellite_name", "type": "string" },
        { "name": "line1", "type": "string" },
        { "name": "line2", "type": "string" },
        { "name": "timestamp", "type": "string" }
    ]
    }
```

## TOPICO PLANN

### Evento 3: PLANN (desde tópico PLANN)

Este no es un evento en si, pero puede comportarse como uno, es la llegada de una nueva planificacion por el tópico PLANN.

* Recibe el mensaje.
* Valida que el mensaje esta destinado a la Unidad.
* Valida que los datos que vienen en el mensaje sean correctos y completos.
* Genera el archivo con la planificacion para ser enviado a las antenas
* Guarda el resultado como planificación en cache del modulo.
* En caso de que este habilitado, envia un mensaje ``ACK`` para la planificacion correspondiente.

**Formato del Mensaje PLANN**
```json
{
"type": "record",
"name": "FullPlanMessage",
"namespace": "com.tuempresa.planificacion",
"doc": "Mensaje completo de planificación de una antena",
"fields": [
    { "name": "message_type","type": "string" },
    { "name": "antenna_id", "type": "string" },
    { "name": "timestamp", "type": "string" },
    { "name": "source", "type": "string" },
    {
    "name": "plan",
    "type": {
        "type": "array",
        "items": {
        "name": "PasePlanificado",
        "type": "record",
        "fields": [
            { "name": "task_id", "type": "string" },
            { "name": "action", "type": "string" },
            { "name": "antenna_id", "type": "string" },
            { "name": "satellite", "type": "string" },
            { "name": "norad_id", "type": "string" },
            { "name": "config_id", "type": "int" },
            { "name": "start", "type": "string" },
            { "name": "end", "type": "string" },
            { "name": "prepass_seconds", "type": "int", "default": 120 },
            { "name": "postpass_seconds", "type": "int", "default": 60 }
        ]
        }
    }
    }
]
}
```

**Formato del Mensaje PLANNTLE**
```json
{
    "type": "record",
    "name": "FullPlanMessage",
    "namespace": "com.tuempresa.planificacion",
    "doc": "Mensaje completo de planificación de una antena",
    "fields": [
        { "name": "message_type","type": "string" },
        { "name": "antenna_id", "type": "string" },
        { "name": "timestamp", "type": "string" },
        { "name": "source", "type": "string" },
        {
        "name": "plan",
        "type": {
            "type": "array",
            "items": {
            "name": "PasePlanificado",
            "type": "record",
            "fields": [
                { "name": "task_id", "type": "string" },
                { "name": "action", "type": "string" },
                { "name": "antenna_id", "type": ["null", "string"], "default": null },
                { "name": "satellite", "type": ["null", "string"], "default": null },
                { "name": "norad_id", "type": ["null", "string"], "default": null },
                { "name": "config_id", "type": ["null", "int"], "default": null },
                { "name": "start", "type": ["null", "string"], "default": null },
                { "name": "end", "type": ["null", "string"], "default": null },
                { "name": "prepass_seconds", "type": ["null", "int"], "default": null },
                { "name": "postpass_seconds", "type": ["null", "int"], "default": null }
                    ]
                }
            }
        },
        {
        "name": "tles",
        "type": {
            "type": "array",
            "items": {
            "name": "TleData",
            "type": "record",
            "fields": [
                    { "name": "norad_id", "type": "string" },
                    { "name": "satellite_name", "type": "string" },
                    { "name": "line1", "type": "string" },
                    { "name": "line2", "type": "string" },
                    { "name": "timestamp", "type": "string" }
                    ]
                }
            },
            "default": []
        }
    ]
}
```

## TOPICO ACK

### Evento 4: ACK (desde topico ACK)

Este no es un evento en si, pero puede comportarse como uno, es la llegada de una respuesta al mensaje enviado con la planificacion, indicando que se cargó correctamente en la antena.

* Recibe el mensaje
* Valida su formato y contenido
* Por cada uno de los ACK:
    * Recorre la lista de enviados y verifica que esten en el mensaje ACK
    * Si hay alguno que no está, envia un mensaje de error, indicando que hay una pasada que no pudo cargarse en la antena.
    * Manejar la logica de reenvio
    * Elimina de la lista los mensajes que fueron cargados correctamente.

**Formato del Mensaje ACK**
```json
{
  "type": "record",
  "name": "ACK_Message",
  "namespace": "sigae.planificacion",
  "doc": "Mensaje de respuesta a la llegada de una planificacion",
  "fields": [
    { "name": "message_type", "type": "string" },
    { "name": "norad_id", "type": "string" },
    { "name": "satellite_name", "type": "string" },
    { "name": "task_id", "type": "string" },
    { "name": "antenna_id", "type": "string" },
    { "name": "timestamp", "type": "string" }
  ]
}
```

## TOPICO EVENTS

Topico donde se realizan el envio de todos los eventos del sistema

**Formato del Mensaje EVENTS**
```json
{
  "type": "record",
  "name": "EVENT_Message",
  "namespace": "sigae.planificacion",
  "doc": "Mensaje de Evento",
  "fields": [
    { "name": "event_type", "type": "string" },
    { "name": "timestamp", "type": "string" }
  ]
}
```

### Evento 2: NEWPLANN (desde tópico EVENTS)

Evento que acusa la llegada de nueva planificacion en estado new y sin asignar a ninguna antena.

**Modulos destino**: ``PlannerModule``

 * Consulta en la base de datos las nuevas actividades asociadas.
 * Asigna automáticamente actividades a antenas según:
    * Compatibilidad (frecuencia, órbita, tiempo).
    * Estado de servicio de la antena.
    * Prioridad y conflictos.
 * Guarda el resultado como planificación nueva en la base de datos.
 * Y publica un evento `SENDPLANN` o directamente lo envía al Plan Sender. 

## Evento 3: SENDPLANN (desde tópico EVENTS)

Evento que establece el envio de planificacion a las antenas.

**Modulos destino**: ``SenderModule``

* Consultar la planificacion lista para ser enviada.
* Armar los mensajes para ser enviado a las diferentes unidades.
Se arma un mensaje por cada unidad, con todas las operaciones. Para este caso hay 3 caminos:
    * **ADD**: Se agregan actividades a la antena
    * **UPDATE**: Se modifican las actividades de una antena (ej. recorte de pasada)
        * Se elimina la actividad en cuestion y luego se agrega la misma con los horarios corridos
    * **DELETE**: Se elimina la actividad
* Validar los datos a ser enviados.
* Revalidar superposición con otras actividades.
* Guardar el cambio del estado de la planificacion a `SENDED`.

Requiere lógica de comparación con el estado anterior

## Evento 4: CHANGEPLANN (desde tópico EVENTS)

**Modulos destino**: ``SenderModule``, ``PlannerModule``

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

## Evento 5: CHANGECONFIG (desde tópico EVENTS)

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


