### Proceso de Envio de Pasadas (ADD)

**INICIO**
0. Puede llegar un `NEWTLE` (se generan las actividades y se asignan) o `NEWPLANN` (solo se asignan)
    * Si se usa ``NEWTLE`` (crea actividades), asegurate de que se registren con ``updated_at = NOW()`` para que los filtros de ``updated > last_sent_at`` funcionen más adelante.
1. Se asigna en la antena, cargando la tabla `activity_assignments` la antena y su estado en ``'pending'`` sin fecha de envio (`last_sent_at` = NULL)
    1.1. El modulo envia un nuevo evento `SENDPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    - ``status = 'authorized' AND is_confirmed = TRUE``: Esta en estado listo para enviar
    - ``is_active = TRUE``: Es la asignacion activa (no tiene ninguna otra)
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

### Proceso de Modificacion de Pasada (UPDATE)

**INICIO**
0. El usuario registra una modificacion en una actividad
    1. Cambia el estado de la actividad a `'authorized'` (ya que la modificacion la hace un usuario que autoriza)
    2. Envia un nuevo evento de modificacion de la planificacion
1. Llegada de un evento `UPDATEPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    - Que la actividad este en estado ``'authorized'`` 
    - Que la actividad este con con campo ``is_confirmed = TRUE``
    - Si la asignacion esta activa `is_active = TRUE`
    - Si tiene asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena)
    - Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)
3. Cambia el estado de envio a `'pending'` (para ser enviado a la antena)
3. Arma el mensaje con todos los datos necesarios para el envio con su campo `UPDATE`
4. Cambiar el estado de las asignaciones enviadas a ``'sent'``
5. Enviar los mensajes
6. Si se configura el **ACK**:
    1. Carga todos los mensajes en la lista ACK para validar su carga
    2. Esperar la llegada de los mensajes ACK
    3. Eliminar de la lista de ACK los mensajes que vayan llegando.
    4. Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
7. Si **no se configura el ACK**, se confirman todas las actividades apenas se envian.
**FIN**

### Proceso de Cancelacion de Pasada (DELETE)

**INICIO**
0. El usuario registra una cancelacion de pasadas.
    1. Cambia el estado de la actividad a `'canceled'`
    2. Envia un nuevo evento de modificacion de la planificacion
1. Llegada de un evento `UPDATEPLANN` al **SenderModule**
2. El **SenderModule**, recorre el listado de actividades macheando las asignaciones y corrobora:
    - Que la actividad este en estado ``'canceled'`` 
    - Que la actividad este con con campo ``is_confirmed = TRUE``
    - Si la asignacion esta activa `is_active = TRUE`
    - Si tiene asignacion, esta en estado ``send_status = 'confirmed'`` (significa que se envio a la antena)
    - Se verifica si la **última vez que se envió a la antena** es anterior a la **última actualización** (`act.updated_at > aa.last_sent_at`)
3. Cambia el estado de envio a `'pending'` (para ser enviado a la antena)
4. Arma el mensaje con todos los datos necesarios para el envio con su campo `DELETE`
5. Cambiar el estado de las asignaciones enviadas a ``'sent'``
6. Enviar los mensajes
7. Si se configura el **ACK**:
    1. Carga todos los mensajes en la lista ACK para validar su carga
    2. Esperar la llegada de los mensajes ACK
    3. Eliminar de la lista de ACK los mensajes que vayan llegando.
    4. Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
8. Si **no se configura el ACK**, se confirman todas las actividades apenas se envian.
**FIN**

### Proceso de Reasignacion de Pasada (DELETE and ADD)

**INICIO**
0. El usuario registra una reasignacion de pasadas.
    1. Cambia la unidad de destino (antenna)
    2. El sistema verifica si tiene una asignacion activa. En caso de tenerla la marca como false `is_active = FALSE` y ``unassigned_at = NOW()``
    3. Se inserta una nueva fila con la nueva asignacion de antena y ``is_active = TRUE``, ``send_status = 'pending'`` y `is_confirmed = TRUE`
1. En este paso debe manejar dos mensajes. Para cada actividad que tenga dos o mas asignaciones (una sola activa)
    - Un mensaje de tipo `DELETE` para la antena origen (problema: necesita saber donde estuvo antes)
        1. Valida si existe un `activity_assignments` con ``is_active = FALSE`` y ``send_status = 'confirmed'``
            * Asignación previa confirmada (``send_status = 'confirmed'``)
            * Actividad en estado autorizado
            * Tiene marca de tiempo de desasignación
        2. Arma el mensaje `DELETE`
        3. Cambia el ``send_status = 'sent'`` y registra ``last_sent_at = NOW()``
        4. 7. Si se configura el **ACK**:
            * Carga todos los mensajes en la lista ACK para validar su carga
            * Esperar la llegada de los mensajes ACK
            * Eliminar de la lista de ACK los mensajes que vayan llegando.
            * Cambiar el estado a ``'confirmed'`` tras la llegada del ACK
    - Un mensaje de tipo `ADD` para la antena destino (necesita saber donde se especifica ir)
        2. Valida si existe un `activity_assignments` con ``is_active = TRUE`` y ``send_status = 'pending' or NULL``
            * Asignación existente y activa
            * Actividad en estado autorizado
            * Tiene marca de tiempo de desasignación
        2. Arma el mensaje `ADD`
        3. Cambia el ``send_status = 'sent'`` y registra ``last_sent_at = NOW()``
        4. 7. Si se configura el **ACK**:
            * Carga todos los mensajes en la lista ACK para validar su carga
            * Esperar la llegada de los mensajes ACK
            * Eliminar de la lista de ACK los mensajes que vayan llegando.
            * Cambiar el estado a ``'confirmed'`` tras la llegada del ACK


## Update vs Reasign

el Update y el Reasign tienen la misma estructura. Ambos tienen que eliminar una tarea y asignarla 
(la diferencia es que una la hace en la misma antena y la otra en diferentes antenas)

### Reasign

Si tenemos la siguiente actividad:

``('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'authorized', 'high')``
> El "authorized" indica que esta listo para ser enviado, se comprueban las asignaciones

Con las siguientes asignaciones:

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Indica que esta tarea es la que funciona ahora
``('ASG002', 'ACT002', 'ANT003', TRUE, TRUE, NULL, 'pending', NULL)`` --> Esta es la nueva asignacion, que indica una reasignacion a la antena **ANT003**

### Reasign

Si tenemos la siguiente actividad:

``('ACT001', '25544', '12345', '2023-06-01 08:00:00+00', '2023-06-01 08:15:00', 78.50, '2023-06-01 08:30:00+00', 1800, 'authorized', 'high')``
> El "authorized" indica que esta listo para ser enviado, se comprueban las asignaciones

Con las siguientes asignaciones:

``('ASG001', 'ACT001', 'ANT001', FALSE, TRUE, '2023-06-01 14:05:00', 'confirmed', '2023-06-01 14:05:00')`` --> Indica que esta tarea es la que funciona ahora
``('ASG002', 'ACT002', 'ANT001', TRUE, TRUE, NULL, 'pending', NULL)`` --> Esta es la nueva asignacion, que indica un update de la actividad en la antena **ANT001**

```sql
SELECT 
    aa_old.antenna_id AS old_antenna,
    aa_new.antenna_id AS new_antenna,
    a.id AS activity_id,
    CASE 
        WHEN aa_old.antenna_id != aa_new.antenna_id THEN 'reassign'
        ELSE 'update'
    END AS action_type
FROM activities a
JOIN activity_assignments aa_old ON aa_old.activity_id = a.id AND aa_old.send_status = 'confirmed'
JOIN activity_assignments aa_new ON aa_new.activity_id = a.id AND aa_new.send_status = 'pending'
WHERE a.status = 'authorized'
  AND aa_old.is_confirmed = TRUE
  AND aa_new.is_confirmed = TRUE;
```