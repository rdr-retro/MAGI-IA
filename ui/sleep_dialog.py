"""
Diálogo de Modo Sueño con Selector de Tiempo - Premium Edition
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QSlider, QProgressBar, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont


class SleepDialog(QDialog):
    """Diálogo para configurar y ejecutar el modo sueño"""
    
    sleep_started = Signal(int)  # Emite la duración en segundos
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💤 Sleep Mode Sync")
        self.setModal(True)
        self.setFixedSize(450, 400)
        
        # Tiempos disponibles (en segundos)
        self.time_options = [
            (60, "1 min"),
            (300, "5 min"),
            (600, "10 min"),
            (1800, "30 min"),
            (3600, "1 hour"),
            (7200, "2 hours")
        ]
        
        self.selected_duration = 60
        self.remaining_seconds = 0
        self.is_sleeping = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)
        
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(35, 35, 35, 35)
        
        # Título
        title = QLabel("🧠 Neural Consolidation")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)
        
        # Descripción
        desc = QLabel("Optimize brain capacity by pruning weak connections and reinforcing high-value patterns.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        layout.addWidget(desc)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #2d3748; max-height: 1px; border: none;")
        layout.addWidget(line)
        
        # Selector de tiempo
        time_label = QLabel("SYNC DURATION")
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setStyleSheet("color: #6366f1; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        layout.addWidget(time_label)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.time_options) - 1)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.slider)
        
        # Label del tiempo seleccionado
        self.time_display = QLabel("1 min")
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.setStyleSheet("color: #e2e8f0; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.time_display)
        
        # Barra de progreso (oculta inicialmente)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Contador regresivo (oculto inicialmente)
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #10a37f; font-size: 18px; font-weight: bold;")
        self.countdown_label.setVisible(False)
        layout.addWidget(self.countdown_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.btn_start = QPushButton("💤 Enter Sleep Mode")
        self.btn_start.setFixedHeight(45)
        self.btn_start.clicked.connect(self.start_sleep)
        buttons_layout.addWidget(self.btn_start)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(45)
        self.btn_cancel.setObjectName("CancelBtn")
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def apply_styles(self):
        """Aplica estilos al diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #161923;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #818cf8, stop:1 #a78bfa);
            }
            QPushButton#CancelBtn {
                background-color: #2d3748;
                background-image: none;
            }
            QPushButton#CancelBtn:hover {
                background-color: #4a5568;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #2d3748;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6366f1;
                border: 2px solid #818cf8;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QProgressBar {
                border: none;
                border-radius: 6px;
                text-align: center;
                background-color: #2d3748;
                color: white;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399);
                border-radius: 6px;
            }
        """)
    
    def on_slider_changed(self, value):
        """Actualiza el display cuando cambia el slider"""
        self.selected_duration, label = self.time_options[value]
        self.time_display.setText(label)
    
    def start_sleep(self):
        """Inicia el modo sueño"""
        if self.is_sleeping:
            return
        
        self.is_sleeping = True
        self.remaining_seconds = self.selected_duration
        
        self.slider.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_cancel.setVisible(False)
        
        self.time_display.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(self.selected_duration)
        self.progress_bar.setValue(0)
        
        self.countdown_label.setVisible(True)
        self.sleep_started.emit(self.selected_duration)
        self.timer.start(1000)
    
    def update_countdown(self):
        """Actualiza el contador regresivo"""
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            elapsed = self.selected_duration - self.remaining_seconds
            self.progress_bar.setValue(elapsed)
            
            minutes = self.remaining_seconds // 60
            seconds = self.remaining_seconds % 60
            self.countdown_label.setText(f"TIME REMAINING: {minutes:02d}:{seconds:02d}")
            
            progress_pct = (elapsed / self.selected_duration) * 100
            self.progress_bar.setFormat(f"Syncing... {progress_pct:.0f}%")
        else:
            self.timer.stop()
            self.countdown_label.setText("✨ CONSOLIDATION COMPLETE")
            self.progress_bar.setFormat("Memory Optimized")
            QTimer.singleShot(2000, self.accept)
