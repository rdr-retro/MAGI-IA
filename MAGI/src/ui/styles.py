"""
Estilos CSS para la interfaz del sistema MAGI
"""

# Estilo global de la aplicación
GLOBAL_STYLE = """
    QMainWindow { background-color: #343541; }
    QWidget { color: #ececf1; font-family: 'Arial', Arial; }
    QFrame#SidePanel { background-color: #202123; border: none; }
    
    /* Sidebar buttons */
    QPushButton#SecondaryBtn { 
        background-color: transparent; 
        border: none; 
        border-radius: 4px; 
        padding: 8px; 
        color: #ececf1; 
        text-align: left;
        font-size: 12px;
    }
    QPushButton#SecondaryBtn:hover { background-color: #3f404d; }

    QLabel#StatLabel { color: #8e8ea0; font-size: 10px; }
    QProgressBar { background-color: #202123; border: 1px solid #4d4d4f; border-radius: 3px; height: 5px; text-align: center; }
    QProgressBar::chunk { background-color: #10a37f; }
"""

# Estilo del botón de entrenamiento
TRAIN_BUTTON_STYLE = """
    QPushButton#TrainBtn {
        background-color: #10a37f;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px;
        font-weight: bold;
        font-size: 12px;
    }
    QPushButton#TrainBtn:hover {
        background-color: #0d8c6f;
    }
    QPushButton#TrainBtn:pressed {
        background-color: #0a7a5e;
    }
"""

# Estilo del botón de sueño (consolidación de memoria)
SLEEP_BUTTON_STYLE = """
    QPushButton#SleepBtn {
        background-color: #7c3aed;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px;
        font-weight: bold;
        font-size: 12px;
    }
    QPushButton#SleepBtn:hover {
        background-color: #6d28d9;
    }
    QPushButton#SleepBtn:pressed {
        background-color: #5b21b6;
    }
"""

# Estilo del área de texto masivo
MASSIVE_INPUT_STYLE = """
    QTextEdit {
        background-color: #2a2b32;
        border: 1px solid #3e3f4b;
        border-radius: 5px;
        padding: 6px;
        color: #d1d5db;
        font-size: 11px;
        font-family: 'Menlo', 'Monaco', monospace;
    }
"""

# Estilo del input del usuario
USER_INPUT_STYLE = """
    background-color: #40414f; 
    border: 1px solid #565869; 
    border-radius: 12px;
"""

# Estilo del botón de enviar
SEND_BUTTON_STYLE = """
    QPushButton { 
        background-color: #10a37f; 
        color: white; 
        border-radius: 6px; 
        font-size: 16px; 
    }
    QPushButton:disabled {
        background-color: #2b2c2f;
        color: #8e8ea0;
    }
"""

# Estilo del botón de micrófono
MIC_BUTTON_STYLE = """
    QPushButton { 
        background-color: #3e3f4b; 
        color: white; 
        border-radius: 6px; 
        font-size: 16px; 
    }
    QPushButton:hover {
        background-color: #4d4d4f;
    }
"""

# Estilo del botón de micrófono activo
MIC_BUTTON_ACTIVE_STYLE = "background-color: #ef4444; color: white; border-radius: 6px; font-size: 16px;"

# Estilo del scrollbar
SCROLLBAR_STYLE = """
    QScrollBar:vertical { border: none; background: #343541; width: 8px; margin: 0; }
    QScrollBar::handle:vertical { background: #565869; min-height: 20px; border-radius: 4px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

# Estilo de los checkboxes de cerebros
CHECKBOX_STYLE = """
    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border-radius: 2px;
        border: 2px solid #10a37f;
        background-color: #202123;
    }
    QCheckBox::indicator:checked {
        background-color: #10a37f;
        border: 2px solid #10a37f;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
    }
    QCheckBox::indicator:hover {
        border: 2px solid #0d8c6f;
    }
"""

# Estilo del switch del votante anónimo
ANONIMO_SWITCH_STYLE = """
    QCheckBox {
        color: #8e8ea0;
        font-size: 10px;
        spacing: 6px;
    }
    QCheckBox::indicator {
        width: 36px;
        height: 18px;
        border-radius: 9px;
        background-color: #3e3f4b;
        border: 2px solid #565869;
    }
    QCheckBox::indicator:checked {
        background-color: #a855f7;
        border: 2px solid #a855f7;
    }
    QCheckBox::indicator:hover {
        border: 2px solid #8e8ea0;
    }
"""

# Estilo del botón de carga de cerebro
LOAD_BRAIN_BUTTON_STYLE = """
    QPushButton { 
        background-color: #3e3f4b; 
        color: white; 
        border-radius: 3px; 
        font-size: 11px; 
    }
    QPushButton:hover { background-color: #4d4d4f; }
"""
