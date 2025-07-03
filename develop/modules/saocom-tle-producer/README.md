# Saocom TLE Publisher

Servicio que se encarga de obtener los nuevos TLE Nominal y PPM desde el SFTP del MOC de Saocom.
1. Obtiene los ultimos tle
2. Comprueba su contenido
3. Compara con el ultimo cargado
4. Envia a kafka para cargarse en las antenas.

## Configuracion

**Consideraciones**
- **type**: Es el tipo de tle, en este caso maneja el Nominal y PPM (Pueden separarse como servicios independientes)
- **satellite_altername**: En el caso que se necesite una traduccion de nombre, se especifica en este atributo.
- **topic**: Es el topic que se hara uso para el envio de mensajes, en caso de no especificarse, se usa el NoradID


```json
{
    "kafka_config":{
        "bootstrap_servers": "server1:9092,server2:9092,server3:9092",
        "schema_registry_url": "http://localhost:8081",
        "schema_file": "tle_schema.json",
        "group_id": "tle-publisher-group",
        "client_id": "saocom-tle-publisher",
        "auto_offset_reset": "latest",
        "topic": "43641",
        "num_partitions": 3,
        "replication_factor": 3,
        "enable_idempotence": true,
        "acks": "all",
        "retries": 5,
        "max_in_flight_requests_per_connection": 5
        },
    "sftp_moc_server":{
        "host":"200.16.81.149",
        "user":"cgss",
        "port": 22,
        "password":"/app/password/moc_passwd",
        "time_out": 30
    },
    "satellite_config":{
        "type":["PPMTLE","TLE"],
        "prefix": "S1",
        "satellite_id": "43641",
        "satellite_name": "SAOCOM-1A",
        "satellite_altername": "",
        "satellite": "A"
    },
    "sleep_time":900,
    "logs": {
        "folder":"logs",
        "filename": "tle_publisher.log",
        "rotation": 5,
        "size": 5000000,
        "debug_mode": true
    },
    "mail":{
        "notifications": true,
        "mailserver": "200.16.81.74",
        "from":"email-agent@conae.gov.ar",
        "to":["cgss.systemsupport@conae.gov.ar"],
        "attachments": ""
    }
}
```

### Envio de mensajes

El servicio crea un topico por cada satelite, manejando el TLE Nominal y PPM en el mismo canal de comunicacion. El Topico es el NoradID del satélite.

Los datos que se intercambian son en formato json y estan de la siguiente forma:
```json
{
    "satellite_name": "SAOCOM-1A",
    "line1": "1 43641U 18076A   25126.45039375 +.00000000 +00000+0 +14262-4 6 22755",
    "line2": "2 43641  97.8901 314.0336 0001478  90.5852 258.3502 14.82148398355841",
    "timestamp": 1746533972
}
```