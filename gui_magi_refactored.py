"""
Sistema MAGI - Interfaz Principal Refactorizada
Versión optimizada y modular
"""
import sys
import os
import threading

# Fix for module loading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QFileDialog, QFrame, QProgressBar, QScrollArea,
                             QCheckBox)
from PySide6.QtCore import Qt, Slot, QSize, QMetaObject, Q_ARG, QTimer
from PySide6.QtGui import QFont, QPixmap, QMovie
import numpy as np

# Importar módulos locales
from core.signals import IAWorkerSignals
from ui.widgets import MessageWidget, ThinkingWidget
from ui.sleep_dialog import SleepDialog
from ui import styles
from chat_interactivo import RedCrecimientoInfinito

# Importar el gestor de cerebros (lo crearemos después)
from core.brain_manager import BrainManager


class MAGISystem(QMainWindow):
    """Ventana principal del sistema MAGI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MAGI SYSTEM (Supercomputer)")
        self.resize(1200, 900)
        
        # Inicializar gestor de cerebros
        self.brain_manager = BrainManager()
        
        # Señales
        self.signals = IAWorkerSignals()
        self.thinking_widget = None
        
        # Estado
        self.escuchando = False
        self.buffer_voz = ""
        self.ultima_respuesta_magi = ""
        self.debate_turn = 0 # 0=Melchor, 1=Gaspar, 2=Casper
        
        # Crear interfaz
        self.init_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Configurar callbacks de expansión
        self.brain_manager.set_expansion_callbacks(
            melchor=lambda n: self.signals.cerebro_expandido.emit("Melchor", n),
            gaspar=lambda n: self.signals.cerebro_expandido.emit("Gaspar", n),
            casper=lambda n: self.signals.cerebro_expandido.emit("Casper", n)
        )
        
        self.actualizar_info_archivo()
    
    def connect_signals(self):
        """Conecta todas las señales"""
        self.signals.respuesta_lista.connect(self.agregar_mensaje)
        self.signals.stats_actualizadas.connect(self.actualizar_labels)
        self.signals.entrenamiento_terminado.connect(
            lambda: self.agregar_mensaje("SISTEMA", "Sincronización finalizada.")
        )
        self.signals.cerebro_expandido.connect(
            # Corregido: Las estadísticas ahora tienen su propio perfil con estrella
            lambda name, n: self.agregar_mensaje("ESTADÍSTICAS", f"{name} ha crecido a {n} neuronas.")
        )
        self.signals.progreso_entrenamiento.connect(self.barra_progreso.setValue)
        self.signals.texto_transcrito.connect(self.cargar_texto_transcrito)
        self.signals.pensando.connect(self.toggle_thinking_animation)
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Aplicar estilo global
        self.setStyleSheet(styles.GLOBAL_STYLE)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crear sidebar y área de chat
        self.sidebar = self.create_sidebar()
        chat_area = self.create_chat_area()
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(chat_area)
    
    def create_sidebar(self):
        """Crea el panel lateral"""
        side_panel = QFrame()
        side_panel.setObjectName("SidePanel")
        side_panel.setFixedWidth(240)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(10, 15, 10, 10)
        side_layout.setSpacing(8)
        
        # Logo
        self.add_logo(side_layout)
        
        # Animación ADN
        self.add_adn_animation(side_layout)
        
        # Sección de entrenamiento
        self.add_training_section(side_layout)
        
        # Separador
        self.add_separator(side_layout)
        
        # Estado de cerebros
        self.add_brain_status_section(side_layout)
        
        # Votante anónimo
        self.add_anonimo_section(side_layout)
        
        # Modo Debate
        self.add_debate_section(side_layout)
        
        # Barra de progreso
        self.barra_progreso = QProgressBar()
        side_layout.addWidget(self.barra_progreso)
        
        side_layout.addStretch()
        
        # Info de usuario
        user_info = QPushButton("Raul Diaz")
        user_info.setObjectName("SecondaryBtn")
        user_info.setStyleSheet("border-top: 1px solid #3e3f4b; border-radius: 0; padding-top: 12px;")
        side_layout.addWidget(user_info)
        
        return side_panel
    
    def add_logo(self, layout):
        """Agrega el logo al layout"""
        logo_label = QLabel()
        base_path = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_path, "IA.png")
        logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(180, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
    
    def add_adn_animation(self, layout):
        """Agrega la animación de ADN"""
        self.adn_label = QLabel()
        base_path = os.path.dirname(os.path.abspath(__file__))
        adn_path = os.path.join(base_path, "adn.gif")
        self.adn_movie = QMovie(adn_path)
        if self.adn_movie.isValid():
            self.adn_label.setMovie(self.adn_movie)
            self.adn_label.setAlignment(Qt.AlignCenter)
            self.adn_label.setMaximumHeight(150)
            self.adn_movie.setScaledSize(QSize(180, 150))
            layout.addWidget(self.adn_label)
            self.adn_movie.start()
    
    def add_training_section(self, layout):
        """Agrega la sección de entrenamiento"""
        # Título
        training_label = QLabel("BULK TRAINING")
        training_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px; padding: 3px 0; letter-spacing: 1px;")
        layout.addWidget(training_label)
        
        # Área de texto masivo
        self.massive_input = QTextEdit()
        self.massive_input.setPlaceholderText("Paste large text here for training...")
        self.massive_input.setStyleSheet(styles.MASSIVE_INPUT_STYLE)
        self.massive_input.setMaximumHeight(100)
        self.massive_input.setMinimumHeight(60)
        layout.addWidget(self.massive_input)
        
        # Botón de entrenar
        btn_train = QPushButton("Train Now")
        btn_train.setObjectName("TrainBtn")
        btn_train.setStyleSheet(styles.TRAIN_BUTTON_STYLE)
        btn_train.setMaximumHeight(32)
        btn_train.clicked.connect(self.entrenar_masivo)
        layout.addWidget(btn_train)
        
        # Botón de dormir (consolidación de memoria)
        btn_sleep = QPushButton("💤 Sleep Mode")
        btn_sleep.setObjectName("SleepBtn")
        btn_sleep.setStyleSheet(styles.SLEEP_BUTTON_STYLE)
        btn_sleep.setMaximumHeight(32)
        btn_sleep.clicked.connect(self.dormir_cerebros)
        layout.addWidget(btn_sleep)
        
        # Botones de carga
        buttons = [
            ("📄 Text", self.abrir_txt),
            ("📁 TXT Folder", self.abrir_carpeta_txt),
            ("📕 PDF", self.abrir_pdf),
            ("🎬 Video", self.abrir_mp4),
            ("📂 Video Folder", self.abrir_carpeta_videos)
        ]
        
        for text, handler in buttons:
            btn = QPushButton(text)
            btn.setObjectName("SecondaryBtn")
            btn.setMaximumHeight(28)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
        
        layout.addSpacing(5)
    
    def add_separator(self, layout):
        """Agrega un separador"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3e3f4b; max-height: 1px;")
        layout.addWidget(separator)
        layout.addSpacing(5)
    
    def add_brain_status_section(self, layout):
        """Agrega la sección de estado de cerebros"""
        stats_label = QLabel("📟 MAGI STATUS")
        stats_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px; padding: 3px 0; letter-spacing: 1px;")
        layout.addWidget(stats_label)
        
        # Crear controles para cada cerebro
        self.brain_controls = {}
        for brain_name in ["melchor", "gaspar", "casper"]:
            control = self.create_brain_control(brain_name)
            layout.addWidget(control)
        
        # Peso total
        self.lbl_peso = QLabel("💾 Memory: 0.00 MB")
        self.lbl_peso.setObjectName("StatLabel")
        layout.addWidget(self.lbl_peso)
        
        layout.addSpacing(5)
    
    def create_brain_control(self, brain_name):
        """Crea un control para un cerebro"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox.setFixedSize(16, 16)
        checkbox.setStyleSheet(styles.CHECKBOX_STYLE)
        checkbox.stateChanged.connect(lambda state: self.brain_manager.toggle_brain(brain_name, state == 2))
        checkbox.stateChanged.connect(lambda state: self.on_brain_toggled(brain_name, state == 2))
        layout.addWidget(checkbox)
        
        # Label
        brain_ia = getattr(self.brain_manager, f"ia_{brain_name}")
        label = QLabel(f"🟢 {brain_name.upper()}: {brain_ia.n_oculta}")
        label.setObjectName("StatLabel")
        label.setStyleSheet("font-size: 10px;")
        layout.addWidget(label, 1)
        
        # Botón de carga
        btn_load = QPushButton("📂")
        btn_load.setFixedSize(20, 20)
        btn_load.setToolTip(f"Load {brain_name.upper()}")
        btn_load.setStyleSheet(styles.LOAD_BRAIN_BUTTON_STYLE)
        btn_load.clicked.connect(lambda: self.cargar_cerebro_externo(brain_name))
        layout.addWidget(btn_load)
        
        # Guardar referencias
        self.brain_controls[brain_name] = {
            'checkbox': checkbox,
            'label': label
        }
        
        return container
    
    def add_anonimo_section(self, layout):
        """Agrega la sección del votante anónimo"""
        self.add_separator(layout)
        
        # Título
        anonimo_label = QLabel("👤 ANÓNIMO")
        anonimo_label.setStyleSheet("color: #a855f7; font-weight: bold; font-size: 11px; padding: 3px 0; letter-spacing: 1px;")
        layout.addWidget(anonimo_label)
        
        # Switch
        self.switch_anonimo = QCheckBox("Activar Votante")
        self.switch_anonimo.setStyleSheet(styles.ANONIMO_SWITCH_STYLE)
        self.switch_anonimo.stateChanged.connect(self.toggle_votante_anonimo)
        layout.addWidget(self.switch_anonimo)
        
        # Estado
        self.lbl_anonimo = QLabel("⚫ INACTIVO")
        self.lbl_anonimo.setObjectName("StatLabel")
        self.lbl_anonimo.setStyleSheet("color: #6b7280; font-size: 10px; font-style: italic;")
        layout.addWidget(self.lbl_anonimo)
        
        layout.addSpacing(3)
        
    def add_debate_section(self, layout):
        """Agrega la sección de modo debate"""
        self.add_separator(layout)
        
        # Título
        debate_label = QLabel("🔥 DEBATE MODE")
        debate_label.setStyleSheet("color: #f43f5e; font-weight: bold; font-size: 11px; padding: 3px 0; letter-spacing: 1px;")
        layout.addWidget(debate_label)
        
        # Switch
        self.switch_debate = QCheckBox("Auto-Deliberación")
        self.switch_debate.setStyleSheet(styles.DEBATE_SWITCH_STYLE)
        self.switch_debate.stateChanged.connect(self.toggle_modo_debate)
        layout.addWidget(self.switch_debate)
        
        # Estado
        self.lbl_debate_status = QLabel("⚫ INACTIVO")
        self.lbl_debate_status.setObjectName("StatLabel")
        self.lbl_debate_status.setStyleSheet("color: #6b7280; font-size: 10px; font-style: italic;")
        layout.addWidget(self.lbl_debate_status)
        
        layout.addSpacing(3)
    
    def create_chat_area(self):
        """Crea el área de chat"""
        chat_container = QWidget()
        chat_container.setStyleSheet("background-color: #0d0f17;")
        chat_vbox = QVBoxLayout(chat_container)
        chat_vbox.setContentsMargins(0, 0, 0, 0)
        chat_vbox.setSpacing(0)
        
        # Header con botón para ocultar sidebar
        header = QWidget()
        header.setFixedHeight(45)
        header.setStyleSheet("border-bottom: 1px solid #1e293b; background-color: #0d0f17;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        self.btn_toggle_sidebar = QPushButton("☰")
        self.btn_toggle_sidebar.setFixedSize(32, 32)
        self.btn_toggle_sidebar.setToolTip("Ocultar/Mostrar Panel Lateral")
        self.btn_toggle_sidebar.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_sidebar.setStyleSheet(styles.TOGGLE_SIDEBAR_STYLE)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.btn_toggle_sidebar)
        
        # Título central
        title = QLabel("MAGI SUPERCOMPUTER")
        title.setStyleSheet("color: #6366f1; font-weight: bold; font-size: 11px; letter-spacing: 2px;")
        header_layout.addStretch()
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Espacio vacío a la derecha para centrar el título
        spacer = QWidget()
        spacer.setFixedSize(32, 32)
        header_layout.addWidget(spacer)
        
        chat_vbox.addWidget(header)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #0d0f17;")
        self.scroll_area.verticalScrollBar().setStyleSheet(styles.SCROLLBAR_STYLE)
        
        self.messages_content = QWidget()
        self.messages_content.setStyleSheet("background-color: #0d0f17;")
        self.messages_layout = QVBoxLayout(self.messages_content)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(0)
        self.messages_layout.addStretch(1) # Stretch al inicio para empujar hacia abajo
        
        self.scroll_area.setWidget(self.messages_content)
        chat_vbox.addWidget(self.scroll_area)
        
        # Input area
        input_container = self.create_input_area()
        chat_vbox.addWidget(input_container)
        
        return chat_container
    
    def create_input_area(self):
        """Crea el área de input"""
        input_container = QWidget()
        input_container.setFixedHeight(100)
        input_container.setStyleSheet("background: transparent;")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(100, 0, 100, 25)
        
        input_shadow = QFrame()
        input_shadow.setStyleSheet(styles.USER_INPUT_STYLE)
        inner_input_layout = QHBoxLayout(input_shadow)
        inner_input_layout.setContentsMargins(10, 5, 10, 5)
        
        # Input de texto
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Send a message")
        self.user_input.setStyleSheet("border: none; background: transparent; padding: 12px; font-size: 15px; color: #f8fafc;")
        self.user_input.returnPressed.connect(self.enviar_mensaje)
        inner_input_layout.addWidget(self.user_input)
        
        # Botón enviar
        btn_enviar = QPushButton("➡️")
        btn_enviar.setFixedSize(32, 32)
        btn_enviar.setStyleSheet(styles.SEND_BUTTON_STYLE)
        btn_enviar.clicked.connect(self.enviar_mensaje)
        inner_input_layout.addWidget(btn_enviar)
        
        # Botón micrófono
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedSize(32, 32)
        self.btn_mic.setStyleSheet(styles.MIC_BUTTON_STYLE)
        self.btn_mic.clicked.connect(self.alternar_escucha)
        inner_input_layout.addWidget(self.btn_mic)
        
        input_layout.addWidget(input_shadow)
        return input_container
    
    # ========== MÉTODOS DE INTERACCIÓN ==========
    
    @Slot(str, str)
    def agregar_mensaje(self, autor, mensaje):
        """Agrega un mensaje al chat"""
        is_ai = autor in ["IA", "SISTEMA", "MAGI", "MELCHOR", "GASPAR", "CASPER", "ANÓNIMO"]
        msg_widget = MessageWidget(autor, mensaje, is_ai)
        
        self.messages_layout.addWidget(msg_widget)
        
        # Guardar última respuesta para el hilo del debate
        if is_ai:
            self.ultima_respuesta_magi = mensaje
            if self.debate_activo:
                # Incrementar turno para el siguiente cerebro
                self.debate_turn = (self.debate_turn + 1) % 3
                # Iniciar siguiente paso del debate con un pequeño retraso
                QTimer.singleShot(3000, self.debate_step)
        
        # Scroll to bottom reliably
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    
    @Slot(bool)
    def toggle_thinking_animation(self, mostrar):
        """Muestra u oculta la animación de pensamiento"""
        if mostrar:
            if self.thinking_widget is None:
                self.thinking_widget = ThinkingWidget()
                self.messages_layout.addWidget(self.thinking_widget)
                QApplication.processEvents()
                self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().maximum()
                )
        else:
            if self.thinking_widget is not None:
                self.thinking_widget.stop_animation()
                self.messages_layout.removeWidget(self.thinking_widget)
                self.thinking_widget.deleteLater()
                self.thinking_widget = None
    
    @Slot(int, float)
    def actualizar_labels(self, neuronas, peso):
        """Actualiza las etiquetas de estadísticas"""
        for brain_name in ["melchor", "gaspar", "casper"]:
            brain_ia = getattr(self.brain_manager, f"ia_{brain_name}")
            label = self.brain_controls[brain_name]['label']
            label.setText(f"{brain_name.upper()}: {brain_ia.n_oculta}")
        self.lbl_peso.setText(f"💾 Mem: {peso:.2f} MB")
    
    @Slot(str)
    def cargar_texto_transcrito(self, texto):
        """Carga texto transcrito en el área masiva"""
        self.massive_input.setPlainText(texto)
        self.agregar_mensaje("SISTEMA", "Transcripción cargada.")
    
    def actualizar_info_archivo(self):
        """Actualiza la información de archivos"""
        peso = self.brain_manager.get_total_size_mb()
        self.actualizar_labels(0, peso)
    
    def on_brain_toggled(self, brain_name, activo):
        """Callback cuando se activa/desactiva un cerebro"""
        label = self.brain_controls[brain_name]['label']
        if activo:
            label.setStyleSheet("color: #e2e8f0; font-size: 12px; font-weight: 500;")
            self.agregar_mensaje("SISTEMA", f"🟢 {brain_name.upper()} ACTIVADO - Brain cell online")
        else:
            label.setStyleSheet("color: #4b5563; font-size: 12px; text-decoration: line-through;")
            self.agregar_mensaje("SISTEMA", f"⚪ {brain_name.upper()} DESACTIVADO - Dormant state")
    
    def toggle_votante_anonimo(self, state):
        """Activa o desactiva el votante anónimo"""
        self.brain_manager.votante_anonimo_activo = (state == 2)
        
        if self.brain_manager.votante_anonimo_activo:
            self.lbl_anonimo.setText("🟣 ACTIVO - Votando aleatoriamente")
            self.lbl_anonimo.setStyleSheet("color: #a855f7; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "👤 Votante Anónimo ACTIVADO - Participará en todas las deliberaciones con votos aleatorios")
        else:
            self.lbl_anonimo.setText("⚫ INACTIVO")
            self.lbl_anonimo.setStyleSheet("color: #6b7280; font-size: 11px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "👤 Votante Anónimo DESACTIVADO - Solo votarán Melchor, Gaspar y Casper")
    
    def toggle_modo_debate(self, state):
        """Activa o desactiva el modo debate"""
        self.debate_activo = (state == 2)
        
        if self.debate_activo:
            self.lbl_debate_status.setText("🔴 ACTIVO - IAs conversando")
            self.lbl_debate_status.setStyleSheet("color: #f43f5e; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "🔥 Modo Debate ACTIVADO - Las IAs comenzarán a deliberar entre ellas")
            
            # Si hay una última respuesta, que sigan desde ahí, si no, que empiecen con algo
            prompt = self.ultima_respuesta_magi if self.ultima_respuesta_magi else "Hablemos sobre nuestra propia existencia."
            QTimer.singleShot(1000, lambda: self.debate_step(prompt))
        else:
            self.lbl_debate_status.setText("⚫ INACTIVO")
            self.lbl_debate_status.setStyleSheet("color: #6b7280; font-size: 11px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Modo Debate DESACTIVADO")

    def debate_step(self, prompt=None):
        """Ejecuta un paso del debate con respuestas individuales"""
        if not self.debate_activo:
            return
            
        texto = prompt if prompt else self.ultima_respuesta_magi
        if not texto: return

        # Determinar a quién le toca
        nombres = ["MELCHOR", "GASPAR", "CASPER"]
        brain_name = nombres[self.debate_turn]
        
        # Procesar de forma individual
        threading.Thread(target=self.brain_manager.process_debate_message, 
                        args=(texto, brain_name, self.signals), daemon=True).start()

    def enviar_mensaje(self):
        """Envía un mensaje"""
        texto = self.user_input.text().strip()
        if not texto:
            return
        self.user_input.clear()
        self.agregar_mensaje("Tu", texto)
        threading.Thread(target=self.brain_manager.process_message, 
                        args=(texto, self.signals), daemon=True).start()
    
    def alternar_escucha(self):
        """Alterna el estado de escucha del micrófono"""
        self.escuchando = not self.escuchando
        if self.escuchando:
            self.btn_mic.setText("🔴")
            self.btn_mic.setStyleSheet(styles.MIC_BUTTON_ACTIVE_STYLE)
            self.agregar_mensaje("SISTEMA", "Micrófono activado. Escuchando continuamente...")
            # TODO: Implementar hilo de voz
        else:
            self.btn_mic.setText("🎤")
            self.btn_mic.setStyleSheet(styles.MIC_BUTTON_STYLE)
            self.agregar_mensaje("SISTEMA", "Micrófono desactivado.")
    
    def entrenar_masivo(self):
        """Entrena con texto masivo"""
        texto = self.massive_input.toPlainText().strip()
        if not texto:
            self.agregar_mensaje("SISTEMA", "No hay texto para entrenar.")
            return
        
        self.massive_input.clear()
        self.agregar_mensaje("SISTEMA", f"Iniciando entrenamiento con {len(texto)} caracteres...")
        threading.Thread(target=self.brain_manager.train_massive, 
                        args=(texto, self.signals), daemon=True).start()
    
    def dormir_cerebros(self):
        """Activa el modo de sueño para consolidación de memoria"""
        dialog = SleepDialog(self)
        dialog.sleep_started.connect(self.ejecutar_modo_sueno)
        dialog.exec()
    
    def ejecutar_modo_sueno(self, duracion_segundos):
        """Ejecuta el modo de sueño con la duración especificada"""
        self.agregar_mensaje("SISTEMA", f"💤 Activando modo de sueño profundo por {duracion_segundos // 60} minutos...")
        threading.Thread(target=self.brain_manager.sleep_all_brains, 
                        args=(self.signals,), daemon=True).start()
    
    def toggle_sidebar(self):
        """Muestra u oculta la barra lateral"""
        self.sidebar.setVisible(not self.sidebar.isVisible())
    
    def abrir_txt(self):
        """Abre un archivo de texto"""
        filename, _ = QFileDialog.getOpenFileName(self, "Select text file", "/", "Text Files (*.txt)")
        if filename:
            self.barra_progreso.setValue(0)
            self.agregar_mensaje("SISTEMA", f"Analyzing '{os.path.basename(filename)}'...")
            threading.Thread(target=self.brain_manager.train_from_file, 
                            args=(filename, self.signals), daemon=True).start()
    
    def abrir_carpeta_txt(self):
        """Abre una carpeta de archivos TXT"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with TXT files", "/")
        if folder:
            self.barra_progreso.setValue(0)
            self.agregar_mensaje("SISTEMA", f"Processing TXT files in: {os.path.basename(folder)}")
            threading.Thread(target=self.brain_manager.train_from_text_folder, 
                            args=(folder, self.signals), daemon=True).start()
    
    def abrir_pdf(self):
        """Abre un archivo PDF"""
        filename, _ = QFileDialog.getOpenFileName(self, "Select PDF file", "/", "PDF Files (*.pdf)")
        if filename:
            self.barra_progreso.setValue(0)
            self.agregar_mensaje("SISTEMA", f"Analyzing PDF '{os.path.basename(filename)}'...")
            threading.Thread(target=self.brain_manager.train_from_pdf, 
                            args=(filename, self.signals), daemon=True).start()
    
    def abrir_mp4(self):
        """Abre un archivo de video"""
        filename, _ = QFileDialog.getOpenFileName(self, "Select Video file", "/", 
                                                  "Video Files (*.mp4 *.mkv *.wav *.mp3)")
        if filename:
            self.barra_progreso.setValue(0)
            self.agregar_mensaje("SISTEMA", f"Analyzing Video/Audio '{os.path.basename(filename)}' (using Whisper)...")
            threading.Thread(target=self.brain_manager.train_from_video, 
                            args=(filename, self.signals), daemon=True).start()
    
    def abrir_carpeta_videos(self):
        """Abre una carpeta de videos"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Videos", "/")
        if folder:
            self.barra_progreso.setValue(0)
            self.agregar_mensaje("SISTEMA", f"Processing all videos in: {os.path.basename(folder)}")
            threading.Thread(target=self.brain_manager.train_from_video_folder, 
                            args=(folder, self.signals), daemon=True).start()
    
    def cargar_cerebro_externo(self, nombre_cerebro):
        """Carga un cerebro pre-entrenado"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select pre-trained {nombre_cerebro.upper()} brain", 
            "/", 
            "Brain Files (*.pkl)"
        )
        
        if not filename:
            return
        
        try:
            success, message = self.brain_manager.load_external_brain(nombre_cerebro, filename)
            if success:
                self.agregar_mensaje("SISTEMA", message)
                self.actualizar_info_archivo()
            else:
                self.agregar_mensaje("SISTEMA", f"❌ {message}")
        except Exception as e:
            self.agregar_mensaje("SISTEMA", f"❌ Error cargando cerebro: {str(e)}")


def main():
    """Función principal"""
    import torch
    
    # Forzar uso de hilos en CPU para mayor rendimiento en M4
    torch.set_num_threads(os.cpu_count() or 8)
    
    app = QApplication(sys.argv)
    window = MAGISystem()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
