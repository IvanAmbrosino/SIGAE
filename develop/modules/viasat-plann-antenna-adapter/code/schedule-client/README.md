# Schedule Automatico antenas VIASAT - VFI

## Introduccion

Cliente que se conecta a un servidor PAI REST pasandole el nombre de la unidad en una URL y le devuelve las pasadas para la unidad.
Luego de esto construye un archivo de planificacion para que lo lea la VFI de la unidad. En este caso funciona para las unidades definidas en los ConfigurationItems:

* https://cgss-managment-tools.et.conae.gov.ar/issues/773
* https://cgss-managment-tools.et.conae.gov.ar/issues/882
* https://cgss-managment-tools.et.conae.gov.ar/issues/340

Al final del proceso deberian haberse cargado y/o actualizado las actividades en funcion de la base de datos de planificacion.

## Funcionamiento


__Desde la perspectiva de el sistema los pasos debieran ser los siguientes.__

* Debe existier la ephem del satelite a cargar.
* Debe ser visible en el horizonte en algun momento usando la ephem cargada.
* No debe generar conflicto con otras actividades ya cargadas.
* Debe tener prepass de no menos de 2 minutos.


__Circuito de los archivos:__

La app debe enviar:

1. Archivo **rciSched** con las actividades
2. Archivo **rciSched.done** avisando que termino el envio

Luego de esto el sistema deberia generar:

1. Archivo **importSched**
2. Archivo **importSched.done** informando que temrino de procesar


## Automatizacion de la planificacion

El sistema de schedule ejecuta los siguientes pasos:

1. se conecta por ftp a la *SCC* del sistema de antena, recupera las actividades para el dia que ya fueron cargadas.
2. se conecta a la API Schedule y recupera las tareas para la unidad
3. compara las actividades cargadas con las que devuelve la API
4. Genera una lista por operacion: 
* * update
* * insert
* * cancel
5. Para cada lista genera un archivo valido para la VFI usando el modulo _make_vfi_
6.  Envia a la SCC en el PATH definido en el archivo de configuracion los archivos 

En relacion al punto *1* esto podria reemplazase usando una bbdd y recuperando el importSched con las pasadas ya cargadas. Esto podria ser mas facil que parsear todo el traer y parsear todo el XML. Para esto el taskid tiene que ser inconfundible.
Actualmente este es el formato:

<pre>
    <Task>
        <TaskID>SAR22024079085617</TaskID>
        <Action>ADD</Action>
        <Track>
            <Satellite>SAR2</Satellite>
            <AntennaID>CORDOBA</AntennaID>
            <ConfigID>2</ConfigID>
            <StartTime>2024 079 08:56:17</StartTime>
            <EndTime>2024 079 09:04:05</EndTime>
            <PrePass>
                <StartOffsetTime>120</StartOffsetTime>
            </PrePass>
            <PostPass>
                <Enabled>Yes</Enabled>
                <Duration>120</Duration>
            </PostPass>
        </Track>
    </Task>
</pre>

La respuesta es:

<pre>
  <Task>
    <TaskID>SSAR22024080090200</TaskID>
    <Status>ACCEPTED</Status>
  </Task>
</pre>

Este parametro *<TaskID>SSAR22024080090200</TaskID>* es el que deberia cambiar a *<TaskID>SateliteOrbita</TaskID>* para hacerlo inconfundible.

Reemplazar la recuperacion del *rciSched* para hacer mas agil la generacion de archivos se puede usar redis y almacenar el json que se obtiene de la API directamente, junto con el TaskID.

### Estructura del archivo rci

Algunas consideraciones sobre el armado del archivo:

El campo *TaskID* no deberia usar el formato nombre de satelite + AOS, es poco practico para identificar la actividad. Seria mejor utilizar la orbita, que no deberia cambiar aunque se actualce el horario.


## Usando Redis como cache

1. Recupero las actividades de la API
2. Almaceno las actividades en redis como documento con el TaskID como key.
3. Valida que este cargada en REDIS, si no esta lo carga y genera el Schedule

Sigue el proceso mencionado antes en *Automatizacion de la planificacion*


