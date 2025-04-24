# TLE Sender

Modulo que se encarga de la recuperacion del TLE del bocker de KAFKA y es enviado a las distintas antenas.

## Estructura

Se desarrolla una primera versión con la siguiente estructura:
<pre>
.
├── __init__.py                 # Script principal con la funcionalidad PostTLE
├── config_manager.py           # Modulo que carga las configuraciones
├── connections.py              # Modulo que contiene la lógica de carga de TLE para las diferentes antenas
├── format_tle.py               # Script que formatea los TLE PPM
├── redis_manager.py            # Modulo para el manejo de conexión con redis
├── logs/                       # Directorio destinado a archivos de logs
├── configs/                    #
     ├── config.json            # Archivo de configuración del PostTLE
     └── list_satellites.config # Archivo con la lista de satélites asignados a la antena 
└── tmp/                        #
     └── tle_tmp.txt            # Archivo temporal usado para el formateo y armado y envió del conjunto de TLEs a la antena
</pre>

### Aclaración

Para acceder a las antenas **Viasat de 6.1 y 5.4**, se deben realizar saltos entre equipos mediante **Túneles**, por lo que se deben especificar adicionalmente en el archivo de configuración.
Se especifica en la opcion **"type"** del archivo de configuracion estableciendo las siguientes opciones:
* **datron** 
* **viasat direct**
* **viasat tunnel**
* **viasat double tunnel**

**viasat tunnel** y **viasat double tunnel** estan desarrollados para sistemas donde las SCC son virtuales en un servidor.


## Configuración

```json
{
    "tle_request":{
        "logs_file":"./logs/tle_request.log",
        "redis_host":"localhost",
        "redis_port":6379,
        "secret_redis_path":"/run/secrets/redis_password"
    },
    "type":"viasat direct",
    "server_config":{
        "server_ip":"ip_ant_viasat",
        "server_user":"user",
        "server_password":"/run/secrets/ant_vst_password",
        "destination_path":"/etc/remote/"
    },
    "server_tunnel":{      # Si la antena tiene un solo salto
        "server_ip":"",
        "server_user":"",
        "server_password":""
    },
    "second_server_tunnel":{      # Si la antena tiene dos saltos
        "server_ip":"",
        "server_user":"",
        "server_password":""
    }
}
```
## Lista de Satélites

Se deben especificar los TLE que van a ser cargados en las antenas. Se utiliza una archivo llamado ``list_satellites.config`` que contiene una lista de **norad_id;Nombre** de cada satelite
<pre>
43641U;SAOCOM-1A
46265U;SAOCOM-1B
31598;SKYMED 1
32376;SKYMED 2
33412;SKYMED 3
37216;SKYMED 4
</pre>

## Conexión a Redis

La obtención del TLE se realiza consultando el ultimo elemento agregado en la cola de Redis, donde la KEY es cada uno de los norad_id de los satélites:
```python
# Se obtiene el NoradID y el TLE del satelite.
REDIS_LIST_KEY = "43641U"
TLE = {
        "name": "SAOCOM-1A",
        "line1": "1 43641U 18076A   24284.89974537 0.00000111  00000-0 014188-4 0    04",
        "line2": "2 43641  97.8887 109.4672 0001393  83.8212 141.0691 14.82130712    07"
    }
TLE["timestamp"] = str(datetime.now()) # Agregar un campo timestamp al TLE (por si hay que ordenarlo por fecha de llegada)
redis_client.lpush(REDIS_LIST_KEY, TLE) # Para PILA (LIFO): usamos LPUSH
print(f"Elemento agregado: {item_json}")
```

### Obtencion de TLE con REDIS

```python
    def get_latest_tle(self,norad_id):
        """Obtiene el ultimo TLE para un satelite en particular"""
        self.connect_reddis()
        latest_tle = self.client.lindex(norad_id, 0)  # Se obtiene el ultimo elemento agregado
        self.disconect_redis()
        return json.loads(latest_tle) if latest_tle else None
```

### Obtencion de TLE con KAFKA

Ante el cambio del middleware (Redis por Kafka), se realiza un cambio en el componente adaptador que conecta con el sistema de brockers de kafka. Se implementa como un Generador, que realiza un stream constante de datos y, ante la llegada de un TLE, este se procesa y se actualiza en la antena.

```python
   def connect_to_kafka(self):
        """Intenta conectarse a Kafka. Reintenta en caso de fallo."""
        while True:
            try:
                self.consumer = KafkaConsumer(
                    bootstrap_servers=self.config['bootstrap_servers'],
                    group_id=self.config['group_id'],
                    auto_offset_reset=self.config['auto_offset_reset'],  # Se reanuda desde el último mensaje leído
                    enable_auto_commit=True,  # Kafka almacena automáticamente los offsets
                )
                self.logger.info("Connected to Kafka successfully.")
                return self.consumer
            except (NoBrokersAvailable,KafkaError) as e:
                self.logger.error(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
                time.sleep(5)

    def get_message(self,list_satellites):
        """
        Obtiene un mensaje de Kafka.
        Recorre la lista de satelites, se suscribe a cada uno de ellos y obtiene el ultimo TLE.
        Devuelve un stream de los ultimos TLEs. que van llegando.
        """
        self.connect_to_kafka()
        try:
            lista_suscripciones = [f"{satelite.split(';')[0]}" for satelite in list_satellites]
            self.consumer.subscribe(lista_suscripciones)
            while True:
                message_batch = self.consumer.poll(timeout_ms=10)
                if message_batch:
                    for _, messages in message_batch.items():
                        for message in messages:
                            yield json.loads(message.value.decode('utf-8'))
        except KafkaError as e:
            self.logger.error(f"Error consuming messages: {e}. Reconnecting...")
        finally:
            self.consumer.close()
```

Luego en la funcion principal ocurren dos cosas:
* Al iniciar el contenedro, se obtienen todos los ultimos TLE presentes en el brocker. En el caso que hayan varios, (por inactividad del servicio) se obtiene el ultimo comparando por timestamp de los mensajes.
```python
        self.tles = self.kafka_conector.get_bulk_message(self.list_satellites,5) # Obtiene todos los TLE
        self.tles = [self.format_tle.format_tle(tle) for tle in self.tles] # Los formatea
        if self.update_new_tle(self.tles,self.header):
            self.make_tle_file(self.tles) # arma el archivo tmp
            subprocess.run(["unix2dos", self.tmp_archive], check=True) # Se convierte en formato DOS
            self.send_archive()
            subprocess.run(["cp", self.tmp_archive, self.tmp_archive_bkp], check=True) # Se guarda el archivo generado como backup
            logger.info('TLE enviado')
        else:
            for tle in self.tles:
                logger.info(f"No hay cambios en el TLE {tle['name']}")
```
* Luego inicia el bucle de espera de mensajes, donde:
    1. Al llegar un TLE lo formatea
    2. Arma el archivo con el formato correcto (DOS)
    3. Actualiza el archivo BKP
    4. Envia el archivo a la antena
```python
        for get_tle in self.kafka_conector.get_message(self.list_satellites):
            if isinstance(get_tle,dict):
                format_tle = self.format_tle.format_tle(get_tle)
                self.tles.append(format_tle)

                if self.update_new_tle(self.tles,self.header):
                    self.make_tle_file(self.tles) # arma el archivo tmp
                    subprocess.run(["unix2dos", self.tmp_archive], check=True) # Se convierte en formato DOS
                    self.send_archive()
                    logger.info('TLE enviado')
                else:
                    for tle in self.tles:
                        logger.info(f"No hay cambios en el TLE {tle['name']}")
                self.tles = [] # Se limpia la lista de TLEs
```

Se hacen uso de dos archivos temporales:
* **tle_bkp.txt**: Contiene el listado del último TLE actualizado para cada uno de los satélites presente en el archivo ``list_satellites.config``.
* **tle_tmp.txt**: Archivo temporal usado para el formateo y armado y envió del conjunto de TLEs a la antena.

## Envío del TLE

Se realiza por sftp al servidor destino. Para las antenas de Viasat se verifica si se acepta el TLE:
```python
        try:
            ssh_client = self.create_ssh_client(server_ip,user=server_user,password=server_password)
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(self.tmp_archive, f"{destination_path}{self.tle_filename}")
            sleep(180) # Espera 3 minutos
            remote_file_path = f"{destination_path}{self.tle_filename}"
            _, stdout, _ = ssh_client.exec_command(f"grep 'ACCEPTED' {remote_file_path}")
            result = stdout.read().decode().strip()

            if "ACCEPTED" in result:
                print(f"La palabra 'ACCEPTED' fue encontrada en el archivo {self.tle_filename}.")
            else:
                print(f"La palabra 'ACCEPTED' no fue encontrada en el archivo {self.tle_filename}.")

            sftp_client.close()
            ssh_client.close()
        except paramiko.ChannelException as e:
            print("Error enviando el archivo al servidor destino: %s",e)
```

En el caso que haya que hacer saltos entre servidores, se utilizan los Tuneles SSH:
```python
        with SSHTunnelForwarder(
            (servidor_intermedio, 22),  # Dirección y puerto del servidor intermedio
            ssh_username=usuario_servidor_intermedio,
            ssh_private_key=None,
            ssh_password=password_servidor_intermedio,
            remote_bind_address=(maquina_virtual, 22),  # Dirección y puerto de la VM
            local_bind_address=('127.0.0.1', 2222)  # Puerto local para el túnel
        ) as tunnel:
            print("Túnel SSH creado. Conectando a la máquina virtual...")

            # Configurar cliente SFTP
            transport = paramiko.Transport(('127.0.0.1', tunnel.local_bind_port))
            transport.connect(
                username=usuario_vm,
                password=password_vm
            )
            sftp = paramiko.SFTPClient.from_transport(transport)
            ...
```
