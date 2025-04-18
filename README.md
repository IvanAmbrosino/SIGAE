# SIGAE
Sistema Integral de Gestion de Actividades Espaciales

SIGAE es una plataforma integral diseñada para planificar, gestionar y supervisar actividades espaciales. Su enfoque modular y escalable permite a las agencias espaciales y organizaciones relacionadas coordinar operaciones complejas de manera eficiente, precisa y segura.

## 🌌 Características principales

- **Planificación de Actividades Espaciales:** Herramientas visuales e inteligentes para programar tareas orbitales, mantenimientos, lanzamientos y más.
- **Gestión de Recursos:** Asignación y seguimiento de personal, equipamiento y satélites.
- **Monitoreo en Tiempo Real:** Visualización del estado actual de las misiones y actividades espaciales.
- **Control de Conflictos:** Detección automática de conflictos de agenda, uso de recursos y trayectorias orbitales.
- **Reportes e Historial:** Registro detallado de eventos, cambios y resultados para análisis posteriores.
- **Interfaz amigable:** Acceso web responsivo con dashboards claros e intuitivos.

## ⚙️ Tecnologías utilizadas

- **Frontend:** React.js, Tailwind CSS
- **Backend:** Java (Spring Boot), Node.js (microservicios complementarios)
- **Base de Datos:** PostgreSQL, MariaDB
- **Autenticación:** JWT + OAuth2
- **Visualización orbital:** CesiumJS / D3.js

## 🚀 Público objetivo

- Agencias espaciales nacionales
- Centros de control de satélites
- Empresas aeroespaciales privadas
- Instituciones académicas con programas espaciales

## 📦 Instalación

```bash
# Clona el repositorio
git clone https://github.com/tuusuario/sigae.git
cd sigae

# Inicia los servicios backend
cd backend
./mvnw spring-boot:run

# Inicia el frontend
cd ../frontend
npm install
npm run dev
