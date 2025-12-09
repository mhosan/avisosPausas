import sys
import os
import json
import time
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from windows_toasts import WindowsToaster, Toast

# Configuración
APP_DATA_DIR = Path(os.getenv('APPDATA')) / 'despertador'
LOG_FILE = APP_DATA_DIR / 'app.log'
STATUS_FILE = APP_DATA_DIR / 'status.json'
CONFIG_FILE = APP_DATA_DIR / 'config.json'

# Crear directorio si no existe
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

class ServicioApp:
    def __init__(self):
        self.corriendo = True
        self.ultimo_aviso = None
        self.contador_avisos = 0
        # Inicializar estado en archivo
        self.guardar_estado()
        
    def registrar_log(self, mensaje):
        """Escribe en el archivo de log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] {mensaje}\n"
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(linea)
        
        # Guardar estado actual
        self.guardar_estado()
    
    def guardar_estado(self):
        """Guarda estado actual en JSON para que la GUI lo pueda leer"""
        # Verificar si hay señal de detención externa antes de escribir
        try:
            if STATUS_FILE.exists():
                with open(STATUS_FILE, 'r') as f:
                    estado_disco = json.load(f)
                    # Si en disco dice False, adoptamos ese estado
                    if not estado_disco.get('corriendo', True):
                        self.corriendo = False
        except Exception:
            pass

        estado = {
            'corriendo': self.corriendo,
            'ultimo_aviso': self.ultimo_aviso,
            'contador_avisos': self.contador_avisos,
            'ultima_actualizacion': datetime.now().isoformat()
        }
        with open(STATUS_FILE, 'w') as f:
            json.dump(estado, f)
    
    def emitir_aviso(self):
        """Emite un aviso con notificación de Windows"""
        self.contador_avisos += 1
        self.ultimo_aviso = datetime.now().strftime("%H:%M:%S")
        self.registrar_log(f"Aviso #{self.contador_avisos} emitido")
        
        # Notificación de Windows
        try:
            notificador = WindowsToaster(applicationText="Despertador")
            new_toast = Toast()
            new_toast.text_fields = [f"🔔 Aviso #{self.contador_avisos}", f"Hora: {self.ultimo_aviso}"]
            notificador.show_toast(new_toast)
            self.registrar_log(f"Notificación enviada para Aviso #{self.contador_avisos}")
        except Exception as e:
            self.registrar_log(f"Error al enviar notificación: {str(e)}")
        
        print(f"[AVISO] #{self.contador_avisos} - {self.ultimo_aviso}")
    
    def ejecutar_servicio(self):
        """Loop principal del servicio"""
        self.registrar_log("=== SERVICIO INICIADO ===")
        
        while self.corriendo:
            try:
                # Leer configuración
                config = leer_config()
                intervalo = config.get('intervalo', 30)
                
                # Emitir aviso según configuración
                time.sleep(intervalo)
                self.emitir_aviso()
                
                # Verificar si se solicitó detención desde GUI
                estado = leer_estado()
                if estado and not estado.get('corriendo', True):
                    self.registrar_log("Detención solicitada desde GUI")
                    self.corriendo = False
                    
            except Exception as e:
                self.registrar_log(f"ERROR en loop: {str(e)}")
                time.sleep(5)


def leer_logs(ultimas_lineas=30):
    """Lee las últimas N líneas del archivo de log"""
    if not LOG_FILE.exists():
        return "No hay logs aún"
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        return ''.join(lineas[-ultimas_lineas:])
    except:
        return "Error al leer logs"

def leer_config():
    """Lee la configuración desde el archivo JSON"""
    if not CONFIG_FILE.exists():
        return {'intervalo': 30}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'intervalo': 30}

def guardar_config_file(intervalo):
    """Guarda la configuración en el archivo JSON"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'intervalo': intervalo}, f)
        return True
    except:
        return False

def leer_estado():
    """Lee el estado actual desde el archivo JSON"""
    if not STATUS_FILE.exists():
        return None
    
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

class VentanaDespertador(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_ui()
        
        # Timer para actualizar cada 5 segundos
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_datos)
        self.timer.start(5000)
        
        # Actualizar inmediatamente
        self.actualizar_datos()
        
        # Cargar configuración inicial
        self.cargar_configuracion()
    
    def init_ui(self):
        """Inicializa la interfaz gráfica"""
        self.setWindowTitle('Control Despertador')
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QTextEdit {
                background-color: #000000;
                color: #00ff00;
                border: 1px solid #333333;
                font-family: Courier;
                font-size: 8pt;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Título
        titulo = QLabel('Estado del Servicio')
        titulo_font = QFont('Arial', 16, QFont.Bold)
        titulo.setFont(titulo_font)
        main_layout.addWidget(titulo)
        
        # Panel de estado
        estado_layout = QHBoxLayout()
        
        # Estado
        label_estado_titulo = QLabel('Estado:')
        label_estado_titulo.setFont(QFont('Arial', 10, QFont.Bold))
        self.label_estado = QLabel('Ejecutándose')
        self.label_estado.setFont(QFont('Arial', 10))
        self.label_estado.setStyleSheet("color: #00ff00;")
        estado_layout.addWidget(label_estado_titulo)
        estado_layout.addWidget(self.label_estado)
        
        # Espaciador
        estado_layout.addSpacing(40)
        
        # Contador
        label_contador_titulo = QLabel('Últimos avisos:')
        label_contador_titulo.setFont(QFont('Arial', 10, QFont.Bold))
        self.label_contador = QLabel('0')
        self.label_contador.setFont(QFont('Arial', 10))
        estado_layout.addWidget(label_contador_titulo)
        estado_layout.addWidget(self.label_contador)
        
        # Espaciador
        estado_layout.addSpacing(40)
        
        # Último aviso
        label_ultimo_titulo = QLabel('Último aviso:')
        label_ultimo_titulo.setFont(QFont('Arial', 10, QFont.Bold))
        self.label_ultimo = QLabel('---')
        self.label_ultimo.setFont(QFont('Arial', 10))
        estado_layout.addWidget(label_ultimo_titulo)
        estado_layout.addWidget(self.label_ultimo)
        
        estado_layout.addStretch()
        main_layout.addLayout(estado_layout)
        
        # Separador
        separador = QLabel('─' * 100)
        separador.setStyleSheet("color: #333333;")
        main_layout.addWidget(separador)

        # Configuración
        config_layout = QHBoxLayout()
        
        label_config = QLabel('Intervalo (segundos):')
        label_config.setFont(QFont('Arial', 10))
        label_config.setStyleSheet("color: #ffffff;") 
        config_layout.addWidget(label_config)
        
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(5, 86400) # 5s to 24h
        self.spin_intervalo.setValue(30)
        self.spin_intervalo.setStyleSheet("""
            QSpinBox {
                background-color: #333333;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #555555;
            }
        """)
        config_layout.addWidget(self.spin_intervalo)
        
        btn_guardar_config = QPushButton('Guardar Intervalo')
        btn_guardar_config.clicked.connect(self.guardar_configuracion)
        config_layout.addWidget(btn_guardar_config)
        
        config_layout.addStretch()
        main_layout.addLayout(config_layout)
        
        # Separador 2
        separador2 = QLabel('─' * 100)
        separador2.setStyleSheet("color: #333333;")
        main_layout.addWidget(separador2)
        
        # Título logs
        titulo_logs = QLabel('Logs (últimas 30 líneas)')
        titulo_logs.setFont(QFont('Arial', 10, QFont.Bold))
        main_layout.addWidget(titulo_logs)
        
        # Area de logs
        self.text_logs = QTextEdit()
        self.text_logs.setReadOnly(True)
        self.text_logs.setFont(QFont('Courier', 8))
        main_layout.addWidget(self.text_logs)
        
        # Botones
        botones_layout = QHBoxLayout()
        
        btn_actualizar = QPushButton('Actualizar')
        btn_actualizar.clicked.connect(self.actualizar_datos)
        botones_layout.addWidget(btn_actualizar)
        
        btn_limpiar = QPushButton('Limpiar Logs')
        btn_limpiar.clicked.connect(self.limpiar_logs)
        botones_layout.addWidget(btn_limpiar)
        
        self.btn_iniciar = QPushButton('Iniciar Servicio')
        self.btn_iniciar.setStyleSheet("background-color: #107c10;") # Verde
        self.btn_iniciar.clicked.connect(self.iniciar_servicio)
        botones_layout.addWidget(self.btn_iniciar)
        
        self.btn_detener = QPushButton('Detener Servicio')
        self.btn_detener.setStyleSheet("background-color: #d13438;") # Rojo
        self.btn_detener.clicked.connect(self.detener_servicio)
        botones_layout.addWidget(self.btn_detener)
        
        btn_salir = QPushButton('Salir GUI')
        btn_salir.clicked.connect(self.close)
        botones_layout.addWidget(btn_salir)
        
        botones_layout.addStretch()
        main_layout.addLayout(botones_layout)
    
    def actualizar_datos(self):
        """Actualiza los datos mostrados en la ventana"""
        estado = leer_estado()
        if estado:
            esta_corriendo = estado.get('corriendo', False)
            self.label_contador.setText(str(estado['contador_avisos']))
            self.label_ultimo.setText(estado['ultimo_aviso'] or '---')
            
            if esta_corriendo:
                self.label_estado.setText('Ejecutándose')
                self.label_estado.setStyleSheet("color: #00ff00;")
                self.btn_iniciar.setEnabled(False)
                self.btn_detener.setEnabled(True)
                self.btn_iniciar.setStyleSheet("background-color: #333333; color: #888888;")
                self.btn_detener.setStyleSheet("background-color: #d13438;")
            else:
                self.label_estado.setText('Detenido')
                self.label_estado.setStyleSheet("color: #ff0000;")
                self.btn_iniciar.setEnabled(True)
                self.btn_detener.setEnabled(False)
                self.btn_iniciar.setStyleSheet("background-color: #107c10;")
                self.btn_detener.setStyleSheet("background-color: #333333; color: #888888;")
        
        # Actualizar logs
        logs = leer_logs(30)
        self.text_logs.setText(logs)
        
        # Auto-scroll al final
        self.text_logs.verticalScrollBar().setValue(
            self.text_logs.verticalScrollBar().maximum()
        )
    
    def limpiar_logs(self):
        """Limpia el archivo de logs"""
        reply = QMessageBox.question(
            self,
            'Confirmar',
            '¿Está seguro de que desea limpiar el archivo de logs?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                open(LOG_FILE, 'w').close()
                self.text_logs.setText('')
                QMessageBox.information(self, 'Éxito', 'Logs limpios correctamente')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error al limpiar logs: {str(e)}')

    def cargar_configuracion(self):
        """Carga la configuración en la interfaz"""
        config = leer_config()
        if config and 'intervalo' in config:
            self.spin_intervalo.setValue(config['intervalo'])

    def guardar_configuracion(self):
        """Guarda la configuración desde la interfaz"""
        intervalo = self.spin_intervalo.value()
        if guardar_config_file(intervalo):
            QMessageBox.information(self, 'Éxito', f'Intervalo actualizado a {intervalo} segundos.\nEl servicio usará este valor en el próximo ciclo.')
            # Nota: No podemos usar self.app.registrar_log aquí directamente si app es solo una instancia separada,
            # pero dado que el paso Main pasa una instancia de ServicioApp, podemos usarla si comparten FS, lo cual hacen.
            self.app.registrar_log(f"Configuración actualizada desde GUI: Intervalo = {intervalo}s")
        else:
            QMessageBox.critical(self, 'Error', 'No se pudo guardar la configuración')

    def detener_servicio(self):
        """Envía señal para detener el servicio"""
        reply = QMessageBox.question(
            self,
            'Confirmar',
            '¿Está seguro de que desea detener el servicio en segundo plano?\nEsto hará que dejen de llegar los avisos.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            estado = leer_estado()
            if estado:
                estado['corriendo'] = False
                try:
                    with open(STATUS_FILE, 'w') as f:
                        json.dump(estado, f)
                    QMessageBox.information(self, 'Éxito', 'Se ha enviado la señal de detención.\nEl servicio se detendrá en el próximo ciclo.')
                    self.label_estado.setText('Deteniéndose...')
                    self.label_estado.setStyleSheet("color: #ffa500;")
                except Exception as e:
                    QMessageBox.critical(self, 'Error', f'No se pudo actualizar el estado: {str(e)}')
            else:
                 QMessageBox.critical(self, 'Error', 'No se pudo leer el estado actual')

    def iniciar_servicio(self):
        """Inicia el servicio en un subproceso"""
        try:
            # Primero reseteamos el estado en disco para evitar que se auto-detenga
            estado = leer_estado() or {}
            estado['corriendo'] = True
            with open(STATUS_FILE, 'w') as f:
                json.dump(estado, f)
            
            # Lanzar proceso
            subprocess.Popen([sys.executable, sys.argv[0], '--service'], 
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            
            QMessageBox.information(self, 'Éxito', 'Servicio iniciado correctamente')
            
            # Actualizar UI inmediatamente
            self.actualizar_datos()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'No se pudo iniciar el servicio: {str(e)}')

def main():
    if len(sys.argv) > 1:
        # Modo servicio (ejecutado por NSSM)
        if sys.argv[1] == '--service':
            app = ServicioApp()
            app.ejecutar_servicio()
    else:
        # Modo GUI (ejecutado por el usuario)
        app_qt = QApplication(sys.argv)
        app = ServicioApp()
        ventana = VentanaDespertador(app)
        ventana.show()
        sys.exit(app_qt.exec_())

if __name__ == '__main__':
    main()