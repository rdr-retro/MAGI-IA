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
                             QCheckBox, QTabWidget, QGridLayout)
from PySide6.QtCore import Qt, Slot, QSize, QMetaObject, Q_ARG, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QMovie
import numpy as np
import requests
import random

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
        self.setMinimumSize(900, 600)
        
        # Inicializar gestor de cerebros
        self.brain_manager = BrainManager()
        
        # Señales
        self.signals = IAWorkerSignals()
        self.thinking_widget = None
        
        # Estado
        self.escuchando = False
        self.buffer_voz = ""
        self.debate_activo = False
        self.ultima_respuesta_magi = ""
        self.debate_turn = 0 # 0=Melchor, 1=Gaspar, 2=Casper
        self.chat_history = [] # Memoria a corto plazo (últimos mensajes)
        self.wiki_activo = False
        self.wiki_dialogo = False
        self.wiki_identity = False
        self.wiki_timer = QTimer()
        self.wiki_timer.timeout.connect(self.fetch_wiki_knowledge)
        
        # Crear interfaz
        self.init_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Inyectar Definición de Identidades (Identity Charter) tras 5 segundos
        QTimer.singleShot(5000, self.inyectar_charter_identidad)
        
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
        self.signals.pensando.connect(self.toggle_thinking_animation)
        self.signals.cerebro_expandido.connect(self.on_brain_expanded)
        self.signals.progreso_entrenamiento.connect(self.actualizar_progreso)
        self.signals.texto_transcrito.connect(self.cargar_texto_transcrito)
    
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
        
        main_layout.addWidget(self.sidebar, 0)
        main_layout.addWidget(chat_area, 1)
    
    def create_sidebar(self):
        """Crea el panel lateral"""
        side_panel = QFrame()
        side_panel.setObjectName("SidePanel")
        side_panel.setFixedWidth(300)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(10, 15, 10, 10)
        side_layout.setSpacing(8)
        
        # Logo
        self.add_logo(side_layout)
        
        # Tabs container
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(styles.TAB_WIDGET_STYLE)
        
        # 1. Dashboard Tab
        self.dashboard_tab = QWidget()
        self.create_dashboard_tab(self.dashboard_tab)
        self.tabs.addTab(self.dashboard_tab, "DASH")
        
        # 2. Training Tab
        self.training_tab = QWidget()
        self.create_training_tab(self.training_tab)
        self.tabs.addTab(self.training_tab, "TRAIN")
        
        # 3. Network Tab
        self.network_tab = QWidget()
        self.create_network_tab(self.network_tab)
        self.tabs.addTab(self.network_tab, "NET")
        
        side_layout.addWidget(self.tabs)
        
        # Barra de progreso (siempre visible abajo)
        self.add_separator(side_layout)
        
        # Label de progreso
        self.lbl_progreso = QLabel("Ready")
        self.lbl_progreso.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: 500;")
        self.lbl_progreso.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(self.lbl_progreso)
        
        self.barra_progreso = QProgressBar()
        self.barra_progreso.setTextVisible(False)
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
            logo_label.setFixedHeight(70) # Altura fija para evitar saltos
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
            self.adn_label.setFixedSize(180, 150) # Tamaño fijo riguroso
            self.adn_movie.setScaledSize(QSize(180, 150))
            layout.addWidget(self.adn_label)
            self.adn_movie.start()

    def add_separator(self, layout):
        """Agrega un separador"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3e3f4b; max-height: 1px;")
        layout.addWidget(separator)
        layout.addSpacing(5)

    def create_dashboard_tab(self, widget):
        """Crea el contenido de la pestaña Dashboard"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Animación ADN
        self.add_adn_animation(layout)
        
        # Estadísticas generales
        stats_group = QFrame()
        stats_group.setStyleSheet("background-color: #111827; border-radius: 10px; padding: 10px;")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_title = QLabel("SYSTEM METRICS")
        stats_title.setStyleSheet("color: #6366f1; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        stats_layout.addWidget(stats_title)
        
        self.lbl_peso = QLabel("💾 Memory: 0.00 MB")
        self.lbl_peso.setObjectName("StatLabel")
        stats_layout.addWidget(self.lbl_peso)
        
        # Neuronas de cada cerebro
        self.lbl_melchor_neurons = QLabel("🔴 Melchor: 0 neurons")
        self.lbl_melchor_neurons.setObjectName("StatLabel")
        stats_layout.addWidget(self.lbl_melchor_neurons)
        
        self.lbl_gaspar_neurons = QLabel("🟢 Gaspar: 0 neurons")
        self.lbl_gaspar_neurons.setObjectName("StatLabel")
        stats_layout.addWidget(self.lbl_gaspar_neurons)
        
        self.lbl_casper_neurons = QLabel("🔵 Casper: 0 neurons")
        self.lbl_casper_neurons.setObjectName("StatLabel")
        stats_layout.addWidget(self.lbl_casper_neurons)
        
        self.lbl_uptime = QLabel("⏱️ Uptime: Stable")
        self.lbl_uptime.setObjectName("StatLabel")
        stats_layout.addWidget(self.lbl_uptime)
        
        layout.addWidget(stats_group)
        layout.addStretch()

    def create_training_tab(self, widget):
        """Crea el contenido de la pestaña Entrenamiento"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Área de texto masivo
        self.massive_input = QTextEdit()
        self.massive_input.setPlaceholderText("Paste massive data here...")
        self.massive_input.setStyleSheet(styles.MASSIVE_INPUT_STYLE)
        self.massive_input.setMaximumHeight(150)
        layout.addWidget(self.massive_input)
        
        # Botones principales
        btn_train = QPushButton("PROCESS DATA")
        btn_train.setObjectName("TrainBtn")
        btn_train.setStyleSheet(styles.TRAIN_BUTTON_STYLE)
        btn_train.clicked.connect(self.entrenar_masivo)
        layout.addWidget(btn_train)
        
        btn_sleep = QPushButton("💤 DEEP SLEEP")
        btn_sleep.setObjectName("SleepBtn")
        btn_sleep.setStyleSheet(styles.SLEEP_BUTTON_STYLE)
        btn_sleep.clicked.connect(self.dormir_cerebros)
        layout.addWidget(btn_sleep)
        
        # Ribbon de carga de archivos (Cuadrícula)
        ribbon_label = QLabel("IMPORT SOURCES")
        ribbon_label.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 10px; margin-top: 5px;")
        layout.addWidget(ribbon_label)
        
        ribbon_container = QWidget()
        ribbon_grid = QGridLayout(ribbon_container)
        ribbon_grid.setContentsMargins(0, 0, 0, 0)
        ribbon_grid.setSpacing(5)
        
        buttons = [
            ("📄", "Load .txt file\nSupports UTF-8 encoding", self.abrir_txt, 0, 0),
            ("📁", "Batch process TXT folder\nSupports nested directories", self.abrir_carpeta_txt, 0, 1),
            ("📕", "Extract text from PDF\nMax 500 pages recommended", self.abrir_pdf, 0, 2),
            ("🎬", "Transcribe audio with Whisper\nFormats: mp4, mkv, wav, mp3", self.abrir_mp4, 1, 0),
            ("📂", "Batch transcribe videos\nMay take several minutes", self.abrir_carpeta_videos, 1, 1),
        ]
        
        for icon, tooltip, handler, r, c in buttons:
            btn = QPushButton(icon)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(styles.ACTION_RIBBON_BTN_STYLE)
            btn.clicked.connect(handler)
            btn.setFixedSize(50, 50)  # Tamaño uniforme
            ribbon_grid.addWidget(btn, r, c)
            
        layout.addWidget(ribbon_container)
        layout.addStretch()

    def create_network_tab(self, widget):
        """Crea el contenido de la pestaña Red/Cerebros"""
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Brain Status Title
        label = QLabel("NEURAL CORES")
        label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 10px; letter-spacing: 1px;")
        layout.addWidget(label)
        
        # Brain Cards
        self.brain_controls = {}
        for brain_name in ["melchor", "gaspar", "casper"]:
            card = self.create_brain_card(brain_name)
            layout.addWidget(card)
            
        # Logic Controls
        logic_label = QLabel("ADVANCED LOGIC")
        logic_label.setStyleSheet("color: #f8fafc; font-weight: bold; font-size: 10px; margin-top: 10px; border-top: 1px solid #3e3f4b; padding-top: 10px;")
        layout.addWidget(logic_label)
        
        # Votante
        self.switch_anonimo = QCheckBox("Anon. Voting")
        self.switch_anonimo.setStyleSheet(styles.ANONIMO_SWITCH_STYLE)
        self.switch_anonimo.stateChanged.connect(self.toggle_votante_anonimo)
        layout.addWidget(self.switch_anonimo)
        
        self.lbl_anonimo = QLabel("⚫ INACTIVO")
        self.lbl_anonimo.setObjectName("StatLabel")
        self.lbl_anonimo.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_anonimo)
        
        # Debate
        self.switch_debate = QCheckBox("Auto-Debate")
        self.switch_debate.setStyleSheet(styles.DEBATE_SWITCH_STYLE)
        self.switch_debate.stateChanged.connect(self.toggle_modo_debate)
        layout.addWidget(self.switch_debate)
        
        self.lbl_debate_status = QLabel("⚫ INACTIVO")
        self.lbl_debate_status.setObjectName("StatLabel")
        self.lbl_debate_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_debate_status)
        
        # Wiki
        self.switch_wiki = QCheckBox("Wiki Inject")
        self.switch_wiki.setStyleSheet(styles.WIKI_SWITCH_STYLE)
        self.switch_wiki.stateChanged.connect(self.toggle_wiki_mode)
        layout.addWidget(self.switch_wiki)
        
        self.lbl_wiki_status = QLabel("⚫ INACTIVO")
        self.lbl_wiki_status.setObjectName("StatLabel")
        self.lbl_wiki_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_wiki_status)

        # Wiki Dialogue
        self.switch_wiki_dialogue = QCheckBox("Wiki Dialogue")
        self.switch_wiki_dialogue.setStyleSheet(styles.WIKI_SWITCH_STYLE) # Reusing wiki style
        self.switch_wiki_dialogue.stateChanged.connect(self.toggle_wiki_dialogue)
        layout.addWidget(self.switch_wiki_dialogue)

        self.lbl_wiki_dialogue_status = QLabel("⚫ INACTIVO")
        self.lbl_wiki_dialogue_status.setObjectName("StatLabel")
        self.lbl_wiki_dialogue_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_wiki_dialogue_status)

        # Wiki Identity
        self.switch_wiki_identity = QCheckBox("Wiki Identity")
        self.switch_wiki_identity.setStyleSheet(styles.WIKI_SWITCH_STYLE)
        self.switch_wiki_identity.stateChanged.connect(self.toggle_wiki_identity)
        layout.addWidget(self.switch_wiki_identity)

        self.lbl_wiki_identity_status = QLabel("⚫ INACTIVO")
        self.lbl_wiki_identity_status.setObjectName("StatLabel")
        self.lbl_wiki_identity_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_wiki_identity_status)
        
        layout.addStretch()

    def create_brain_card(self, brain_name):
        """Crea una tarjeta visual para un cerebro"""
        card = QFrame()
        card.setObjectName("BrainCard")
        card.setStyleSheet(styles.BRAIN_CARD_STYLE)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        
        # Izquierda: Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox.setFixedSize(16, 16)
        checkbox.setStyleSheet(styles.CHECKBOX_STYLE)
        checkbox.stateChanged.connect(lambda state, b=brain_name: self.brain_manager.toggle_brain(b, state == 2))
        checkbox.stateChanged.connect(lambda state, b=brain_name: self.on_brain_toggled(b, state == 2))
        card_layout.addWidget(checkbox)
        
        # Centro: Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(brain_name.upper())
        name_label.setObjectName("BrainName")
        info_layout.addWidget(name_label)
        
        brain_ia = getattr(self.brain_manager, f"ia_{brain_name}")
        neurons_label = QLabel(f"Neurons: {brain_ia.n_oculta}")
        neurons_label.setObjectName("BrainNeurons")
        info_layout.addWidget(neurons_label)
        
        card_layout.addLayout(info_layout, 1)
        
        # Derecha: Botón Load
        btn_load = QPushButton("📂")
        btn_load.setFixedSize(24, 24)
        btn_load.setToolTip(f"Load external {brain_name.upper()} brain (.pkl)")
        btn_load.setStyleSheet(styles.LOAD_BRAIN_BUTTON_STYLE)
        btn_load.clicked.connect(lambda checked=False, b=brain_name: self.cargar_cerebro_externo(b))
        card_layout.addWidget(btn_load)
        
        # Guardar referencias
        self.brain_controls[brain_name] = {
            'checkbox': checkbox,
            'label': neurons_label,
            'card': card,
            'name_label': name_label
        }
        
        return card

    
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
        
        # Notification Area (Ticker)
        self.notification_area = QFrame()
        self.notification_area.setObjectName("NotificationArea")
        self.notification_area.setStyleSheet(styles.NOTIFICATION_AREA_STYLE)
        notification_layout = QHBoxLayout(self.notification_area)
        notification_layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_notification = QLabel("IDLE - System ready")
        self.lbl_notification.setObjectName("NotificationLabel")
        self.lbl_notification.setStyleSheet(styles.NOTIFICATION_LABEL_STYLE)
        # Asegurar que el texto largo no rompa la UI ni expanda la ventana
        self.lbl_notification.setWordWrap(False)
        self.lbl_notification.setMinimumWidth(10) # Permitir que se reduzca
        from PySide6.QtWidgets import QSizePolicy
        self.lbl_notification.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        notification_layout.addWidget(self.lbl_notification, 1) # Darle stretch 1
        
        chat_vbox.addWidget(self.notification_area)
        
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
        """Agrega un mensaje al chat y a la memoria a corto plazo"""
        is_ai = autor in ["IA", "SISTEMA", "MAGI", "MELCHOR", "GASPAR", "CASPER", "ANÓNIMO", "WIKIPEDIA"]
        
        # Guardar en historial (máximo 5 mensajes para contexto)
        if autor == "ESTADÍSTICAS":
            self.lbl_notification.setText(f"📊 {mensaje}")
            self.lbl_notification.setToolTip(mensaje)
            return
            
        if autor == "SISTEMA":
            self.lbl_notification.setText(f"⚙️ {mensaje}")
            self.lbl_notification.setToolTip(mensaje)
            return

        if autor == "WIKIPEDIA":
            # Update notification bar with short message
            self.lbl_notification.setText(f"🌐 Wikipedia: Knowledge injected")
            # Continue to show full message in chat (removed return)


        # Guardar en historial (máximo 5 mensajes para contexto)
        self.chat_history.append(f"{autor}: {mensaje}")
        if len(self.chat_history) > 5:
            self.chat_history.pop(0)

        msg_widget = MessageWidget(autor, mensaje, is_ai)
        
        self.messages_layout.addWidget(msg_widget)
        
        # Animación de fade-in suave
        msg_widget.setWindowOpacity(0.0)
        animation = QPropertyAnimation(msg_widget, b"windowOpacity")
        animation.setDuration(300)  # 300ms
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        
        # Guardar referencia para que no se destruya
        if not hasattr(self, 'animations'):
            self.animations = []
        self.animations.append(animation)
        
        # Guardar última respuesta para el hilo del debate
        if is_ai:
            self.ultima_respuesta_magi = mensaje
            if self.debate_activo:
                # Incrementar turno para el siguiente cerebro
                self.debate_turn = (self.debate_turn + 1) % 3
                # Iniciar siguiente paso del debate con un pequeño retraso
                QTimer.singleShot(3000, self.debate_step)
            
            # Dialogue Mode: If AI responded to Wikipedia, trigger next Wiki message
            if self.wiki_dialogo and autor in ["MELCHOR", "GASPAR", "CASPER", "MAGI", "IA"]:
                # Trigger Wikipedia after AI responds
                QTimer.singleShot(4000, self.fetch_wiki_knowledge)
        
        # Dialogue Mode: If Wikipedia sent a message, trigger AI response
        if self.wiki_dialogo and autor == "WIKIPEDIA":
            # MAGI must answer
            contexto = "\n".join(self.chat_history[-4:])
            threading.Thread(target=self.brain_manager.process_message, 
                            args=(contexto, self.signals), daemon=True).start()
        
        # Scroll to bottom reliably
        # FIXED: Usar un temporizador un poco más largo para asegurar que el layout se ha estabilizado
        QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
    
    @Slot(bool)
    def toggle_thinking_animation(self, mostrar):
        """Muestra u oculta la animación de pensamiento"""
        if mostrar:
            if self.thinking_widget is None:
                self.thinking_widget = ThinkingWidget()
                self.messages_layout.addWidget(self.thinking_widget)
                # FIXED: Evitar processEvents que causa saltos de layout
                QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().maximum()
                ))
        else:
            if self.thinking_widget is not None:
                self.thinking_widget.stop_animation()
                self.messages_layout.removeWidget(self.thinking_widget)
                self.thinking_widget.deleteLater()
                self.thinking_widget = None
    
    @Slot(str, int)
    def on_brain_expanded(self, nombre, n):
        """Callback cuando un cerebro crece"""
        # Actualizar el chat
        self.agregar_mensaje("ESTADÍSTICAS", f"🚀 {nombre.upper()} ha evolucionado a {n} neuronas.")
        
        # Actualizar sidebar
        key = nombre.lower()
        if key in self.brain_controls:
            label = self.brain_controls[key]['label']
            label.setText(f"Neurons: {n}")
        
        # Actualizar Dashboard metrics
        if key == "melchor":
            self.lbl_melchor_neurons.setText(f"🔴 Melchor: {n:,} neurons")
        elif key == "gaspar":
            self.lbl_gaspar_neurons.setText(f"🟢 Gaspar: {n:,} neurons")
        elif key == "casper":
            self.lbl_casper_neurons.setText(f"🔵 Casper: {n:,} neurons")
        
        # Actualizar peso total
        self.actualizar_info_archivo()
    
    @Slot(int, float)
    def actualizar_labels(self, neuronas, peso):
        """Actualiza las etiquetas de estadísticas"""
        for brain_name in ["melchor", "gaspar", "casper"]:
            if brain_name in self.brain_controls:
                brain_ia = getattr(self.brain_manager, f"ia_{brain_name}")
                label = self.brain_controls[brain_name]['label']
                label.setText(f"Neurons: {brain_ia.n_oculta}")
        
        # Actualizar métricas en Dashboard
        self.lbl_peso.setText(f"💾 Memory: {peso:.2f} MB")
        
        # Actualizar neuronas individuales en Dashboard
        melchor_n = self.brain_manager.ia_melchor.n_oculta
        gaspar_n = self.brain_manager.ia_gaspar.n_oculta
        casper_n = self.brain_manager.ia_casper.n_oculta
        
        self.lbl_melchor_neurons.setText(f"🔴 Melchor: {melchor_n:,} neurons")
        self.lbl_gaspar_neurons.setText(f"🟢 Gaspar: {gaspar_n:,} neurons")
        self.lbl_casper_neurons.setText(f"🔵 Casper: {casper_n:,} neurons")
    
    @Slot(str)
    def cargar_texto_transcrito(self, texto):
        """Carga texto transcrito en el área masiva"""
        self.massive_input.setPlainText(texto)
        self.agregar_mensaje("SISTEMA", "Transcripción cargada.")
    
    def actualizar_info_archivo(self):
        """Actualiza la información de archivos"""
        peso = self.brain_manager.get_total_size_mb()
        self.actualizar_labels(0, peso)
    
    @Slot(int)
    def actualizar_progreso(self, valor):
        """Actualiza la barra de progreso con colores dinámicos y texto"""
        self.barra_progreso.setValue(valor)
        
        # Color dinámico según estado
        if valor == 0:
            # Idle - gris
            self.barra_progreso.setStyleSheet("""
                QProgressBar { 
                    background-color: #1f2937; 
                    border: none; 
                    border-radius: 4px; 
                    height: 6px; 
                }
                QProgressBar::chunk { 
                    background-color: #374151;
                    border-radius: 4px; 
                }
            """)
            self.lbl_progreso.setText("Ready")
            self.lbl_progreso.setStyleSheet("color: #94a3b8; font-size: 9px; font-weight: 500;")
        elif valor == 100:
            # Completo - verde
            self.barra_progreso.setStyleSheet("""
                QProgressBar { 
                    background-color: #1f2937; 
                    border: none; 
                    border-radius: 4px; 
                    height: 6px; 
                }
                QProgressBar::chunk { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                    border-radius: 4px; 
                }
            """)
            self.lbl_progreso.setText("✓ Complete")
            self.lbl_progreso.setStyleSheet("color: #10b981; font-size: 9px; font-weight: 600;")
            # Reset después de 2 segundos
            QTimer.singleShot(2000, lambda: self.actualizar_progreso(0))
        else:
            # Procesando - azul/índigo
            self.barra_progreso.setStyleSheet("""
                QProgressBar { 
                    background-color: #1f2937; 
                    border: none; 
                    border-radius: 4px; 
                    height: 6px; 
                }
                QProgressBar::chunk { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
                    border-radius: 4px; 
                }
            """)
            self.lbl_progreso.setText(f"Processing... {valor}%")
            self.lbl_progreso.setStyleSheet("color: #6366f1; font-size: 9px; font-weight: 600;")
    
    def on_brain_toggled(self, brain_name, activo):
        """Callback cuando se activa/desactiva un cerebro"""
        controls = self.brain_controls[brain_name]
        label = controls['label']
        name_label = controls['name_label']
        card = controls['card']
        
        if activo:
            name_label.setStyleSheet("color: #f8fafc; font-weight: bold;")
            label.setStyleSheet("color: #94a3b8; font-size: 10px;")
            card.setStyleSheet(styles.BRAIN_CARD_STYLE)
            self.agregar_mensaje("SISTEMA", f"🟢 {brain_name.upper()} ACTIVADO")
        else:
            name_label.setStyleSheet("color: #4b5563; font-weight: bold; text-decoration: line-through;")
            label.setStyleSheet("color: #374151; font-size: 10px; text-decoration: line-through;")
            card.setStyleSheet("background-color: #0d0f17; border: 1px solid #1f2937; border-radius: 12px; padding: 5px;")
            self.agregar_mensaje("SISTEMA", f"⚪ {brain_name.upper()} DESACTIVADO")
    
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
        """Ejecuta un paso del debate con memoria de contexto"""
        if not self.debate_activo:
            return
            
        # Construir contexto de los últimos 4 mensajes
        contexto = "\n".join(self.chat_history[-4:]) if self.chat_history else ""
        if prompt:
            contexto += f"\nTu: {prompt}"
        
        # Determinar a quién le toca
        nombres = ["MELCHOR", "GASPAR", "CASPER"]
        brain_name = nombres[self.debate_turn]
        
        # Procesar de forma individual con contexto
        threading.Thread(target=self.brain_manager.process_debate_message, 
                        args=(contexto, brain_name, self.signals), daemon=True).start()

    def toggle_wiki_mode(self, state):
        """Activa o desactiva la inyección de Wikipedia"""
        self.wiki_activo = (state == 2)
        if self.wiki_activo:
            self.lbl_wiki_status.setText("🔵 ACTIVO - Recibiendo datos")
            self.lbl_wiki_status.setStyleSheet("color: #0ea5e9; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "🌐 Inyección de Wiki ACTIVADA - MAGI recibirá datos aleatorios de Wikipedia ES")
            # Iniciar primer fetch con pequeño retraso
            QTimer.singleShot(1000, self.fetch_wiki_knowledge)
        else:
            self.wiki_timer.stop()
            self.lbl_wiki_status.setText("⚫ INACTIVO")
            self.lbl_wiki_status.setStyleSheet("color: #6b7280; font-size: 11px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Inyección de Wiki DESACTIVADA")

    def fetch_wiki_knowledge(self):
        """Obtiene un artículo aleatorio de Wikipedia en español y lo enseña a MAGI"""
        if not self.wiki_activo: return
        
        # Mapeo de categorías para Wiki Identity
        categories = {
            "MELCHOR": ["Ciencia", "Tecnología", "Matemáticas", "Física", "Computación", "Astronomía", "Biología"],
            "GASPAR": ["Literatura", "Arte", "Música", "Pintura", "Cine", "Poesía", "Arquitectura", "Escultura"],
            "CASPER": ["Filosofía", "Ética", "Sociología", "Psicología", "Derecho", "Historia", "Religión", "Política"]
        }

        def job():
            try:
                tag_prefix = ""
                selected_brain = None
                
                if self.wiki_identity:
                    # Elegir un cerebro al azar y una categoría de su especialidad
                    selected_brain = random.choice(["MELCHOR", "GASPAR", "CASPER"])
                    category = random.choice(categories[selected_brain])
                    tag_prefix = f"@{selected_brain} "
                    
                    # Buscar artículo aleatorio en esa categoría (usar Categoría: en ES)
                    search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Categoría:{category}&cmlimit=20&format=json"
                    headers = {'User-Agent': 'MAGI-System/1.0 (raul@example.com)'}
                    r = requests.get(search_url, headers=headers, timeout=10).json()
                    
                    pages = r.get('query', {}).get('categorymembers', [])
                    if pages:
                        title = random.choice(pages).get('title')
                        # Obtener sumario de ese título
                        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
                    else:
                        # Fallback a random normal si falla la categoría
                        url = "https://es.wikipedia.org/api/rest_v1/page/random/summary"
                else:
                    # API de Wikipedia para artículo aleatorio (sumario) normal
                    url = "https://es.wikipedia.org/api/rest_v1/page/random/summary"
                
                headers = {'User-Agent': 'MAGI-System/1.0 (raul@example.com)'}
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    titulo = data.get('title', 'Sin Título')
                    extracto = data.get('extract', '')
                    
                    if extracto and len(extracto) > 50:
                        full_msg = f"{tag_prefix}{titulo.upper()}: {extracto}"
                        # Enviar al chat (esto se ejecuta en el hilo, usar Slot o QMetaObject)
                        QMetaObject.invokeMethod(self, "agregar_mensaje", 
                                               Qt.QueuedConnection,
                                               Q_ARG(str, "WIKIPEDIA"),
                                               Q_ARG(str, full_msg))
                        
                        # Entrenar cerebros (BrainManager ahora maneja el filtrado por tags si existen)
                        # Pero aquí lo forzamos si es modo inyección simple
                        contexto = f"Wikipedia: {titulo}. {extracto}"
                        if selected_brain:
                            contexto = f"@{selected_brain} " + contexto
                        
                        self.brain_manager.process_message(contexto, self.signals)
                
            except Exception as e:
                print(f"Error Wiki: {e}")
            
            # Programar siguiente fetch si sigue activo (solo si no es modo diálogo)
            if self.wiki_activo and not self.wiki_dialogo:
                intervalo = 10000 if self.wiki_identity else 1000 # Más lento en modo identidad
                QMetaObject.invokeMethod(self.wiki_timer, "start", 
                                       Qt.QueuedConnection,
                                       Q_ARG(int, intervalo))

        threading.Thread(target=job, daemon=True).start()

    def toggle_wiki_dialogue(self, state):
        """Activa o desactiva el diálogo con Wikipedia"""
        self.wiki_dialogo = (state == 2)
        if self.wiki_dialogo:
            self.lbl_wiki_dialogue_status.setText("💬 ACTIVO - Conversando")
            self.lbl_wiki_dialogue_status.setStyleSheet("color: #0ea5e9; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "💬 Diálogo Wiki ACTIVADO - MAGI conversará con Wikipedia")
            
            # Desactivar modo identidad para evitar conflictos
            if self.wiki_identity:
                self.switch_wiki_identity.setChecked(False)

            # Si el modo inyección no está activo, iniciamos el primer mensaje
            if not self.wiki_activo:
                self.wiki_activo = True # Necesario para fetch_wiki_knowledge
                QTimer.singleShot(1000, self.fetch_wiki_knowledge)
        else:
            self.lbl_wiki_dialogue_status.setText("⚫ INACTIVO")
            self.lbl_wiki_dialogue_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Diálogo Wiki DESACTIVADO")
            # Restaurar estado de wiki_activo basado en el otro switch
            self.wiki_activo = self.switch_wiki.isChecked()

    def toggle_wiki_identity(self, state):
        """Activa o desactiva la inyección por identidad especializada"""
        self.wiki_identity = (state == 2)
        if self.wiki_identity:
            self.lbl_wiki_identity_status.setText("🧬 ACTIVO - Especializado")
            self.lbl_wiki_identity_status.setStyleSheet("color: #a855f7; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "🧬 Wiki Identidad ACTIVADO - Melchor, Gaspar y Casper recibirán datos de sus áreas")
            
            # Desactivar modo diálogo para evitar conflictos
            if self.wiki_dialogo:
                self.switch_wiki_dialogue.setChecked(False)

            if not self.wiki_activo:
                self.wiki_activo = True
                QTimer.singleShot(1000, self.fetch_wiki_knowledge)
        else:
            self.lbl_wiki_identity_status.setText("⚫ INACTIVO")
            self.lbl_wiki_identity_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Wiki Identidad DESACTIVADO")
            self.wiki_activo = self.switch_wiki.isChecked()

    def enviar_mensaje(self):
        """Envía un mensaje"""
        texto = self.user_input.text().strip()
        if not texto: return
        
        self.user_input.clear()
        self.agregar_mensaje("Tu", texto)
        
        # Construir contexto para la IA
        contexto = "\n".join(self.chat_history[-4:-1]) if len(self.chat_history) > 1 else ""
        contexto += f"\nTu: {texto}"

        if self.debate_activo:
            self.debate_step(texto)
        else:
            threading.Thread(target=self.brain_manager.process_message, 
                            args=(contexto, self.signals), daemon=True).start()
    
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
        """Activa el modo de sueño para consolidación de memoria instantánea"""
        self.agregar_mensaje("SISTEMA", "💤 Iniciando consolidación neuronal instantánea...")
        # Ejecutar en segundo plano para no congelar la UI si los cerebros son grandes
        threading.Thread(target=self.brain_manager.sleep_all_brains, 
                        args=(self.signals,), daemon=True).start()
    
    def toggle_sidebar(self):
        """Muestra u oculta la barra lateral"""
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def inyectar_charter_identidad(self):
        """Inyecta la definición de las identidades de Melchor, Gaspar y Casper"""
        mensaje = (
            "📜 PROTOCOLO DE IDENTIDAD MAGI:\n\n"
            "🔴 MELCHOR (Lógica/Ciencia): Entrenado con textos técnicos, leyes y ciencia. Cerebro racional.\n"
            "🟢 GASPAR (Creatividad/Arte): Entrenado con literatura, poesía y guiones. Cerebro emocional.\n"
            "🔵 CASPER (Filosofía/Ética): Entrenado con tratados de ética y diálogos humanos. Cerebro mediador."
        )
        
        # Mostrar en chat como si viniera de Wikipedia (la fuente del conocimiento)
        self.agregar_mensaje("WIKIPEDIA", mensaje)
        
        # Hacer que todos los cerebros aprendan su propia definición
        def job():
            self.brain_manager.train_massive(mensaje, self.signals)
            # Notificar éxito
            QMetaObject.invokeMethod(self, "agregar_mensaje", 
                                   Qt.QueuedConnection,
                                   Q_ARG(str, "SISTEMA"),
                                   Q_ARG(str, "✅ Identidades consolidadas en el núcleo neuronal."))
            
        threading.Thread(target=job, daemon=True).start()
    
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
