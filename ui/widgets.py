"""
Widgets personalizados para la interfaz MAGI
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont


class MessageWidget(QWidget):
    """Widget para mostrar mensajes en el chat"""
    
    def __init__(self, author, text, is_ai=False):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(80, 16, 80, 16)
        self.layout.setSpacing(12)
        
        # COLORES SEGÚN LA NUEVA IMAGEN
        # Usuario: Gris azulado (#343541)
        # IA: Gris oscuro (#444654)
        bg_color = "#444654" if is_ai else "#343541"
        self.setStyleSheet(f"background-color: {bg_color}; border: none;")
        
        # Avatar
        avatar_label = QLabel()
        avatar_label.setFixedSize(28, 28)
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setFont(QFont("Arial", 9, QFont.Bold))
        
        # Detectar si es un mensaje de micrófono/transcripción
        is_mic_message = "🎤" in text or "Transcrito:" in text or "Micrófono" in text or author == "MIC"
        
        if is_ai:
            if is_mic_message:
                avatar_label.setText("MI")  # MI para mensajes de micrófono
                avatar_label.setStyleSheet("border-radius: 2px; background-color: #3b82f6; color: white;")  # Azul para micrófono
            elif author == "ANÓNIMO":
                avatar_label.setText("??")  # ?? para votante anónimo
                avatar_label.setStyleSheet("border-radius: 2px; background-color: #a855f7; color: white;")  # Púrpura para anónimo
            else:
                avatar_label.setText("AI") 
                avatar_label.setStyleSheet("border-radius: 2px; background-color: #10a37f; color: white;")
        else:
            avatar_label.setText("UL") # 'UL' como en la imagen
            # Púrpura/Rosa para el usuario como en la nueva imagen
            avatar_label.setStyleSheet("border-radius: 2px; background-color: #8e44ad; color: white;")
        
        self.layout.addWidget(avatar_label, alignment=Qt.AlignTop)
        
        # Text Message
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.text_label.setFont(QFont("Arial", 10))
        self.text_label.setStyleSheet("color: #d1d5db; background: transparent; line-height: 1.5;")
        self.layout.addWidget(self.text_label, 1)
        
        # Removed feedback icons as requested
        if not is_ai:
            self.layout.addSpacing(60)


class ThinkingWidget(QWidget):
    """Widget animado que muestra cuando MAGI está deliberando"""
    
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(80, 16, 80, 16)
        self.layout.setSpacing(12)
        
        # Fondo similar a mensajes de IA
        self.setStyleSheet("background-color: #444654; border: none;")
        
        # Avatar
        avatar_label = QLabel()
        avatar_label.setFixedSize(28, 28)
        avatar_label.setAlignment(Qt.AlignCenter)
        avatar_label.setFont(QFont("Arial", 9, QFont.Bold))
        avatar_label.setText("AI")
        avatar_label.setStyleSheet("border-radius: 2px; background-color: #10a37f; color: white;")
        self.layout.addWidget(avatar_label, alignment=Qt.AlignTop)
        
        # Contenedor de animación
        anim_container = QWidget()
        anim_layout = QHBoxLayout(anim_container)
        anim_layout.setContentsMargins(0, 0, 0, 0)
        anim_layout.setSpacing(8)
        
        # Texto de deliberación
        self.thinking_label = QLabel("MAGI deliberando")
        self.thinking_label.setFont(QFont("Arial", 10))
        self.thinking_label.setStyleSheet("color: #10a37f; background: transparent;")
        anim_layout.addWidget(self.thinking_label)
        
        # Puntos animados
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setFont(QFont("Arial", 14))
            dot.setStyleSheet("color: #10a37f; background: transparent;")
            self.dots.append(dot)
            anim_layout.addWidget(dot)
        
        anim_layout.addStretch()
        self.layout.addWidget(anim_container, 1)
        
        # Animación de los puntos
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_dots)
        self.current_dot = 0
        self.timer.start(400)  # Cambiar cada 400ms

    def animate_dots(self):
        """Anima los puntos de pensamiento"""
        for i, dot in enumerate(self.dots):
            if i == self.current_dot:
                dot.setStyleSheet("color: #10a37f; background: transparent; font-weight: bold;")
            else:
                dot.setStyleSheet("color: #565869; background: transparent;")
        
        self.current_dot = (self.current_dot + 1) % 3
    
    def stop_animation(self):
        """Detiene la animación"""
        if hasattr(self, 'timer'):
            self.timer.stop()
