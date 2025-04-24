# SIGAE
Sistema de Gestión de Actividades Espaciales

**Objetivo:**  
Optimizar la gestión de actividades espaciales mediante la integración de herramientas de planificación, control de antenas y visualización de información satelital.

**Componentes Clave:**
- Módulo de planificación automatizada (Planner)
- Integración con sistemas existentes (CONAE)
- Interfaz web con dashboards y notificaciones
- API RESTful para interoperabilidad con otros sistemas

**Impacto Esperado:**
- Mejora de la eficiencia en operaciones satelitales
- Disminución de conflictos en el uso compartido de antenas
- Trazabilidad completa en planificación y ejecución de tareas

---

## 📅 Detalle Técnico - Módulo Planner

El **Planner** es un componente esencial del `Ground Station Controller`. Permite:

### Funcionalidades Principales:
- **Definición de tareas planificadas (Scheduled Tasks)** para actividades como:
  - Seguimiento satelital
  - Grabación
  - Transmisión (Tx) / Recepción (Rx)
  - Envío de comandos

### Cada tarea incluye:
- Identificador único y nombre
- Tiempo de inicio y duración
- Frecuencia asignada, polarización, tipo de modulación
- Restricciones de visibilidad (elevación mínima, zona de paso)

### Modos de operación:
- **Planificación regular:** ejecución automatizada según cronograma
- **Modo simulación:** pruebas sin transmisión real, ideal para depuración

### Capacidades adicionales:
- Edición manual o automática (vía interfaz web o API)
- Gestión de conflictos de recursos (ej. antenas ocupadas) según prioridad
- Interfaz web intuitiva para la creación y seguimiento de tareas
- Soporte para importación/exportación de planificaciones en formatos **JSON/XML**

> 🔗 **Nota Importante:**  
> Este módulo sirve como **interfaz clave** entre el sistema de gestión de CONAE y los controladores de estación terrena. El planificador debe poder **leer y escribir tareas** y sincronizar con la infraestructura física.

---

## 🏗️ Arquitectura General del Sistema

### Frontend (Cliente Web)
- **Tecnologías:** React + TailwindCSS o Material UI
- **Funcionalidad:** Interfaz dinámica que consume APIs REST para mostrar:
  - Tareas planificadas
  - Estado de antenas
  - Información satelital
  - Paneles y dashboards

### Backend (API RESTful / Microservicios)
- **Framework:** FastAPI (asíncrono, rápido, con Swagger automático)
- **Módulos separados:**
  - Usuarios
  - Planificación
  - Antenas
  - TLE (Two-Line Element)
  - Notificaciones
  - Tareas
- **Tareas en segundo plano:** Celery + Redis (notificaciones, descarga de TLE, sincronización)

### Base de Datos
- **PostgreSQL:** Integridad referencial, manejo de JSON, timestamps, etc.
- **Mariadb Galera Cluster:** Alta disponibilidad (HA), replicación de datos
- **GlusterFS / Ceph:** Almacenamiento distribuido de alta disponibilidad

### Servicio de Tareas Periódicas
- Creación de servicios que consultan APIs externas o realizan cargas regulares de datos hacia las antenas.

### Comunicación y Mensajería
- **MailSender:** Envío de notificaciones y planificación a diferentes áreas operativas

### Autenticación
- **OAuth2 con JWT** o integración con Active Directory (SSO)
- Roles y permisos gestionados por tipo de usuario

---

## ⚙️ Infraestructura

- **Docker + Docker Compose:** Para entornos de desarrollo locales
- **Kubernetes o Docker Swarm:** Para entornos de producción
- **GitHub + Portainer:** Despliegue continuo y gestión visual de contenedores
- **Proxy:** Balanceo de carga y ruteo dinámico de microservicios
- **Entorno de nodos HA:** Proxmox + Ceph o GlusterFS

---

## 🧪 Frameworks y Tecnologías

| Tipo             | Tecnología      | Justificación                               |
|------------------|------------------|---------------------------------------------|
| Backend API      | FastAPI          | Asíncrono, rápido, Swagger automático       |
| Frontend         | React            | UI moderna y dinámica                       |
| Autenticación    | OAuth2 / JWT     | Estándar de seguridad                       |
| Base de Datos    | Mariadb Cluster  | Alta disponibilidad                         |
| Base de Datos    | PostgreSQL       | Potente para relaciones complejas           |
| Infraestructura  | Docker           | Despliegue replicable y portable            |
| Backend Tareas   | Redis / Kafka    | Broker de mensajes en tiempo real           |

---

## 📋 Metodologías de Trabajo

- **Scrum:** Organización ágil de sprints
- **CI/CD:** Automatización de pruebas y despliegue
- **Git / GitHub:** Control de versiones y ramas
- **Testing:** TDD con PyTest y React Testing Library
- **Documentación:** Swagger/OpenAPI + Storybook
- **Colaboración:** Google Drive para documentos y plantillas

---

Desarrollado por el equipo SIGAE 🌍  
Para más información, contactá con el equipo técnico o revisá la documentación en la carpeta `/docs`.
