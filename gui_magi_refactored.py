"""
Sistema MAGI - Interfaz Principal Refactorizada
Versión optimizada y modular
"""
import sys
import os
import threading
import time
import re
import html

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
# Headless trainer support
from core.headless_trainer import HeadlessTrainer


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
        self.modo_separado = False # Si activo, cada cerebro responde por separado por defecto
        self.ultima_respuesta_magi = ""
        self.debate_turn = 0 # 0=Melchor, 1=Gaspar, 2=Casper
        self.chat_history = [] # Memoria a corto plazo (últimos mensajes)
        self.wiki_activo = False
        self.wiki_activo_base = False
        self.wiki_dialogo = False
        self.wiki_identity = False
        self.max_mensajes_visibles = 50 # Límite para mantener el rendimiento
        self.wiki_timer = QTimer()
        self.wiki_timer.setSingleShot(True) # Crucial: Solo dispara una vez y lo reiniciamos manualmente
        self.wiki_timer.timeout.connect(self.fetch_wiki_knowledge)
        
        # World News Mode (BBC Mundo)
        self.news_activo = False
        self.news_timer = QTimer()
        self.news_timer.setSingleShot(True)
        self.news_timer.timeout.connect(self.fetch_news_knowledge)

        # Story Mode (Cuentos)
        self.story_activo = False
        self.story_cache = [] # Cache para microrrelatos de internet
        self.story_timer = QTimer()
        self.story_timer.setSingleShot(True)
        self.story_timer.timeout.connect(self.fetch_story_knowledge)
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
        
        self.add_separator(stats_layout)
        
        self.lbl_vocab_size = QLabel("🔤 Shared Vocab: 0 chars")
        self.lbl_vocab_size.setObjectName("StatLabel")
        stats_layout.addWidget(self.lbl_vocab_size)
        
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

        btn_siesta = QPushButton("🛌 SIESTA")
        btn_siesta.setObjectName("SiestaBtn")
        # Reuse sleep style but perhaps with a slight color tweak if I had more styles, 
        # for now I'll use a custom one derived from SLEEP_BUTTON_STYLE or just use it as is.
        btn_siesta.setStyleSheet(styles.SLEEP_BUTTON_STYLE.replace("#6366f1", "#8b5cf6")) # Slightly more purple
        btn_siesta.setToolTip("Refuerza patrones fuertes sin eliminar neuronas (Modo Ligero)")
        btn_siesta.clicked.connect(self.siesta_cerebros)
        layout.addWidget(btn_siesta)
        
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
            ("🚀", "M4 GPU Massive Training\nRequires PyTorch + MPS", self.abrir_carpeta_txt_gpu, 1, 2),
            ("💻", "Launch External Terminal\nRobust Headless Mode", self.abrir_terminal_gpu, 2, 0),
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

        # SECCIÓN WORLD NEWS (BBC Mundo)
        lbl_news_title = QLabel("GLOBAL AWARENESS")
        lbl_news_title.setStyleSheet("color: #2dd4bf; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_news_title)

        self.switch_news = QCheckBox("Modo Noticias")
        self.switch_news.setStyleSheet(styles.WIKI_SWITCH_STYLE)
        self.switch_news.stateChanged.connect(self.toggle_news_mode)
        layout.addWidget(self.switch_news)

        self.lbl_news_status = QLabel("⚫ INACTIVO")
        self.lbl_news_status.setObjectName("StatLabel")
        self.lbl_news_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_news_status)

        # SECCIÓN CUENTOS
        lbl_story_title = QLabel("STORYTELLING TRAINING")
        lbl_story_title.setStyleSheet("color: #f472b6; font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_story_title)

        self.switch_story = QCheckBox("Modo Cuentos")
        self.switch_story.setStyleSheet(styles.WIKI_SWITCH_STYLE)
        self.switch_story.stateChanged.connect(self.toggle_story_mode)
        layout.addWidget(self.switch_story)

        self.lbl_story_status = QLabel("⚫ INACTIVO")
        self.lbl_story_status.setObjectName("StatLabel")
        self.lbl_story_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        layout.addWidget(self.lbl_story_status)
        
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
        
        # Botón enviar (MAGI Consensus)
        btn_enviar = QPushButton("➡️")
        btn_enviar.setFixedSize(32, 32)
        btn_enviar.setToolTip("Submit to MAGI (Consensus)")
        btn_enviar.setStyleSheet(styles.SEND_BUTTON_STYLE)
        btn_enviar.clicked.connect(self.enviar_mensaje)
        inner_input_layout.addWidget(btn_enviar)
        
        # Botón SWITCH POR SEPARADO
        self.btn_toggle_separado = QPushButton("🧬")
        self.btn_toggle_separado.setCheckable(True)
        self.btn_toggle_separado.setFixedSize(32, 32)
        self.btn_toggle_separado.setToolTip("Toggle Separate Response Mode")
        self.btn_toggle_separado.setStyleSheet(styles.MIC_BUTTON_STYLE)
        self.btn_toggle_separado.toggled.connect(self.alternar_modo_separado)
        inner_input_layout.addWidget(self.btn_toggle_separado)
        
        # Botón micrófono
        self.btn_mic = QPushButton("🎤")
        self.btn_mic.setFixedSize(32, 32)
        self.btn_mic.setStyleSheet(styles.MIC_BUTTON_STYLE)
        self.btn_mic.clicked.connect(self.alternar_escucha)
        inner_input_layout.addWidget(self.btn_mic)
        
        input_layout.addWidget(input_shadow)
        return input_container
    
    # ========== MÉTODOS DE INTERACCIÓN ==========
    
    def alternar_modo_separado(self, activo):
        """Activa o desactiva el modo de respuesta individual persistente"""
        self.modo_separado = activo
        if activo:
            self.btn_toggle_separado.setStyleSheet(styles.MIC_BUTTON_ACTIVE_STYLE.replace("#ef4444", "#a855f7")) # Púrpura para ADN
            self.lbl_notification.setText("🧬 MODO SEPARADO ACTIVADO: Cada cerebro responderá individualmente")
        else:
            self.btn_toggle_separado.setStyleSheet(styles.MIC_BUTTON_STYLE)
            self.lbl_notification.setText("🤝 MODO CONSENSO ACTIVADO: Respuesta vía MAGI")

    def enviar_mensaje(self):
        """Procesa el envío de mensaje según el modo activo"""
        texto = self.user_input.text().strip()
        if not texto: return
        
        self.agregar_mensaje("TÚ", texto)
        self.user_input.clear()
        
        # Modo Debate Secuencial (Auto-Debate)
        if hasattr(self, 'debate_activo') and self.debate_activo:
            self.debate_step(texto)
            return

        # Modo Respuesta Separada (🧬)
        if self.modo_separado:
            threading.Thread(target=self.brain_manager.process_message_separate, 
                            args=(texto, self.signals), daemon=True).start()
        else:
            # MAGI Normal (Consenso)
            threading.Thread(target=self.brain_manager.process_message, 
                            args=(texto, self.signals), daemon=True).start()

    @Slot(str, str)
    def agregar_mensaje(self, autor, mensaje):
        """Agrega un mensaje al chat y a la memoria a corto plazo"""
        is_ai = autor in ["IA", "SISTEMA", "MAGI", "MELCHOR", "GASPAR", "CASPER", "ANÓNIMO", "WIKIPEDIA", "BBC MUNDO"]
        
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
        
        # Limpiar mensajes antiguos para mantener el rendimiento
        self.limpiar_mensajes_antiguos()
    
    def limpiar_mensajes_antiguos(self):
        """Elimina los widgets de mensajes más antiguos si superan el límite"""
        if self.messages_layout.count() > self.max_mensajes_visibles + 1: # +1 por el stretch
            # El stretch es el primer elemento (index 0)
            # Los mensajes empiezan desde el index 1
            # Borramos el mensaje más antiguo (el que está en index 1)
            item = self.messages_layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
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
        
        # Actualizar vocabulario (usamos Melchor como referencia principal)
        vocab_n = len(self.brain_manager.ia_melchor.vocab)
        self.lbl_vocab_size.setText(f"🔤 Shared Vocab: {vocab_n:,} chars")
        
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
        
        vocab_n = len(self.brain_manager.ia_melchor.vocab)
        self.lbl_vocab_size.setText(f"🔤 Shared Vocab: {vocab_n:,} chars")
    
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
        """Activa/Desactiva la inyección base de Wikipedia"""
        self.wiki_activo_base = (state == 2)
        self.actualizar_estado_wiki()

    def clean_wiki_content(self, text):
        """Limpia el contenido de Wikipedia de basura visual y LaTeX"""
        if not text: return ""
        
        # 1. Eliminar bloques de fórmulas LaTeX {\displaystyle ...}
        text = re.sub(r'\{\\displaystyle.*?\}', '', text, flags=re.DOTALL)
        
        # 2. Eliminar referencias tipo [1], [23], [cita requerida]
        text = re.sub(r'\[\d+\]|\[cita\s+requerida\]', '', text)
        
        # 3. Eliminar caracteres matemáticos aislados y símbolos raros que rompen el flujo
        # Eliminamos secuencias de símbolos matemáticos que suelen venir en bloques de fórmulas mal convertidos
        text = re.sub(r'[\∂\μ\ψ\σ\¯\±\≠\≤\≥\→\∞\∫\∑\∏\√\∝\∞\∠\∧\∨\∩\∪\⊂\⊃\⊆\⊇]+', ' ', text)
        
        # 4. Eliminar bloques de código o basura técnica que empieza por {\
        text = re.sub(r'\{\\.*?\}', '', text, flags=re.DOTALL)
        
        # 5. Normalizar espacios y saltos de línea
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def _wiki_worker(self, brain_name=None):
        """Worker individual para obtener y procesar un artículo de Wikipedia"""
        # Mapeo de categorías para Wiki Identity
        categories = {
            "MELCHOR": ["Ciencia", "Tecnología", "Matemáticas", "Física", "Computación", "Astronomía", "Biología"],
            "GASPAR": ["Literatura", "Arte", "Música", "Pintura", "Cine", "Poesía", "Arquitectura", "Escultura"],
            "CASPER": ["Filosofía", "Ética", "Sociología", "Psicología", "Derecho", "Historia", "Religión", "Política"]
        }
        
        try:
            titulo_final = ""
            headers = {'User-Agent': 'MAGI-System/1.0 (raul@example.com)'}
            
            # 1. Obtener un título basado en el cerebro o aleatorio
            if brain_name and brain_name in categories:
                category = random.choice(categories[brain_name])
                search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Categoría:{category}&cmlimit=20&format=json"
                r = requests.get(search_url, headers=headers, timeout=10).json()
                pages = r.get('query', {}).get('categorymembers', [])
                if pages: titulo_final = random.choice(pages).get('title')
            
            if not titulo_final:
                # Random title fallback
                random_url = "https://es.wikipedia.org/w/api.php?action=query&list=random&rnnamespace=0&rnlimit=1&format=json"
                r = requests.get(random_url, headers=headers, timeout=10).json()
                pages = r.get('query', {}).get('random', [])
                if pages: titulo_final = pages[0].get('title')

            if not titulo_final: return

            # 2. Obtener el CONTENIDO COMPLETO
            content_url = f"https://es.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&titles={requests.utils.quote(titulo_final)}&format=json"
            r_content = requests.get(content_url, headers=headers, timeout=15).json()
            pages_data = r_content.get('query', {}).get('pages', {})
            page_id = list(pages_data.keys())[0]
            raw_text = pages_data[page_id].get('extract', '')

            full_text = self.clean_wiki_content(raw_text)

            if full_text and len(full_text) > 50:
                chunk_size = 1500
                chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
                
                # Limitar a máximo 3 bloques para no saturar si es multi-cerebro
                if brain_name: chunks = chunks[:3]
                
                info_msg = f"📚 LEYENDO ARTÍCULO COMPLETO: {titulo_final.upper()}"
                if brain_name: info_msg = f"🧬 ESPECIALIZACIÓN {brain_name}: {titulo_final.upper()}"
                
                QMetaObject.invokeMethod(self, "agregar_mensaje", 
                                       Qt.QueuedConnection,
                                       Q_ARG(str, "WIKIPEDIA"),
                                       Q_ARG(str, f"{info_msg} ({len(chunks)} bloques)"))

                for idx, chunk in enumerate(chunks):
                    if not self.wiki_activo: break
                    
                    tag = f"@{brain_name} " if brain_name else ""
                    full_msg = f"{tag}[BLOQUE {idx+1}/{len(chunks)}] {chunk}"
                    
                    QMetaObject.invokeMethod(self, "agregar_mensaje", 
                                           Qt.QueuedConnection,
                                           Q_ARG(str, "WIKIPEDIA"),
                                           Q_ARG(str, full_msg))
                    
                    contexto = f"Wikipedia: {titulo_final}. {chunk}"
                    if brain_name: contexto = f"@{brain_name} " + contexto
                    
                    self.brain_manager.process_message(contexto, self.signals)
                    time.sleep(4.0) # Pausa un poco más larga para que la IA responda bien
                
        except Exception as e:
            print(f"Error Wiki Worker ({brain_name}): {e}")

    def fetch_wiki_knowledge(self):
        """Punto de entrada para el sistema de Wikipedia"""
        if not self.wiki_activo: return
        
        def master_job():
            try:
                if self.wiki_identity:
                    # LANZAR 3 CEREBROS A LA VEZ
                    threads = []
                    for name in ["MELCHOR", "GASPAR", "CASPER"]:
                        t = threading.Thread(target=self._wiki_worker, args=(name,), daemon=True)
                        threads.append(t)
                        t.start()
                        time.sleep(2.0) # Escalonar un poco el inicio
                    
                    # Esperar a que terminen o ignorar (son daemon)
                else:
                    # Modo normal (uno solo por consenso)
                    self._wiki_worker(None)
                
            finally:
                # REPROGRAMACIÓN
                if self.wiki_activo:
                    # Intervalos más largos si son 3 a la vez
                    intervalo = 12000 if self.wiki_identity else (8000 if self.wiki_dialogo else 5000)
                    QMetaObject.invokeMethod(self.wiki_timer, "start", 
                                           Qt.QueuedConnection,
                                           Q_ARG(int, intervalo))

        threading.Thread(target=master_job, daemon=True).start()

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
        else:
            self.lbl_wiki_dialogue_status.setText("⚫ INACTIVO")
            self.lbl_wiki_dialogue_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Diálogo Wiki DESACTIVADO")
        
        self.actualizar_estado_wiki()

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
        else:
            self.lbl_wiki_identity_status.setText("⚫ INACTIVO")
            self.lbl_wiki_identity_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Wiki Identidad DESACTIVADO")
        
        self.actualizar_estado_wiki()

    def actualizar_estado_wiki(self):
        """Sincroniza el estado global de Wiki y el timer"""
        was_active = self.wiki_activo
        self.wiki_activo = self.wiki_activo_base or self.wiki_dialogo or self.wiki_identity
        
        if self.wiki_activo:
            if not was_active:
                self.agregar_mensaje("SISTEMA", "🧬 Sistema de Conocimiento Wikipedia ACTIVADO")
                self.wiki_timer.start(1000)
            
            # Actualizar labels principales si es necesario
            if self.wiki_activo_base:
                self.lbl_wiki_status.setText("🧬 ACTIVO")
                self.lbl_wiki_status.setStyleSheet("color: #a855f7; font-size: 11px; font-weight: bold;")
        else:
            self.wiki_timer.stop()
            self.lbl_wiki_status.setText("⚫ INACTIVO")
            self.lbl_wiki_status.setStyleSheet("color: #6b7280; font-size: 11px; font-style: italic;")
            if was_active:
                self.agregar_mensaje("SISTEMA", "⚫ Sistema de Conocimiento Wikipedia DESACTIVADO")

    def toggle_news_mode(self, state):
        """Activa/Desactiva el modo de noticias del mundo"""
        self.news_activo = (state == 2)
        if self.news_activo:
            self.lbl_news_status.setText("🌐 ACTIVO - BBC Mundo")
            self.lbl_news_status.setStyleSheet("color: #2dd4bf; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "🌐 World News Mode ACTIVADO (BBC Mundo - 0.5s)")
            self.news_timer.start(100)
        else:
            self.news_timer.stop()
            self.lbl_news_status.setText("⚫ INACTIVO")
            self.lbl_news_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Modo Noticias DESACTIVADO")

    def fetch_news_knowledge(self):
        """Obtiene noticias breves del mundo de BBC Mundo en español"""
        if not self.news_activo: return
        
        def job():
            try:
                url = "https://www.bbc.com/mundo/index.xml"
                headers = {'User-Agent': 'MAGI-System/1.0 (raul@example.com)'}
                r = requests.get(url, headers=headers, timeout=12)
                if r.status_code == 200:
                    content = r.text
                    items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
                    if items:
                        item = random.choice(items)
                        title_match = re.search(r'<title>(.*?)</title>', item)
                        desc_match = re.search(r'<description>(.*?)</description>', item)
                        
                        titulo = title_match.group(1) if title_match else "Noticia Global"
                        titulo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo)
                        titulo = html.unescape(titulo).strip()
                        
                        desc = desc_match.group(1) if desc_match else ""
                        desc = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', desc)
                        desc = re.sub(r'<[^>]+>', '', desc)
                        desc = html.unescape(desc).strip()
                        
                        full_msg = f"{titulo.upper()}\n{desc}"
                        
                        QMetaObject.invokeMethod(self, "agregar_mensaje", 
                                               Qt.QueuedConnection,
                                               Q_ARG(str, "BBC MUNDO"),
                                               Q_ARG(str, full_msg))
                        
                        contexto = f"Actualidad Mundial: {titulo}. {desc}"
                        for brain in ["@MELCHOR", "@GASPAR", "@CASPER"]:
                            msg = f"{brain} {contexto}"
                            self.brain_manager.process_message(msg, self.signals)
                            time.sleep(0.05)
                
            except Exception as e:
                print(f"Error BBC News: {e}")
            
            finally:
                if self.news_activo:
                    # Velocidad MÁXIMA: 0.5 segundos
                    intervalo = 500 if 'item' in locals() else 500
                    QMetaObject.invokeMethod(self.news_timer, "start", 
                                           Qt.QueuedConnection,
                                           Q_ARG(int, intervalo))

        threading.Thread(target=job, daemon=True).start()

    def toggle_story_mode(self, state):
        """Activa/Desactiva el modo de cuentos rápidos"""
        self.story_activo = (state == 2)
        if self.story_activo:
            self.lbl_story_status.setText("📖 ACTIVO - Leyendo")
            self.lbl_story_status.setStyleSheet("color: #f472b6; font-size: 11px; font-weight: bold;")
            self.agregar_mensaje("SISTEMA", "📖 Modo Cuentos ACTIVADO (Lectura cada segundo)")
            self.story_timer.start(100)
        else:
            self.story_timer.stop()
            self.lbl_story_status.setText("⚫ INACTIVO")
            self.lbl_story_status.setStyleSheet("color: #6b7280; font-size: 9px; font-style: italic;")
            self.agregar_mensaje("SISTEMA", "⚫ Modo Cuentos DESACTIVADO")

    def fetch_story_knowledge(self):
        """Obtiene microrrelatos de internet (RSS) para entrenamiento creativo"""
        if not self.story_activo: return
        
        # Si la cache está vacía, reponerla en un hilo
        if not self.story_cache:
            def refill_cache():
                urls = [
                    "https://www.relatos-cortos.es/feed/",
                    "https://mundorelatos.wordpress.com/feed/",
                    "https://www.senorbreve.com/feed/"
                ]
                new_stories = []
                headers = {'User-Agent': 'MAGI-System/1.0 (raul@example.com)'}
                
                for url in urls:
                    try:
                        r = requests.get(url, headers=headers, timeout=10)
                        if r.status_code == 200:
                            content = r.text
                            items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
                            for item in items:
                                title_match = re.search(r'<title>(.*?)</title>', item)
                                desc_match = re.search(r'<description>(.*?)</description>', item) or \
                                             re.search(r'<content:encoded>(.*?)</content:encoded>', item, re.DOTALL)
                                
                                titulo = title_match.group(1) if title_match else ""
                                titulo = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', titulo)
                                titulo = html.unescape(titulo).strip()
                                
                                desc = desc_match.group(1) if desc_match else ""
                                desc = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', desc)
                                desc = re.sub(r'<[^>]+>', '', desc) # Limpiar HTML
                                desc = html.unescape(desc).strip()
                                
                                if len(desc) > 20: # Evitar vacíos o muy cortos
                                    # Limitar longitud para lectura rápida
                                    snippet = desc[:500] + "..." if len(desc) > 500 else desc
                                    new_stories.append(f"{titulo.upper()}\n{snippet}")
                        
                        if new_stories: break # Con uno que funcione vale
                    except Exception as e:
                        print(f"Error fetching RSS {url}: {e}")
                
                if new_stories:
                    random.shuffle(new_stories)
                    self.story_cache.extend(new_stories)
                    # Una vez llena, procesar el primer elemento
                    QMetaObject.invokeMethod(self, "_process_next_story", Qt.QueuedConnection)
                else:
                    # Fallback si falla internet
                    fallbacks = [
                        "En un rincón del código, una variable soñaba con ser constante.",
                        "El silicio no olvida, solo archiva el silencio.",
                        "La red es un laberinto donde la información busca su salida."
                    ]
                    self.story_cache.extend(fallbacks)
                    QMetaObject.invokeMethod(self, "_process_next_story", Qt.QueuedConnection)

            threading.Thread(target=refill_cache, daemon=True).start()
            return

        # Si hay cache, procesar directamente
        self._process_next_story()

    @Slot()
    def _process_next_story(self):
        """Procesa el siguiente cuento de la cache"""
        if not self.story_activo or not self.story_cache:
            return

        story = self.story_cache.pop(0)
        
        def job():
            try:
                QMetaObject.invokeMethod(self, "agregar_mensaje", 
                                       Qt.QueuedConnection,
                                       Q_ARG(str, "CUENTACUENTOS"),
                                       Q_ARG(str, story))
                
                contexto = f"Microrrelato de internet: {story}"
                for brain in ["@MELCHOR", "@GASPAR", "@CASPER"]:
                    msg = f"{brain} Analiza la narrativa de este cuento: {contexto}"
                    self.brain_manager.process_message(msg, self.signals)
                    time.sleep(0.05)
                
            except Exception as e:
                print(f"Error Story Mode Job: {e}")
            
            finally:
                if self.story_activo:
                    # Velocidad: 1 segundo
                    QMetaObject.invokeMethod(self.story_timer, "start", 
                                           Qt.QueuedConnection,
                                           Q_ARG(int, 1000))

        threading.Thread(target=job, daemon=True).start()

    
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

    def siesta_cerebros(self):
        """Activa el modo de siesta para refuerzo suave"""
        self.agregar_mensaje("SISTEMA", "🛌 Iniciando siesta reparadora (refuerzo sin poda)...")
        threading.Thread(target=self.brain_manager.siesta_all_brains, 
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
    
    def abrir_carpeta_txt_gpu(self):
        """Abre una carpeta de archivos TXT para entrenamiento GPU Masivo en modo Headless"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for Massive GPU Training", "/")
        if folder:
            self.agregar_mensaje("SISTEMA", "🖥️ SWITCHING TO HEADLESS TERMINAL MODE...")
            
            # Lanzar en modo headless
            def run_headless():
                trainer = HeadlessTrainer(self.brain_manager)
                # Ocultar ventana principal
                self.hide()
                # Ejecutar trabajo (bloqueante hasta que termine el hilo interno del trainer o ESC)
                trainer.run_job(self.brain_manager.train_from_text_folder_gpu, folder_path=folder)
                # Mostrar ventana al volver
                self.show()
                self.agregar_mensaje("SISTEMA", "✅ Training session ended. Welcome back.")
                self.barra_progreso.setValue(100)

            # Ejecutar esto en un hilo separado para no congelar la GUI antes de ocultarse?
            # No, queremos que bloquee la GUI ("hide" lo hace visualmente) pero necesitamos
            # que el main thread quede libre si fuera GUI, pero aqui queremos tomar la terminal.
            # Al usar 'self.hide()', la ventana se va. Podemos usar un hilo para lanzar el trainer
            # pero el trainer usa input() y prints, así que mejor correrlo "aquí" pero 
            # necesitamos asegurarnos que Qt no interfiera con stdin.
            
            # Mejor estrategia: Un QTimer o threading.
            # Si corremos en MainThread, Qt bloqueará eventos pero eso está bien si la ventana está oculta.
            # Sin embargo, 'run_job' tiene un loop de input.
            
            
            threading.Thread(target=run_headless, daemon=False).start()

    def abrir_terminal_gpu(self):
        """Lanza el entrenamiento en una ventana de Terminal externa (Más robusto)"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for Terminal Training", "/")
        if not folder: return

        import subprocess
        
        # Ruta al script y al intérprete actual
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal_train.py")
        python_exe = sys.executable
        
        # Comando de Shell: "python" "script" "folder"
        # Importante: Envolver todo en comillas dobles para el Shell
        cmd_str = f'"{python_exe}" "{script_path}" "{folder}"'
        
        # Escapar comillas dobles y barras invertidas para AppleScript
        # AppleScript usa comillas dobles para strings. Si hay comillas dentro, deben ser \"
        # Y las barras invertidas deben ser \\
        cmd_str_applescript = cmd_str.replace('\\', '\\\\').replace('"', '\\"')
        
        # AppleScript para abrir Terminal y ejecutar
        # activate: trae al frente
        # do script: ejecuta el comando en una ventana nueva
        apple_script = f'''
        tell application "Terminal"
            activate
            do script "{cmd_str_applescript}"
        end tell
        '''
        
        try:
            subprocess.run(["osascript", "-e", apple_script], check=True, capture_output=True, text=True)
            self.agregar_mensaje("SISTEMA", "🚀 Launched External Terminal. Check the new window!")
        except subprocess.CalledProcessError as e:
            self.agregar_mensaje("SISTEMA", f"❌ Error launching terminal: {e.stderr}")
        except Exception as e:
            self.agregar_mensaje("SISTEMA", f"❌ Error launching terminal: {str(e)}")
    
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
