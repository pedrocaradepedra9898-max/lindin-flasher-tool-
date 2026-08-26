import sys
import os
import subprocess
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit, 
    QProgressBar, QGroupBox, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPalette, QColor

class FlashWorkerSignals(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

class LindinFlasherTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.device_connected = False

    def initUI(self):
        self.setWindowTitle("Lindin Flasher Tool v1.0 - Real Android Flashing Utility")
        self.setGeometry(100, 100, 750, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QGroupBox {
                color: #cdd6f4;
                font-weight: bold;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475a;
                color: #cdd6f4;
                padding: 5px;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1;
                font-family: Consolas, Monospace;
                border: 1px solid #45475a;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                background-color: #313244;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
            }
        """)

        main_layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Header
        header = QLabel("LINDIN FLASHER TOOL")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #f38ba8; margin-bottom: 10px;")
        main_layout.addWidget(header)

        # Status do Dispositivo
        status_group = QGroupBox("Status da Conexão USB")
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel("Status: Nenhum dispositivo detectado")
        self.lbl_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
        self.btn_check_device = QPushButton("Detectar Dispositivo")
        self.btn_check_device.clicked.connect(self.check_device)
        status_layout.addWidget(self.lbl_status)
        status_layout.addWidget(self.btn_check_device)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)

        # Arquivos de Flash
        flash_group = QGroupBox("Seleção de Arquivos / Partições")
        flash_layout = QVBoxLayout()

        self.partition_select = QComboBox()
        self.partition_select.addItems(["boot", "recovery", "system", "vendor", "userdata"])
        self.partition_select.setStyleSheet("background-color: #313244; color: #cdd6f4; padding: 5px;")
        
        file_layout = QHBoxLayout()
        self.txt_file_path = QLineEdit()
        self.txt_file_path.setPlaceholderText("Selecione o arquivo .img ou .bin...")
        btn_browse = QPushButton("Procurar...")
        btn_browse.clicked.connect(self.browse_file)
        file_layout.addWidget(self.txt_file_path)
        file_layout.addWidget(btn_browse)

        flash_layout.addWidget(QLabel("Selecione a Partição:"))
        flash_layout.addWidget(self.partition_select)
        flash_layout.addWidget(QLabel("Arquivo da ROM/IMG:"))
        flash_layout.addLayout(file_layout)
        flash_group.setLayout(flash_layout)
        main_layout.addWidget(flash_group)

        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Botão de Ação
        self.btn_flash = QPushButton("INICIAR FLASH REAL")
        self.btn_flash.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-size: 14px;")
        self.btn_flash.clicked.connect(self.start_flash)
        main_layout.addWidget(self.btn_flash)

        # Console Log
        log_group = QGroupBox("Console de Comunicação USB / Output")
        log_layout = QVBoxLayout()
        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        log_layout.addWidget(self.txt_console)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        self.log("Lindin Flasher Tool iniciada com sucesso.")
        self.log("Conecte o celular em modo Fastboot/Download para iniciar.")

    def log(self, message):
        self.txt_console.append(f"[{time.strftime('%H:%M:%S')}] {message}")

    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem", "", "Imagens de Firmware (*.img *.bin *.tar)")
        if filename:
            self.txt_file_path.setText(filename)

    def check_device(self):
        self.log("Verificando barramento USB por dispositivos em modo Fastboot...")
        try:
            result = subprocess.run(["fastboot", "devices"], capture_output=True, text=True, shell=True)
            output = result.stdout.strip()
            
            if output:
                device_id = output.split()[0]
                self.lbl_status.setText(f"Status: Conectado ({device_id})")
                self.lbl_status.setStyleSheet("color: #a6e3a1; font-weight: bold;")
                self.log(f"Dispositivo detectado com sucesso! ID: {device_id}")
                self.device_connected = True
            else:
                self.lbl_status.setText("Status: Nenhum dispositivo em Fastboot")
                self.lbl_status.setStyleSheet("color: #f38ba8; font-weight: bold;")
                self.log("Nenhum dispositivo encontrado em modo Fastboot. Verifique o cabo e os drivers.")
                self.device_connected = False
        except Exception as e:
            self.log(f"Erro ao acessar drivers USB/Fastboot: {str(e)}")
            self.device_connected = False

    def start_flash(self):
        file_path = self.txt_file_path.text()
        partition = self.partition_select.currentText()

        if not self.device_connected:
            QMessageBox.critical(self, "Erro", "Nenhum celular conectado em modo Fastboot!")
            return

        if not file_path or not os.path.exists(file_path):
            QMessageBox.critical(self, "Erro", "Selecione um arquivo de imagem (.img) válido!")
            return

        self.btn_flash.setEnabled(False)
        self.progress_bar.setValue(10)
        self.log(f"Iniciando procedimento de gravação na partição [{partition}]...")

        # Inicia thread separada para não travar a GUI durante o processo
        self.signals = FlashWorkerSignals()
        self.signals.log_signal.connect(self.log)
        self.signals.progress_signal.connect(self.progress_bar.setValue)
        self.signals.finished_signal.connect(self.flash_finished)

        threading.Thread(target=self.run_fastboot_flash, args=(partition, file_path)).start()

    def run_fastboot_flash(self, partition, file_path):
        try:
            self.signals.log_signal.emit("Enviando pacote para a memória buffer do aparelho...")
            self.signals.progress_signal.emit(30)
            
            # Comando real de flash executado no hardware via protocolo Fastboot
            cmd = f"fastboot flash {partition} \"{file_path}\""
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.signals.progress_signal.emit(90)
                self.signals.log_signal.emit(stdout)
                self.signals.log_signal.emit("Gravação concluída na memória Flash ROM com sucesso!")
                self.signals.finished_signal.emit(True, "Sucesso")
            else:
                self.signals.log_signal.emit(f"FALHA NO FLASH: {stderr}")
                self.signals.finished_signal.emit(False, stderr)

        except Exception as e:
            self.signals.log_signal.emit(f"Erro crítico no barramento USB: {str(e)}")
            self.signals.finished_signal.emit(False, str(e))

    def flash_finished(self, success, message):
        self.btn_flash.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Sucesso", "Partição gravada com sucesso no dispositivo!")
        else:
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Erro de Flash", f"Falha na gravação:\n{message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LindinFlasherTool()
    window.show()
    sys.exit(app.exec_())