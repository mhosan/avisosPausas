import sys
import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from windows_toasts import WindowsToaster, Toast

# Configuración
APP_DATA_DIR = Path(os.getenv('APPDATA')) / 'despertador'
LOG_FILE = APP_DATA_DIR / 'app.log'
STATUS_FILE = APP_DATA_DIR / 'status.json'

# Crear directorio si no existe
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

class ServicioApp:
    def __init__(self):
        self.corriendo = True
        self.ultimo_aviso = None
        self.contador_avisos = 0
        
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
                # Emitir aviso cada 30 minutos (1800 segundos)
                # Para pruebas, usa 30 segundos: time.sleep(30)
                time.sleep(30)
                self.emitir_aviso()
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
        
        btn_salir = QPushButton('Salir')
        btn_salir.clicked.connect(self.close)
        botones_layout.addWidget(btn_salir)
        
        botones_layout.addStretch()
        main_layout.addLayout(botones_layout)
    
    def actualizar_datos(self):
        """Actualiza los datos mostrados en la ventana"""
        estado = leer_estado()
        if estado:
            self.label_contador.setText(str(estado['contador_avisos']))
            self.label_ultimo.setText(estado['ultimo_aviso'] or '---')
        
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