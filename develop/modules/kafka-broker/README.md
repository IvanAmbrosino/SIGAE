## Schema Registry

Stack de docker implementando Schema Registry para la validacion del formato del mensaje con AVRO.

* Avro tiene apoyo a primitivo ( int, boolean, string, floatetc.) y complejo ( enums,arrays, maps, unionsetc.) tipos.
* Las esquemas Avro se definen usando JSON.

```json
{
    "type" : "record",
    "name" : "User",
    "namespace" : "com.example.models.avro",
    "fields" : [ 
        {"name" : "userID", "type" : "string", "doc" : "User ID of a web app"}, 
        {"name" : "customerName", "type" : "string", "doc" : "Customer Name", "default": "Test User"} 
    ]
}
```

### Documentacion de Schema Registry
- https://medium.com/slalom-blog/introduction-to-schema-registry-in-kafka-915ccf06b902
- https://jskim1991.medium.com/docker-docker-compose-example-for-kafka-zookeeper-and-schema-registry-c516422532e7