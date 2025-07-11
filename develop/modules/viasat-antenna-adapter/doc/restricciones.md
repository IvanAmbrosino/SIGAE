 RESTRICCIONES TÉCNICAS CLAVE
# Reestricciones de VFI

### 1. El TaskID debe ser único

* No puede haber dos tareas con el mismo TaskID en el sistema VFI.
* Si intentás enviar una tarea con ADD y ese TaskID ya está presente, será rechazada.
* El intento de CANCEL con un TaskID inexistente también es error.

> TaskID basado en: SATNAME_ANT_ID_YYYY_DDD_HHMMSS para que sea único por pase

### 2. El archivo debe ser enviado antes del inicio del pase

* El VFI no aceptará tareas si la hora de inicio ya pasó.
* Si llega después del inicio,:
    * El sistema eliminará cualquier actividad de pretest.
    * Insertará prepass por defecto si hay tiempo.
    * Si no hay tiempo, el pase será eliminado automáticamente

> Enviar el archivo XML con al menos unos minutos de anticipación, idealmente 5-10 min.

### 3. Conflictos de recursos

* El VFI verifica que:
    * Haya efemérides válidas para el satélite.
    * El pase esté por encima del horizonte.
    * No haya conflictos con recursos ya asignados.
* Si hay conflicto, el pase será rechazado o desplazado y se notificará en el archivo `importSched.xxx`

### 4. Ubicación y formato del archivo

* Archivo XML: ``/home/scc/etc/remote/rciSched.xxx``
* Archivo ``.done`` vacío: ``/home/scc/etc/remote/rciSched.xxx.done``
* El nombre xxx debe:
    * Tener hasta 36 caracteres.
    * Incluir solo letras, números, ``_`` y ``.``.
    * No puede incluir caracteres especiales ni las palabras ``done``, ``inprocess``

### 5. Formato de tiempo

* Debe seguir el formato: ``YYYY DDD HH:MM:SS`` (por ejemplo: ``2025 193 15:30:00``)
* Aplica a todos los campos de tiempo: ``StartTime``, ``EndTime``, etc.

### 6. Prepass obligatorio

* Todos los pases deben incluir un bloque ``<PrePass>``:
    * Si no se especifica, el VFI lo calcula automáticamente.
    * Dura típicamente:
        * 2 minutos para pedestales **El/Az/Train**
        * 1 minuto para pedestales **X/Y**
* El ``<PreTest>`` es opcional y debe ocurrir antes del prepass

### 7. Procesamiento

* El VFI procesa los archivos en cuanto detecta el ``.done``, en orden **alfabético**.
* Se genera un archivo ``importSched.xxx`` que reporta errores o estado del proceso.
* El archivo original es archivado en ``$RCIDIR/archive`` y se conservan los últimos 1000 archivos

### 8. Purge borra todo

* Si mandás una tarea con ``<Action>PURGE</Action>``, borra todos los pases programados, incluso los manuales

## Buenas Practicas

| Requisito             | Recomendación práctica                                 |
| --------------------- | ------------------------------------------------------ |
| Unicidad del `TaskID` | Usar hash, timestamp o patrón satélite+hora            |
| Validación previa     | Simular/validar conflictos localmente antes de enviar  |
| Envío anticipado      | Mandar con suficiente margen antes de la hora del pase |
| Log de resultados     | Revisar `importSched.xxx` tras cada envío              |
| Archivos válidos      | No usar nombres reservados (`schedule.xml`, etc.)      |
| Empaquetado seguro    | Usar `rsync` o `scp` seguido del `.done`               |

## Validaciones

| Validación                               | ¿Cómo hacerlo?                                                                |
| ---------------------------------------- | ----------------------------------------------------------------------------- |
| Que el `TaskID` sea único                | Comparar contra tareas ya enviadas (guardadas localmente o en la BD).         |
| Que el pase aún no haya comenzado        | `start_time > now + margen`                                                   |
| Que el tiempo esté en formato `YYYY DDD` | Usar `strftime("%Y %j %H:%M:%S")`                                             |
| Que el satélite tenga TLE actualizado    | Verificar en tu cache o repositorio de TLE                                    |
| Que la elevación máxima sea > 0°         | Calcular el pase con TLE y posición de la antena                              |
| Que no haya conflicto de recursos        | Consultar tu planificación local / simulador de antena                        |
| Que la antena esté disponible            | Validar que no esté en mantenimiento, reserva o fuera de servicio             |
| Que el XML esté bien formado             | Usar validación contra el esquema `schedule.xsd` (opcional pero útil)         |
| Que el nombre del archivo sea válido     | Validar con regex: `^[a-zA-Z0-9_.]{1,36}$` y no incluya `.done` ni especiales |


## Estructura

```
src/
├── domain/
│   ├── entities/
│   │   └── planificacion.py          # Clases Planificacion, Pase, Reserva, Antena, etc.
│   ├── services/
│   │   └── validador_planificacion.py  # Lógica de validación (tiempo, visibilidad, conflictos)
│   └── exceptions.py
│
├── application/
│   ├── use_cases/
│   │   └── generar_planificacion_vfi.py  # Orquesta validación + generación XML
│   └── ports/
│       ├── xml_writer_port.py          # Interfaz para escribir archivo
│       └── tle_repository_port.py      # Interfaz para acceder a TLE
│
├── infrastructure/
│   ├── xml/
│   │   └── xml_writer_vfi.py         # Implementa xml_writer_port usando lxml
│   ├── tle/
│   │   └── tle_repository.py         # Accede a DB, cache o archivos TLE
│   └── fs/
│       └── file_sender.py            # Enviar a path VFI y crear .done
│
└── interface/
    ├── cli/
    │   └── generar_xml.py            # CLI que invoca el caso de uso
    └── kafka/
        └── event_consumer.py         # Invoca caso de uso ante evento
```