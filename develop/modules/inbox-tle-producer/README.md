# Inbox TLE Publisher

Servicio que mira la llegada de archivos `.TLE` en un directorio configurado, verifica el contenido del TLE y lo envia por Kafka. 

Se hace con el objetivo de poder editar, subir un nuevo TLE de forma facil y rapida desde una interfaz comun. En este caso el servicio queda esperando la llegada de un archivo `.tle` en un directorio especificado. La carga se hace de forma directa, no valida que el TLE sea el ultimo o mayor que el anterior, en caso de que haya un error y que la antena no lo acepte, el encargado de notificar es el modulo **Viasat-TLE-Sender**

## Configuracion

```json
{
    "kafka_config":{
        "bootstrap_servers": "localhost:19092,localhost:29092,localhost:39092",
        "schema_registry_url": "http://localhost:8081",
        "schema_file": "tle_schema.json",
        "group_id": "tle-publisher-group",
        "client_id": "inbox-tle-publisher",
        "auto_offset_reset": "latest",
        "num_partitions": 3,
        "replication_factor": 3,
        "enable_idempotence": true,
        "acks": "all",
        "retries": 5,
        "max_in_flight_requests_per_connection": 5,
        "auto_create_topics": true
        },
    "sftp_server":{
        "host":"10.x.x.x",
        "user":"soporte",
        "port": 22,
        "password":"/src/secrets/srv_passwd",
        "directory":"/home/soporte/inbox-tle-test",
        "file_suffix":".TLE",
        "file_prefix": "",
        "time_out": 30
    },
    "sleep_time": 10,
    "logs": {
        "folder":"logs",
        "filename": "inbox_tle_publisher.log",
        "rotation": 5,
        "size": 5000000,
        "debug_mode": false
    },
    "mail":{
        "notifications": false,
        "mailserver": "200.16.81.74",
        "from":"email-agent@conae.gov.ar",
        "to":["cgss.systemsupport@conae.gov.ar"],
        "attachments": ""
    }
}
```

### Envio de mensajes

**Consideraciones**

* Utiliza Schema Registry, por lo que si se encuentra desactualado, este lanzará un error
* El servicio no crea nuevos topicos, primero valida que existe y lo envia. 
* Se reemplazan los espacios en blanco con `_`

Los datos que se intercambian son en formato json y estan de la siguiente forma:
```json
{
    "satelite_name": "SAOCOM-1A",
    "line1": "1 43641U 18076A   25126.45039375 +.00000000 +00000+0 +14262-4 6 22755",
    "line2": "2 43641  97.8901 314.0336 0001478  90.5852 258.3502 14.82148398355841",
    "timestamp": 1746533972
}
```