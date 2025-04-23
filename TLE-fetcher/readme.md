# Space Track Downloader

Modulo que se encarga de la obtencion de TLEs para todos los satelites especificados.

### Resultado de la consulta
```json
[
    {
        "ORDINAL": "1",
        "COMMENT": "GENERATED VIA SPACETRACK.ORG API",
        "ORIGINATOR": "18 SPCS",
        "NORAD_CAT_ID": "27424",
        "OBJECT_NAME": "AQUA",
        "OBJECT_TYPE": "PAYLOAD",
        "CLASSIFICATION_TYPE": "U",
        "INTLDES": "02022A",
        "EPOCH": "2024-10-24 20:34:48",
        "EPOCH_MICROSECONDS": "889056",
        "MEAN_MOTION": "14.60134861",
        "ECCENTRICITY": "0.0002353",
        "INCLINATION": "98.3457",
        "RA_OF_ASC_NODE": "248.8647",
        "ARG_OF_PERICENTER": "69.9556",
        "MEAN_ANOMALY": "342.7855",
        "EPHEMERIS_TYPE": "0",
        "ELEMENT_SET_NO": "999",
        "REV_AT_EPOCH": "19559",
        "BSTAR": "0.0006857",
        "MEAN_MOTION_DOT": "0.00003253",
        "MEAN_MOTION_DDOT": "0",
        "FILE": "4533525",
        "TLE_LINE0": "0 AQUA",
        "TLE_LINE1": "1 27424U 02022A   24298.85751029  .00003253  00000-0  68570-3 0  9999",
        "TLE_LINE2": "2 27424  98.3457 248.8647 0002353  69.9556 342.7855 14.60134861195596",
        "OBJECT_ID": "2002-022A",
        "OBJECT_NUMBER": "27424",
        "SEMIMAJOR_AXIS": "7070.876",
        "PERIOD": "98.621",
        "APOGEE": "694.404",
        "PERIGEE": "691.077",
        "DECAYED": "0" 
    }
]
```

### Requerimientos de Consulta

Para hacer las consultas de Space-Track se deben tener los siguientes **requerimientos**:

* Los TLE se pueden **descargar cada 1 hora**. Se debe **elegir al azar un minuto** para esta consulta que no esté en el parte superior o inferior de la hora.
* Para hacer una sola consulta de un conjunto TLE y que obtenga **ciertos campos** que se necesitan, se pueden concatenar con "," en la consulta y agregarle /predicates/:
    * Ejemplo: https://www.space-track.org/basicspacedata/query/class/tle_latest/ORDINAL/1/NORAD_CAT_ID/25544,36411,26871,27422/predicates/FILE,EPOCH,TLE_LINE1,TLE_LINE2/format/html
    ```
        FILE       EPOCH                  TLE_LINE1                                                           TLE_LINE2
        1339414    2012-08-23 14:41:35    1 25544U 98067A 12236.61221542 .00014781 00000-0 26483-3 0  1660    2 25544 051.6476 145.7539 0014860 352.2902 087.3290 15.50074566788503
        1339388    2012-08-23 13:09:41    1 36411U 10008A 12236.54839284 .00000068 00000-0 00000+0 0  1996    2 36411 000.4393 261.8677 0004087 269.6508 223.6226 01.00284253 9094
        1339308    2012-08-23 09:04:34    1 26871U 01031A 12236.37818175 -.00000300 00000-0 10000-3 0 7001    2 26871 002.4043 072.3013 0002099 076.5029 259.0419 01.00285194 40660
        1339234    2012-08-23 05:26:49    1 27422U 02021B 12236.22696129 .00000039 00000-0 32070-4 0  9902    2 27422 098.3978 295.8841 0013298 043.4759 316.7468 14.28769327535462
    ```

* Formato de la URL para la consulta debe ser: ```https://www.space-track.org/basicspacedata/query/class/boxscore/```
    * Base: URL: ```https://www.space-track.org/```
    * Controlador de solicitudes: ```basicspacedata/```
    * Acción de solicitud: ```querry/```
    * Pares de valores de predicado: ```class/nameclass/```
        * Nombre de la clase: ```tle_latest```
        * ```ORDINAL/1``` Cuanto menor sea el ORDINAL, más reciente se agregó el ELSET. Por ejemplo, añadiendo ```/ORDINAL/1/``` a la URL mostrará solo el ELSET más reciente de cada objeto.
        * ```NORAD_CAT_ID/ID,ID,ID/``` para obtener los TLEs de un listado de IDs de Satelites.
    * Space-Track recomienda limitar las consultas de la API en ```OBJECT_NUMBER / NORAD_CAT_ID``` Y un **rango de época** como ```>now-30``` para evitar errores de "Rango de consulta fuera de los límites".
* Para hacer la consulta en la API primero se debe loguear obteniendo una cookie encriptada:
    * ```$ curl -c cookies.txt -b cookies.txt https://www.space-track.org/ajaxauth/login -d "identity=myusername&password=mY_S3cr3t_pA55w0rd!"```
* Luego se debe hacer la consulta utilizando la cookie
    * $ ```curl --cookie cookies.txt https://www.space-track.org/basicspacedata/query/class/boxscore```
