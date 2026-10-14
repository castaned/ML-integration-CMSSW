# Primer acceso y activación de la cuenta

Esta etapa se realiza **una sola vez**, antes de preparar el repositorio o el entorno de análisis. Completarla preferentemente antes de la sesión del taller.

## Primera conexión: SSH y activación de doble verificación

**El primer ingreso debe hacerse por terminal**, antes de utilizar Open OnDemand. Este acceso permite crear el directorio personal y activar la verificación en dos pasos (2FA), siguiendo las instrucciones del clúster.

Necesitas el usuario y la contraseña proporcionados por ACARUS, además de la aplicación **Google Authenticator** instalada en tu teléfono.

### Windows: conexión con PuTTY

1. Abrir PuTTY.
2. En **Host Name (or IP address)** escribir `yuca.unison.mx` o `148.225.111.153`.
3. Seleccionar **SSH**, puerto **22**, y pulsar **Open**.
4. Introducir el nombre de usuario y la contraseña cuando se soliciten. Al escribir la contraseña no se muestran caracteres; es normal.

### Linux o macOS: conexión desde la terminal

Sustituir `TU_USUARIO` por el usuario asignado:

```bash
ssh TU_USUARIO@yuca.unison.mx
```

También se puede utilizar la dirección IP:

```bash
ssh TU_USUARIO@148.225.111.153
```

### Activar 2FA con Google Authenticator

1. En el primer acceso aparecerán un código QR y un enlace de configuración.
2. Abrir **Google Authenticator** en el teléfono y añadir una cuenta escaneando el QR, según las instrucciones mostradas por Yuca. Si no puedes escanearlo, seguir la alternativa de configuración indicada por el sistema.
3. Completar las preguntas o verificaciones que solicite el clúster. No cerrar la sesión hasta terminar la activación.
4. En los accesos posteriores, introducir el código temporal de la aplicación y la contraseña en el orden que solicite el sistema.

!!! warning "Credenciales personales"
    No compartir usuario, contraseña, código QR, enlace de configuración ni códigos de verificación. Si sospechas un acceso no autorizado, notificar inmediatamente al soporte técnico de ACARUS.

## Acceso posterior por Open OnDemand

**Después de completar el primer acceso SSH y la activación de 2FA**, abrir [Open OnDemand de Yuca](http://yucaood.acarus.unison.mx).

Iniciar sesión con el usuario, código de verificación y contraseña cuando se soliciten. Desde el portal se pueden utilizar las herramientas habilitadas por ACARUS, como el explorador de archivos y las sesiones de terminal. Abrir una terminal de Yuca para continuar con los pasos del curso.

Si la primera conexión o la activación de 2FA falla, solicitar ayuda al soporte de ACARUS antes de continuar. No intentar resolverlo compartiendo credenciales con otros participantes.


## Al terminar

La cuenta queda lista para iniciar sesiones por SSH o Open OnDemand. En esta etapa no se clona el repositorio ni se instalan bibliotecas. Continuar después con [Repositorio y entorno de trabajo](01_entorno.md).
