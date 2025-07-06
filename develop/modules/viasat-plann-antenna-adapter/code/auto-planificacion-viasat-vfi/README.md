# Schedule ACU 4100 

## Objetivo 

El objeto es crear un servicio que genere la planificacion para las antenas obteniendo los datos desde las BBDD de planificacion del segmento de estaciones terrenas. 
Los datos se obtienen curzando los datos de la planificacion con el de las tablas de macro y configuraciones de las DB.
+Aclaracion+
Para el caso de ETTdF identificar la antena tendra una  caracteristica diferente, ya que no hay configuraciones asociadeas a la planificacion.

## Funcionamiento 

Se debe crear un archivo de configuracion que contenga:

* datos de conexion a la unidad( ip o hostname, puerto)
* nombre de la unidad en la bbdd
* datos de conexion a la bbdd
* directorios q utilice el archivo

El sistema deberia realizar la consulta de pasadas, filtrar por unidad y mantener en una lista o diccionario el conjunto de pasadas que corresponden a la unidad designada en el archivo de configuracion.


Se puede consultar el conjunto de las pasadas via la API consultando al contenedor pasando como variable la unidad.
