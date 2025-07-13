 RESTRICCIONES TÉCNICAS CLAVE
# VFI Documentación

### Terminos

1. **VFI (Viasat File Interface)**: Proceso de software que se ejecuta en una computadora y que procesa horarios, efemérides y otra información para su transferencia entre el usuario remoto y los procesos de ViaSat.
2. **Remote User**: Un sistema informático que se comunica con el software ViaSat a través de la interfaz de usuario virtual (VFI). La ubicación física de la unidad de usuario (RU) es arbitraria. Deberá poder establecer comunicación con la VFI mediante FTP.
3. **Pass**: El tiempo que un satelite es visible y puede ser trackeado
4. **Task**: Coleccion de actividades asociada con una pasadada satelital.
5. **PreTest**: Tiempo asignado antes del Prepass para ejecutar pruebas automatizadas (BER) para validar que el equipo esté listo para el pase.
6. **PrePass**: El tiempo asignado para preposicionar el pedestal al inicio de la pista y configurar los instrumentos para el pase.
7. **InPassActivity**: Actividades realizadas durante el periodo de un pase. Un ejemplo es una prueba de BER de bucle largo.
8. **PostPass**: El tiempo asignado para colocar el pedestal de nuevo en su posición de reposo (zenith)
9. **Activity**: Actividad que puede ocurrir en un período de tiempo designado. Actualmente, aplica la configuración en un momento designado.

## Interfaz VFI

El método básico para transferir **schedules**, **ephemeris**, **resultados de pruebas** e informes de aprobación entre el **VFI** y el **Usuario Remoto** es mediante **transferencias de archivos**. 

### Procesamiento general de archivos remotos
Los **pasos generales del procesamiento** son los siguientes:
1. La **RU** crea un archivo remoto y lo transfiere al equipo **VFI**.
2. La **RU** crea un archivo remoto finalizado y lo transfiere al equipo **VFI**. Esto indica que el archivo remoto está completo y listo para procesarse.
3. **VFI** detecta un nuevo archivo remoto finalizado.
4. **VFI** elimina el archivo remoto finalizado.
5. **VFI** procesa el archivo remoto.
6. **VFI** crea un archivo de estado de importación.
7. **VFI** mueve el archivo remoto al directorio de archivo.
8. **VFI** crea el archivo de importación finalizada.

La **VFI** almacena los resultados del procesamiento del archivo en un archivo de estado de importación y crea un **archivo de importación finalizada** (``file.done``). El usuario remoto puede usar este archivo como indicación de que la VFI ha finalizado la importación del archivo remoto. El usuario remoto puede revisar los **resultados de la importación examinando el archivo de estado de importación**. El usuario remoto puede eliminar los archivos de estado de importación y los archivos de importación finalizada en cualquier momento. La siguiente figura muestra una transferencia típica.

![alt text](<TransferenciaTipicaVFI.png>)

### Tiempos y restricciones del procesamiento remoto de archivos
El proceso de detección de archivos sondea el directorio remoto cada segundo. No existen restricciones en cuanto a la cantidad ni al tipo de archivos (efemérides o programación) que se pueden enviar simultáneamente. El proceso de detección de archivos se realizará en orden alfanumérico, comenzando por el nombre completo del archivo, incluida la ruta. No se deben utilizar los nombres de archivo reservados "schedule.xml" ni "schedule.txt". Todos los archivos se procesarán de inmediato y solo estarán sujetos a los tiempos de procesamiento necesarios para leerlos y actualizar las distintas bases de datos del sistema. Las solicitudes cortas de programación y efemérides suelen procesarse en un plazo de 1 segundo tras la detección en el directorio remoto.

### Eliminación de archivos completados
La eliminación de un archivo completado una vez finalizado el procesamiento es responsabilidad del proceso que lo detecta.
* En el caso de transferencias de la ER a la VFI, la VFI eliminará los archivos completados durante el procesamiento.
* En el caso de transferencias de la VFI a la ER, es la ER la que eliminará el archivo completado. 
* Si el VFI detecta un archivo terminado con un nombre coincidente, el VFI eliminará el archivo terminado antes de crear el archivo a transferir.

### Directorios


```
/home/scc/
        │
        └── etc/
            ├── remote/
            │   ├── archive/ # Remote ephemeris and schedule files are archived
            │   ├── rciEphem.xxx
            │   ├── rciEphem.xxx.done
            │   ├── importEphem.xxx
            │   ├── importEphem.xxx.done
            │   ├── rciSched.xxx
            │   ├── rciSched.xxx.done
            │   ├── importSched.xxx.done
            │   └── importSched.xxx
            └── log/
                ├── tests/
                │    └── testResult.TASKID
                ├── reports/
                │    └── passReport.TASKID
                ├── testResult.TASKID.done
                └── passReport.TASKID.done

```

## Procesamiento de archivos de efemérides
El usuario remoto transferirá un archivo de efemérides remoto al directorio remoto ``/home/scc/etc/remote`` de VFI.
Una vez completada la transferencia, el usuario remoto transferirá un archivo ``.done`` al directorio remoto ``/home/scc/etc/remote``. Este archivo finalizado puede ser cualquier archivo, incluso uno vacío, y se utiliza para indicar a VFI que las efemérides remotas están completas y listas para su procesamiento.

VFI analizará todas las efemérides disponibles del archivo de efemérides remoto. Agregará cada elemento o vector de efemérides a la base de datos de efemérides. Cualquier error se registrará en el archivo de estado de importación de efemérides remotas.

Al finalizar la importación, los vectores antiguos se eliminarán automáticamente de la base de datos. El criterio para eliminar vectores antiguos es eliminar cualquier vector con una fecha anterior a la hora juliana de procesamiento del archivo, dejando al menos un vector en el archivo con la fecha más cercana a la hora juliana de procesamiento del archivo. Las efemérides con sellos de fecha posteriores a la hora juliana no afectan los procesos del archivo.

## Reestricciones de VFI

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
* El archivo original es archivado en ``/home/scc/etc/remote/archive`` y se conservan los últimos 1000 archivos

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