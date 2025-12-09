# Despertador - Aplicación de Servicio Windows

Una aplicación desktop para Windows 10 que emite avisos cada 30 minutos. Se ejecuta como servicio en segundo plano y cuenta con una interfaz gráfica opcional para administración y visualización de logs.

## Características

- ✅ Se ejecuta como servicio de Windows (inicia automáticamente)
- ✅ Emite avisos cada 30 minutos con notificaciones de Windows
- ✅ Interfaz gráfica para administración (se abre a demanda)
- ✅ Visualización de logs en tiempo real
- ✅ Sin dependencia de Python en la máquina del usuario
- ✅ Fácil instalación y desinstalación

## Requisitos previos (solo para desarrollo)

- Python 3.8 o superior
- Windows 10 o superior
- Visual Studio Code (opcional pero recomendado)

## Instalación para desarrollo

### 1. Clonar o descargar el proyecto

```bash
cd tu-carpeta-de-proyectos
git clone <url-del-repositorio>
cd despertador
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

En Windows (PowerShell o CMD):
```bash
venv\Scripts\activate
```

Deberías ver `(venv)` al inicio de la línea de la terminal.

### 4. Instalar dependencias

```bash
pip install pyinstaller PyQt5 windows-toasts
```

Para verificar que se instalaron correctamente:
```bash
pip list
```

## Desarrollo y pruebas

### Ejecutar la aplicación en modo desarrollo

En la terminal (con el entorno virtual activado):

```bash
python despertador.py
```

Esto abre la interfaz gráfica para ver el estado y logs.

### Probar el servicio localmente

Para simular que se ejecuta como servicio sin registrarlo realmente:

```bash
python despertador.py --service
```

Este comando inicia el loop del servicio en la terminal (emitirá un aviso cada 30 minutos).

## Compilación a ejecutable

### Crear el .exe

Con el entorno virtual activado, ejecuta:

```bash
pyinstaller --onefile --windowed despertador.py
```

Esto genera:
- **Archivo ejecutable**: `dist/despertador.exe`
- **Carpeta temporal**: `build/` (se puede eliminar)
- **Archivo de configuración**: `despertador.spec` (se puede eliminar)

El ejecutable es **autónomo y no requiere Python instalado**.

### Ubicación del ejecutable compilado

```
tu-proyecto/
├── dist/
│   └── despertador.exe  ← Este es el archivo que usaremos
├── venv/
├── despertador.py
└── README.md
```

## Instalación como servicio Windows

### Requisitos

- Descargar **NSSM** (Non-Sucking Service Manager) desde: https://nssm.cc/download
- Descomprimir el archivo descargado
- Abrir una terminal **como administrador**

### Pasos de instalación

**1. Navega a la carpeta de NSSM en la terminal (como administrador):**

```bash
cd C:\ruta\a\nssm-x.x\win64
```

**2. Registra el servicio:**

```bash
nssm install despertador "C:\ruta\completa\a\dist\despertador.exe" --service
```

Reemplaza `C:\ruta\completa\a\dist\despertador.exe` con la ruta real del ejecutable.

**3. Inicia el servicio:**

```bash
nssm start despertador
```

**4. Verifica que está corriendo:**

```bash
nssm status despertador
```

Deberías ver: `SERVICE_RUNNING`

### Verificación en Servicios de Windows

Puedes verificar que el servicio está registrado:

1. Presiona `Win + R`
2. Escribe `services.msc` y Enter
3. Busca "despertador" en la lista
4. Deberías ver su estado como "Ejecutándose"

## Ubicación de datos

Todos los datos de la aplicación se guardan en:

```
C:\Users\[Tu Usuario]\AppData\Roaming\despertador\
```

Dentro de esta carpeta encontrarás:

- **app.log** - Archivo de log con todos los eventos y avisos
- **status.json** - Archivo JSON con el estado actual del servicio

Ejemplo de contenido de `status.json`:
```json
{
  "corriendo": true,
  "ultimo_aviso": "14:30:45",
  "contador_avisos": 24,
  "ultima_actualizacion": "2025-12-08T14:30:45.123456"
}
```

## Usar la interfaz gráfica

### Abrir la interfaz

Simplemente ejecuta el archivo `despertador.exe` (sin parámetros):

```bash
despertador.exe
```

O haz doble clic en él desde el Explorador de Windows.

### Funcionalidades de la interfaz

- **Estado** - Muestra si el servicio está corriendo
- **Contador de avisos** - Número total de avisos emitidos
- **Último aviso** - Hora del último aviso registrado
- **Logs** - Visualización de las últimas 30 líneas del archivo de log
- **Botón Actualizar** - Recarga los datos y logs manualmente
- **Botón Limpiar Logs** - Elimina el contenido del archivo de log
- **Botón Salir** - Cierra la interfaz (el servicio sigue corriendo)

Los datos se actualizan automáticamente cada 5 segundos.

## Desinstalación del servicio

Si necesitas eliminar el servicio:

**1. Abre terminal como administrador**

**2. Navega a la carpeta de NSSM:**

```bash
cd C:\ruta\a\nssm-x.x\win64
```

**3. Detén el servicio:**

```bash
nssm stop despertador
```

**4. Elimina el servicio:**

```bash
nssm remove despertador confirm
```

**5. Verifica que fue eliminado:**

```bash
nssm status despertador
```

Debería mostrar un error indicando que el servicio no existe.

## Archivos del proyecto

```
despertador/
├── despertador.py          # Código fuente principal
├── venv/                   # Entorno virtual (no incluir en distribución)
├── dist/
│   └── despertador.exe     # Ejecutable compilado
├── build/                  # Carpeta temporal (puede eliminarse)
├── despertador.spec        # Archivo de configuración de PyInstaller (puede eliminarse)
└── README.md               # Este archivo
```

## Configuración avanzada

### Cambiar el intervalo de avisos

Abre `despertador.py` y busca esta línea:

```python
time.sleep(1800)  # 1800 segundos = 30 minutos
```

Cambia `1800` al número de segundos que desees. Ejemplos:

- 30 segundos: `time.sleep(30)`
- 1 minuto: `time.sleep(60)`
- 5 minutos: `time.sleep(300)`
- 15 minutos: `time.sleep(900)`
- 1 hora: `time.sleep(3600)`

### Personalizar el aviso

En el método `emitir_aviso()` puedes cambiar el mensaje de la notificación:

```python
def emitir_aviso(self):
    ...
    notificador = WindowsToasts()
    notificador.show_toast(
        title="🔔 Despertador",  # ← Cambiar este título
        body=f"Aviso #{self.contador_avisos} - {self.ultimo_aviso}",  # ← Cambiar este mensaje
        duration="long"
    )
```

**Opciones de duración:**
- `"long"` → Notificación visible unos 7-8 segundos
- `"short"` → Notificación visible unos 3-4 segundos

## Solución de problemas

### El servicio no inicia

1. Verifica que la ruta al .exe en NSSM es correcta:
   ```bash
   nssm get despertador Application
   ```

2. Revisa los logs en `AppData\Roaming\despertador\app.log`

3. Intenta ejecutar el .exe directamente para ver si hay errores

### No puedo abrir la interfaz gráfica

Asegúrate de que:
- Estás ejecutando el archivo correcto (`despertador.exe`)
- El archivo no está corrompido (intenta recompilar)
- Tienes permisos en la carpeta de datos

### Los logs no se actualizan

1. Verifica que la carpeta `AppData\Roaming\despertador\` existe
2. Verifica permisos de escritura en esa carpeta
3. Reinicia el servicio:
   ```bash
   nssm restart despertador
   ```

## Información técnica

### Stack tecnológico

- **Lenguaje**: Python 3.8+
- **Interfaz gráfica**: PyQt5 (Open Source)
- **Compilador**: PyInstaller
- **Gestor de servicios**: NSSM (Non-Sucking Service Manager)
- **Notificaciones**: windows-toasts
- **Sistema operativo**: Windows 10+

### Arquitectura

La aplicación funciona en dos modos:

1. **Modo servicio** (`python despertador.py --service`)
   - Se ejecuta como servicio de Windows
   - Sin interfaz gráfica
   - Emite avisos automáticamente
   - Escribe logs en disco

2. **Modo interfaz** (`python despertador.py`)
   - Abre la ventana de administración
   - Lee los datos del servicio en ejecución
   - Permite visualizar logs y estado
   - No interfiere con el servicio

### Comunicación entre modos

El servicio y la interfaz se comunican a través de archivos JSON:

- **status.json**: El servicio escribe aquí su estado actual
- **app.log**: Ambos modos leen/escriben en este archivo

## Notas

- Iniciar el servicio a partir del archivo .exe:
```bash
python despertador.py --service
```
- Iniciar la interfaz gráfica:
```bash
python despertador.py
```

- Detener el servicio:
```bash
taskkill /F /IM despertador.exe
```
/F: Fuerza el cierre.
/IM: Indica que vas a usar el "Image Name" (nombre del archivo).

- Verificar el estado del servicio:
```bash
tasklist | findstr "despertador"
```
Si no sale nada, es que está detenido. Si aparece una línea con números, es que sigue activo.

## Contribuciones y mejoras

Para sugerir mejoras o reportar bugs, contacta al desarrollador.

## Licencia

[Especificar la licencia si aplica]

---

**Última actualización**: Diciembre 2025