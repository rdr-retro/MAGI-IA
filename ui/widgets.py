"""
Widgets personalizados para la interfaz MAGI - Premium Edition
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class MessageWidget(QWidget):
    """Widget para mostrar mensajes en el chat con alineación lateral"""
    
    def __init__(self, author, text, is_ai=False):
        super().__init__()
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Reconocer si es un mensaje de estadísticas
        is_stats = author == "ESTADÍSTICAS"
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(50, 10, 50, 10)
        self.main_layout.setSpacing(0)
        
        # Contenedor de la burbuja
        self.bubble = QFrame()
        self.bubble_layout = QHBoxLayout(self.bubble)
        self.bubble_layout.setContentsMargins(15, 12, 15, 12)
        self.bubble_layout.setSpacing(15)
        
        # Estilizacion según autor
        if is_ai or is_stats:
            bg_color = "#1f2937"
            self.bubble.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px; border-bottom-left-radius: 2px;")
            self.main_layout.addWidget(self.bubble)
            self.main_layout.addStretch()
        else:
            bg_color = "#312e81" # Indigo profundo para el usuario
            self.bubble.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px; border-bottom-right-radius: 2px;")
            self.main_layout.addStretch()
            self.main_layout.addWidget(self.bubble)

        # Avatar
        avatar_label = QLabel()
        avatar_label.setFixedSize(32, 32)
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setFont(QFont("Inter", 10, QFont.Bold))
        
        is_mic_message = "🎤" in text or "Transcrito:" in text or "Micrófono" in text or author == "MIC"
        
        if is_ai or is_stats:
            if is_stats:
                avatar_label.setText("🌟")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #f59e0b; color: white;") 
            elif author == "MELCHOR":
                avatar_label.setText("ME")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #ef4444; color: white;")
            elif author == "GASPAR":
                avatar_label.setText("GA")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #10b981; color: white;")
            elif author == "CASPER":
                avatar_label.setText("CA")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #6366f1; color: white;")
            elif author == "WIKIPEDIA":
                avatar_label.setText("W")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #0ea5e9; color: white;")
            elif is_mic_message:
                avatar_label.setText("MI")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #3b82f6; color: white;")
            elif author == "ANÓNIMO":
                avatar_label.setText("??")
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #a855f7; color: white;")
            else:
                avatar_label.setText("AI") 
                avatar_label.setStyleSheet("border-radius: 6px; background-color: #10b981; color: white;")
            self.bubble_layout.addWidget(avatar_label, alignment=Qt.AlignTop)
        else:
            avatar_label.setText("UL")
            avatar_label.setStyleSheet("border-radius: 6px; background-color: #6366f1; color: white;")
        
        # Texto
        text_container = QVBoxLayout()
        author_label = QLabel(author.upper())
        
        # Selección de color de acento por autor
        if is_stats: accent = '#f59e0b'
        elif author == "MELCHOR": accent = '#ef4444'
        elif author == "GASPAR": accent = '#10b981'
        elif author == "CASPER": accent = '#6366f1'
        elif author == "WIKIPEDIA": accent = '#0ea5e9'
        elif is_ai: accent = '#10b981'
        else: accent = '#a5b4fc'
        
        author_label.setStyleSheet(f"color: {accent}; font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        text_container.addWidget(author_label)
        
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.text_label.setFont(QFont("Inter", 11))
        self.text_label.setStyleSheet("color: #f1f5f9; background: transparent; line-height: 1.4;")
        text_container.addWidget(self.text_label)
        
        self.bubble_layout.addLayout(text_container, 1)
        
        if not is_ai and not is_stats:
            self.bubble_layout.addWidget(avatar_label, alignment=Qt.AlignTop)


class ThinkingWidget(QWidget):
    """Widget animado de deliberación alineado a la izquierda"""
    
    def __init__(self):
        super().__init__()
        from PySide6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(80) # Altura fija para el widget de pensamiento para evitar saltos
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(50, 10, 50, 10)
        
        self.bubble = QFrame()
        self.bubble.setStyleSheet("background-color: #1f2937; border-radius: 12px; border-bottom-left-radius: 2px;")
        self.bubble_layout = QHBoxLayout(self.bubble)
        self.bubble_layout.setContentsMargins(15, 12, 15, 12)
        self.bubble_layout.setSpacing(15)
        
        # Avatar
        avatar_label = QLabel("AI")
        avatar_label.setFixedSize(32, 32)
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setFont(QFont("Inter", 10, QFont.Bold))
        avatar_label.setStyleSheet("border-radius: 6px; background-color: #10b981; color: white;")
        self.bubble_layout.addWidget(avatar_label, alignment=Qt.AlignTop)
        
        # Animación
        content_layout = QVBoxLayout()
        author_label = QLabel("MAGI")
        author_label.setStyleSheet("color: #10b981; font-size: 9px; font-weight: bold; letter-spacing: 1px;")
        content_layout.addWidget(author_label)
        
        anim_layout = QHBoxLayout()
        self.thinking_label = QLabel("Deliberando")
        self.thinking_label.setFont(QFont("Inter", 11))
        self.thinking_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        anim_layout.addWidget(self.thinking_label)
        
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet("color: #10b981; font-size: 10px;")
            self.dots.append(dot)
            anim_layout.addWidget(dot)
        anim_layout.addStretch()
        content_layout.addLayout(anim_layout)
        
        self.bubble_layout.addLayout(content_layout)
        self.main_layout.addWidget(self.bubble)
        self.main_layout.addStretch()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_dots)
        self.current_dot = 0
        self.timer.start(400)

    def animate_dots(self):
        for i, dot in enumerate(self.dots):
            dot.setStyleSheet(f"color: {'#10b981' if i == self.current_dot else '#374151'}; font-size: 10px;")
        self.current_dot = (self.current_dot + 1) % 3
    
    def stop_animation(self):
        if hasattr(self, 'timer'): self.timer.stop()
