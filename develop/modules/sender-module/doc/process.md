# Procesos de Envio

## Proceso de Envio de Pasadas (ADD)

**INICIO**

0. Puede llegar un `NEWTLE` (se generan las actividades y se asignan) o `NEWPLANN` (solo se asignan)
    * Si se usa ``NEWTLE`` (crea actividades), asegurate de que se registren con ``updated_at = NOW()`` para que los filtros de ``updated > last_sent_at`` funcionen más adelante.
1. Se asigna en la antena, cargando la tabla `activity_assignments` la antena y su estado en ``'pending'`` sin fecha de envio (`last_sent_at` = NULL)
    1.1. El modulo envia un nuevo evento `SENDPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    - ``status = 'authorized' AND is_confirmed = TRUE``: Esta en estado listo para enviar
    - ``len(asignaciones) == 1``: Solamente debe tener una sola asignacion
    - ``is_active = TRUE``: Es la asignacion activa
    - ``send_status = 'pending'``: Si tiene asignacion y esta en estado ``'pending'``
    - Que su **fecha sea mayor a la actual** sumado a un **intervalo de seguridad**
    - Validar que no haya otro **activity_assignment** activo para la misma actividad (**evitar duplicados** por error).
3. Arma el mensaje con todos los datos necesarios para el envio con su campo `ADD`
4. Cambiar el estado de las asignaciones enviadas a ``'sent'``
5. Enviar los mensajes
6. Si se configura el ACK:
    1. Carga todos los mensajes en la lista ACK para validar su carga
    2. Esperar la llegada de los mensajes ACK
    3. Eliminar de la lista de ACK los mensajes que vayan llegando.
    4. Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
7. Si no se configura el ACK, se confirman todas las actividades apenas se envian.

**FIN**

## Proceso de Cancelacion de Pasada (DELETE)

**INICIO**

0. El usuario registra una cancelacion de pasadas.
    1. Cambia el estado de la actividad a `'canceled'`
    2. Envia un nuevo evento de modificacion de la planificacion
1. Llegada de un evento `UPDATEPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    * En este caso, hay que validar la nueva asignacion en ``'pending'`` y si tiene otra asignacion (num_asignaciones >= 2)
        - Si tiene 2 o mas asignaciones, se evalua la ultima en ``send_status = 'confirmed'``
        - Si hay una diferencia de antenas (``ant1 != ant2 is true``) debe generar un **error**
    - ``status = 'delete' AND is_confirmed = TRUE``: Que la actividad este en estado delete
    - ``len(asignaciones) >= 1``: Solamente debe tener una sola asignacion
    - ``is_active = TRUE``: Es la asignacion activa
    - ``send_status = 'pending'``: Si tiene asignacion y esta en estado ``'pending'`` 
    - Si tiene otra asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena y hay que borrar)
    - Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)
3. Arma el mensaje con todos los datos necesarios para el envio con su campo `DELETE`
4. Cambiar el estado de las asignaciones enviadas a ``'sent'``
5. Enviar los mensajes
6. Si se configura el **ACK**:
    1. Carga todos los mensajes en la lista ACK para validar su carga
    2. Esperar la llegada de los mensajes ACK
    3. Eliminar de la lista de ACK los mensajes que vayan llegando.
    4. Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
7. Si **no se configura el ACK**, se confirman todas las actividades apenas se envian.

**FIN**

## Proceso de Modificacion de Pasada (UPDATE)

**INICIO**

0. El usuario registra una modificacion en una actividad
    1. Cambia el estado de la actividad a `'authorized'` (ya que la modificacion la hace un usuario que autoriza)
    2. Envia un nuevo evento de modificacion de la planificacion
1. Llegada de un evento `UPDATEPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    * En este caso, hay que validar la nueva asignacion en ``'pending'`` y si tiene otra asignacion (num_asignaciones >= 2)
        - Si tiene 2 o mas asignaciones, se evalua la ultima en ``send_status = 'confirmed'``
        - Si no hay diferencia de antenas (``ant1 == ant2 is true``), mandar un **DELETE** y un **ADD a la misma antena**
    - ``status = 'authorized' AND is_confirmed = TRUE``: Que la actividad este en estado delete
    - ``len(asignaciones) == 1``: Tiene mas de una asignacion
    - ``is_active = TRUE``: Es la asignacion activa
    - ``send_status = 'pending'``: Si tiene asignacion y esta en estado ``'pending'``
    - Si tiene otra asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena y hay que borrar)
        - Obtiene la ultima asignacion en estado ``send_status = 'confirmed'``
        - Verifica si no hay diferencia de antenas (``ant1 == ant2 is true``) **UPDATE**
    - Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)
3. Arma el mensaje con todos los datos necesarios para el envio con su campo `UPDATE`
    1. Crea un mensaje **DELETE** y **ADD** para la **misma antena** y los agrega en la lista para ser enviados
4. Cambiar el estado de las asignaciones enviadas a ``'sent'``
5. Enviar los mensajes
6. Si se configura el **ACK**:
    1. Carga todos los mensajes en la lista ACK para validar su carga
    2. Esperar la llegada de los mensajes ACK
    3. Eliminar de la lista de ACK los mensajes que vayan llegando.
    4. Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
7. Si **no se configura el ACK**, se confirman todas las actividades apenas se envian.

**FIN**

## Proceso de Reasignacion de Pasada (DELETE and ADD)

**INICIO**

0. El usuario registra una modificacion en una actividad
    1. Cambia el estado de la actividad a `'authorized'` (ya que la modificacion la hace un usuario que autoriza)
    2. Envia un nuevo evento de modificacion de la planificacion
1. Llegada de un evento `UPDATEPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    * En este caso, hay que validar la nueva asignacion en ``'pending'`` y si tiene otra asignacion (num_asignaciones >= 2)
        - Si tiene 2 o mas asignaciones, se evalua la ultima en ``send_status = 'confirmed'``
        - Si no hay diferencia de antenas (``ant1 == ant2 is true``), mandar un **DELETE a la antena origen** y un **ADD a la antena destino**
    - ``status = 'authorized' AND is_confirmed = TRUE``: Que la actividad este en estado delete
    - ``len(asignaciones) == 1``: Tiene mas de una asignacion
    - ``is_active = TRUE``: Es la asignacion activa
    - ``send_status = 'pending'``: Si tiene asignacion y esta en estado ``'pending'``
    - Si tiene otra asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena y hay que borrar)
        - Obtiene la ultima asignacion en estado ``send_status = 'confirmed'``
        - Verifica que hay diferencia de antenas (``ant1 != ant2 is true``) **REASIGNACION**
    - Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)
3. Arma el mensaje con todos los datos necesarios para el envio con su campo `REASIGN`
    1. Crea un mensaje **DELETE** y **ADD** para las antenas correspondientes.
4. Cambiar el estado de las asignaciones enviadas a ``'sent'``
5. Enviar los mensajes
6. Si se configura el **ACK**:
    1. Carga todos los mensajes en la lista ACK para validar su carga
    2. Esperar la llegada de los mensajes ACK
    3. Eliminar de la lista de ACK los mensajes que vayan llegando.
    4. Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
7. Si **no se configura el ACK**, se confirman todas las actividades apenas se envian.

**FIN**

### NOTA
Para los casos en que se envian dos mensajes, ambos van a ser validados con el mismo ID, en el caso de que uno falle, el send_status va a ser cargado con ``'failed'``
> tener en cuenta que no se puede pasar de ``'failed'`` -> ``'confirmed'``, si uno falla, ambos fallan. Es para el caso que el primer ACK que llega sea con error y el segundo sea correcto. (evita sobreescribirse)

## Ejemplos de procesamiento

### Add

Si tenemos la siguiente actividad:

``('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'authorized', 'high')``

Con las siguientes asignaciones:

``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE, NULL, 'pending', NULL)`` --> Esta es la nueva asignacion, que indica el **estado del envio del mensaje DELETE**

Al finalizar la Reasignacion, los valores son los siguientes

``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE,'2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Esta es la asignacion en curso

Al filtrarlas, para no volver a procesar una actividad (en estado ``'authorized'``) se filtra si tiene una asignacion en estado ``'pending'``

En este caso, hay que **validar** la nueva asignacion en ``'pending'`` y si solo tiene una asignacion asignacion (num_asignaciones == 1)
- Si tiene 1 asignacion con ``send_status = 'confirmed'``

Las actividades se **filtran** con:
- Que la actividad este en estado ``'authorized'``
- Que la unica asignacion esta en estado ``'pending'`` 
- Que la actividad este con con campo ``is_confirmed = TRUE`` (indica la asignacion que esta en uso)
- Si la asignacion esta activa `is_active = TRUE`

**Pseudocodigo**
```python
actividades = get_act_to send() # Busca todas las actividades con asignacion en estado 'pending'
for act,act_asig in actividades:
    if act.status == 'authorized':
        if len(asignaciones) == 1: # Pensar tambien el caso que pase de un estado 'delete' -> 'authorized' (va a tener 2 asignaciones)
            if act_asig.send_action == 'add' and act_asig.send_action == 'pending':
                message = make_message_delete(act, act_asig)     # Creamos el mensaje a enviar
                list_messages[act_asign.antenna].append(message) # Agregamos a la lista de mensajes para las diferentes antenas
```

## Update vs Reasign vs Delete

el Update y el Reasign tienen la misma estructura. Ambos tienen que eliminar una tarea y asignarla 
(la diferencia es que una la hace en la misma antena y la otra en diferentes antenas)

Se puede tomar la tabla asignaciones como un registro de envios a las antenas, donde la ultima asignacion activa es donde actualmente se encuentra asignada.
Para las actividades que se cancelan, siguen teniendo el registro de asignaciones, pero todas desactivadas

---

### Delete

Si tenemos la siguiente actividad:

``('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'delete', 'high')``
> El "delete" indica que se elimino de la planificacion, en este caso hay que validar si tiene alguna asignacion

Con las siguientes asignaciones:

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Indica que esta tarea es la que funciona ahora
``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE, NULL, 'pending', NULL)`` --> Esta es la nueva asignacion, que indica el **estado del envio del mensaje DELETE**

O podemos usar el campo `is_active` de la asignacion, ya que ninguna actividad cancelada deberia tener asignaciones activas.

Al finalizar la Reasignacion, los valores son los siguientes

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Historial de asignacion
``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE,'2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Esta es la nueva asignacion, indicando que se envio correctamente el mensaje DELTE.

Al filtrarlas, para no volver a procesar una actividad en estado delete se filtra si tiene una asignacion en estado ``'pending'``

En este caso, hay que validar la nueva asignacion en ``'pending'`` y si tiene otra asignacion (num_asignaciones >= 2)
- Si tiene 2 o mas asignaciones, se evalua la ultima en ``send_status = 'confirmed'``
- Si hay una diferencia de antenas (``ant1 != ant2 is true``) debe generar un **error**

Las actividades se filtran con:
- Que la actividad este en estado ``'delete'``
- Que la nueva asignacion esta en estado ``'pending'`` 
- Que la actividad este con con campo ``is_confirmed = TRUE`` (indica la asignacion que esta en uso)
- Si la asignacion esta activa `is_active = TRUE`
- Si tiene otra asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena)
- Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)

**Pseudocodigo**
```python
actividades = get_act_to send() # Busca todas las actividades con asignacion en estado 'pending'
for act,act_asig in actividades:
    if act.status == 'delete':
        if act_asig.send_action == 'delete' and act_asig.send_action == 'pending':
            message = make_message_delete(act, act_asig)     # Creamos el mensaje a enviar
            list_messages[act_asign.antenna].append(message) # Agregamos a la lista de mensajes para las diferentes antenas
```

---

### Reasign

Si tenemos la siguiente actividad:

``('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'authorized', 'high')``
> El "authorized" indica que esta listo para ser enviado, se comprueban las asignaciones

Con las siguientes asignaciones:

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Indica que esta tarea es la que funciona ahora
``('ASG002', 'ACT002', 'ANT003', TRUE, TRUE, NULL, 'pending', NULL)`` --> Esta es la nueva asignacion, que **indica una reasignacion** a la antena **ANT003**

Al finalizar la Reasignacion, los valores son los siguientes

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Historial de asignacion
``('ASG002', 'ACT002', 'ANT003', TRUE, TRUE,'2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Esta es la nueva asignacion, que indica una reasignacion a la antena **ANT003**

En este caso, hay que validar la nueva asignacion en ``'pending'`` y si tiene otra asignacion (num_asignaciones >= 2)
- Si tiene 2 o mas asignaciones, se evalua la ultima en ``send_status = 'confirmed'``
- Si hay una diferencia de antenas (``ant1 != ant2 is true``), mandar un **DELETE a la antena origen** y un **ADD a la antena destino**

Las actividades se filtran con:
- Que la actividad este en estado ``'authorized'``
- Que la nueva asignacion esta en estado ``'pending'`` 
- Que la actividad este con con campo ``is_confirmed = TRUE`` (indica la asignacion que esta en uso)
- Si la asignacion esta activa `is_active = TRUE`
- Si tiene otra asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena)
- Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)

**Pseudocodigo**
```python
actividades = get_act_to send() # Busca todas las actividades con asignacion en estado 'pending'
for act,act_asig in actividades:

    if act.status == 'authorized':
        if len(asignaciones) > 1:
            asignaciones_ordenadas = sorted(
                    asignaciones,
                    key=lambda x: (not x['is_active'], x['assigned_at']),
                    reverse=True
                )
            asignacion_activa = next(
                (a for a in asignaciones_ordenadas if a['is_active']), 
                None
            )
            asignacion_anterior = next(
                (a for a in asignaciones_ordenadas 
                    if not a['is_active'] and a['send_status'] == 'confirmed'),
                None
            )
            if asignacion_activa.send_action == 'reasign' and act_asig.send_action == 'pending':
                delete_message = make_message_delete(act, asignacion_anterior) # Creamos el mensaje delete
                add_message = make_message_add(act, asignacion_activa)         # Creamos el mensaje add
                list_messages[asignacion_anterior.antenna].append(delete_message)   # Agregamos a la lista de mensajes para las diferentes antenas
                list_messages[asignacion_activa.antenna].append(add_message)        # Agregamos a la lista de mensajes para las diferentes antenas
```

---

### Update

Si tenemos la siguiente actividad:

``('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'authorized', 'high')``
> El "authorized" indica que esta listo para ser enviado, se comprueban las asignaciones

Con las siguientes asignaciones:

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Indica que esta tarea es la que funciona ahora
``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE, NULL, 'pending', NULL)`` --> Esta es la nueva asignacion, que indica un **update de la actividad en la antena** **ANT001**

Al finalizar el Update, los valores son los siguientes

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Historial de asignacion
``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE,'2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Esta es la nueva asignacion, que indica un update de la actividad en la antena **ANT001**

En este caso, hay que validar la nueva asignacion en ``'pending'`` y si tiene otra asignacion (num_asignaciones >= 2)
- Si tiene 2 o mas asignaciones, se evalua la ultima en ``send_status = 'confirmed'``
- Si no hay diferencia de antenas (``ant1 == ant2 is true``), mandar un **DELETE** y un **ADD a la misma antena**
> Tener en cuenta que las actividades deben estar ordenadas. Primero el DELETE y luego el ADD

Las actividades se filtran con:
- Que la actividad este en estado ``'authorized'``
- Que la nueva asignacion esta en estado ``'pending'`` 
- Que la actividad este con con campo ``is_confirmed = TRUE`` (indica la asignacion que esta en uso)
- Si la asignacion esta activa `is_active = TRUE`
- Si tiene otra asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena)
- Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)

**Pseudocodigo**
```python
actividades = get_act_to send() # Busca todas las actividades con asignacion en estado 'pending'
for act,act_asig in actividades:

    if act.status == 'authorized':
        if len(asignaciones) > 1:
            asignaciones_ordenadas = sorted(
                    asignaciones,
                    key=lambda x: (not x['is_active'], x['assigned_at']),
                    reverse=True
                )
            asignacion_activa = next(
                (a for a in asignaciones_ordenadas if a['is_active']), 
                None
            )
            asignacion_anterior = next(
                (a for a in asignaciones_ordenadas 
                    if not a['is_active'] and a['send_status'] == 'confirmed'),
                None
            )
            if asignacion_activa.send_action == 'update' and act_asig.send_action == 'pending':
                delete_message = make_message_delete(act, asignacion_anterior) # Creamos el mensaje delete
                add_message = make_message_add(act, asignacion_activa)         # Creamos el mensaje add
                list_messages[asignacion_anterior.antenna].append(delete_message)   # Agregamos a la lista de mensajes para las diferentes antenas
                list_messages[asignacion_activa.antenna].append(add_message)        # Agregamos a la lista de mensajes para las diferentes antenas
```