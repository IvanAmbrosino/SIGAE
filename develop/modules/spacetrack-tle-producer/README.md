# SpaceTrack TLE Publisher

Servicio que se encarga de obtener los nuevos TLE desde la API de SpaceTrack.
1. Obtiene los ultimos tle
2. Comprueba su contenido
3. Compara con el ultimo cargado
4. Envia a kafka para cargarse en las antenas.

### Consultas a Space-Track

Para hacer las consultas de **Space-Track** se deben tener los siguientes requerimientos:
* Los TLE se pueden descargar cada 1 hora. Se debe elegir al azar un minuto para esta consulta que no esté en el parte superior o inferior de la hora.
* Para hacer una sola consulta de un conjunto TLE y que obtenga ciertos campos que se necesitan, se pueden concatenar con "," en la consulta y agregarle ```/predicates/```:
    * Ejemplo: ```https://www.space-track.org/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/25544,36411,26871,27422/predicates/FILE,EPOCH,TLE_LINE1,TLE_LINE2/format/html```
        <pre>
        FILE	EPOCH				TLE_LINE1        TLE_LINE2
        1339414	2012-08-23 14:41:35	1 25544U 98067A 12236.61221542 .00014781 00000-0 26483-3 0  1660	2 25544 051.6476 145.7539 0014860 352.2902 087.3290 15.50074566788503
        1339388	2012-08-23 13:09:41	1 36411U 10008A 12236.54839284 .00000068 00000-0 00000+0 0  1996	2 36411 000.4393 261.8677 0004087 269.6508 223.6226 01.00284253 9094
        1339308	2012-08-23 09:04:34	1 26871U 01031A 12236.37818175 -.00000300 00000-0 10000-3 0 7001	2 26871 002.4043 072.3013 0002099 076.5029 259.0419 01.00285194 40660
        1339234	2012-08-23 05:26:49	1 27422U 02021B 12236.22696129 .00000039 00000-0 32070-4 0  9902	2 27422 098.3978 295.8841 0013298 043.4759 316.7468 14.28769327535462
        </pre>
* Formato de la URL para la consulta debe ser: ```https://www.space-track.org/basicspacedata/query/class/boxscore/```
    * Base: URL: https://www.space-track.org/
    * Controlador de solicitudes: ```basicspacedata/```
    * Acción de solicitud: ```querry/```
    * Pares de valores de predicado: ```class/nameclass/``` 
        * Nombre de la clase: ```tle_latest```
        * ```ORDINAL/1``` Cuanto menor sea el ORDINAL, más reciente se agregó el ELSET. Por ejemplo, añadiendo /ORDINAL/1/ a la URL mostrará solo el ELSET más reciente de cada objeto.
        * ```NORAD_CAT_ID/ID,ID,ID/```
    * Space-Track recomienda limitar las consultas de la API en ```OBJECT_NUMBER / NORAD_CAT_ID``` Y un *rango de época* como ```>now-30``` para evitar errores de "Rango de consulta fuera de los límites".
* Para hacer la consulta en la API primero se debe loguear obteniendo una cookie encriptada:
    * ```$ curl -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=myusername&password=mY_S3cr3t_pA55w0rd!"```
* Luego se debe hacer la consulta utilizando la cookie
    * ```$ curl --cookie cookies.txt https://www.space-track.org/basicspacedata/query/class/boxscore```


## Configuracion

**Consideraciones**
- **space_track_config**: Tiene todas las configuraciones de URL para poder acceder a SpaceTrack
- **sleep_time**: Cada cuanto tiempo el programa realiza una nueva busqueda. 
- **interval**: Es el intervalo donde el script va a obtener un tiempo aleatorio de espera (0 a "interval" en segundos)

```json
{
    "kafka_config":{
        "bootstrap_servers": "kafka1:9092,kafka2:9093,kafka3:9094",
        "schema_registry_url": "http://localhost:8081",
        "schema_file": "tle_schema.json",
        "group_id": "tle-consumer-group",
        "client_id": "saocom-tle-publisher",
        "auto_offset_reset": "latest",
        "num_partitions": 3,
        "replication_factor": 3,
        "enable_idempotence": true,
        "acks": "all",
        "retries": 5,
        "max_in_flight_requests_per_connection": 5
        },
    "space_track_config":{
        "username": "ambrosino.ivan@gmail.com",
        "password": "/home/iambrosino/actualiza_tle/space-track-tle-publisher/test/password/spacetrack_passwd",
        "uri_base": "https://www.space-track.org",
        "request_login": "/ajaxauth/login",
        "request_cmd_action": "/basicspacedata/query",
        "request_get_last": "/class/tle_latest/ORDINAL/1/NORAD_CAT_ID",
        "order": "/orderby/TLE_LINE1",
        "format": ""
    },
    "topic_satellite_name": true,
    "sleep_time":3600,
    "interval": 60,
    "list_satelites":{
        "file": "list_satellites.config",
        "separator": ";",
        "name_collumns": true
    },
    "logs": {
        "folder":"logs",
        "filename": "tle_publisher.log",
        "rotation": 5,
        "size": 5000000,
        "debug_mode": false
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

### Listado de satelites

El listado se realiza en formato CSV, donde la primera columna es el **NoradID**, seguido del **nombre** del satelite y finalmente el **AltName** que seria el nombre aceptado por las antenas.
Para el caso de los TLE descargados de Space-Track, son los siguientes:

<pre>
NUMBER;NAME;ALTNAME
25994;TERRA;TERRA
27424;AQUA;AQUA
37849;NPP;SUOMI NPP
29079;EROS B;EROS B
31598;SKYMED 1;SKYMED 1
32376;SKYMED 2;SKYMED 2
33412;SKYMED 3;SKYMED 3
37216;SKYMED 4;SKYMED 4
39153;CUBEBUG 1;CUBEBUG 1
25338;NOAA 15;NOAA 15
28654;NOAA 18;NOAA 18
33591;NOAA 19;NOAA 19
38771;METOP-B;METOP-B
43689;METOP-C;METOP-C
38782;VRSS-1;VRSS-1
37793;APRIZESAT 6;APRIZESAT 6
39416;APRIZESAT 7;APRIZESAT 7
39425;APRIZESAT 8;APRIZESAT 8
40018;APRIZESAT 9;APRIZESAT 9
40019;APRIZESAT 10;APRIZESAT 10
38752;RBSP A;RBSPA
38753;RBSP B;RBSPB
25989;XMM;XMM
41557;NUSAT 1;NUSAT 1
41558;NUSAT 2;NUSAT 2
42760;NUSAT-3C;NUSAT 3C
43013;JPSS 1;JPSS 1
44229;HARBINGER;ICEYE-X3
38755;SPOT 6;SPOT 6
40053;SPOT 7;SPOT 7
28376;AURA;AURA
</pre>
