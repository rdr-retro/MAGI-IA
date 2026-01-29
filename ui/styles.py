"""
Estilos CSS para la interfaz del sistema MAGI - Premium Edition
"""

# Paleta de colores
# Background: #0d0f17 (Very Dark Blue/Gray)
# Panel: #161923 (Dark Blue/Gray)
# Accent: #6366f1 (Indigo)
# Success: #10b981 (Emerald)
# Text: #e2e8f0 (Slate 200)
# Muted: #94a3b8 (Slate 400)

GLOBAL_STYLE = """
    QMainWindow { 
        background-color: #0d0f17; 
    }
    QWidget { 
        color: #e2e8f0; 
        font-family: 'Inter', 'Helvetica Neue', 'Arial', sans-serif;
    }
    QFrame#SidePanel { 
        background-color: #161923; 
        border-right: 1px solid #2d3748; 
    }
    
    /* Sidebar buttons */
    QPushButton#SecondaryBtn { 
        background-color: transparent; 
        border: 1px solid transparent; 
        border-radius: 8px; 
        padding: 10px; 
        color: #cbced4; 
        text-align: left;
        font-size: 13px;
    }
    QPushButton#SecondaryBtn:hover { 
        background-color: #262a38; 
        border: 1px solid #374151;
        color: white;
    }

    QLabel#StatLabel { color: #94a3b8; font-size: 11px; font-weight: 500; }
    
    QProgressBar { 
        background-color: #1f2937; 
        border: none; 
        border-radius: 4px; 
        height: 6px; 
        text-align: center; 
    }
    QProgressBar::chunk { 
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6);
        border-radius: 4px; 
    }
"""

TRAIN_BUTTON_STYLE = """
    QPushButton#TrainBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
        font-size: 13px;
        letter-spacing: 0.5px;
    }
    QPushButton#TrainBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
    }
    QPushButton#TrainBtn:pressed {
        background-color: #047857;
        margin-top: 1px;
    }
"""

SLEEP_BUTTON_STYLE = """
    QPushButton#SleepBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6d28d9);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
        font-size: 13px;
        letter-spacing: 0.5px;
    }
    QPushButton#SleepBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #7c3aed);
    }
    QPushButton#SleepBtn:pressed {
        margin-top: 1px;
    }
"""

MASSIVE_INPUT_STYLE = """
    QTextEdit {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 8px;
        padding: 10px;
        color: #e2e8f0;
        font-size: 12px;
        font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    }
    QTextEdit:focus {
        border: 1px solid #6366f1;
        background-color: #111827;
    }
"""

USER_INPUT_STYLE = """
    QFrame {
        background-color: #1f2937; 
        border: 1px solid #374151; 
        border-radius: 20px;
    }
    QFrame:hover {
        border: 1px solid #4b5563;
    }
"""

SEND_BUTTON_STYLE = """
    QPushButton { 
        background-color: #6366f1; 
        color: white; 
        border-radius: 12px; 
        font-size: 16px; 
        border: none;
    }
    QPushButton:hover {
        background-color: #818cf8;
    }
    QPushButton:pressed {
        background-color: #4f46e5;
    }
    QPushButton:disabled {
        background-color: #374151;
        color: #6b7280;
    }
"""

MIC_BUTTON_STYLE = """
    QPushButton { 
        background-color: #374151; 
        color: #e2e8f0; 
        border-radius: 12px; 
        font-size: 16px; 
        border: none;
    }
    QPushButton:hover {
        background-color: #4b5563;
        color: white;
    }
"""

MIC_BUTTON_ACTIVE_STYLE = """
    QPushButton { 
        background-color: #ef4444; 
        color: white; 
        border-radius: 12px; 
        font-size: 16px;
        border: none;
    }
    QPushButton:hover {
        background-color: #dc2626;
    }
"""

SCROLLBAR_STYLE = """
    QScrollBar:vertical { border: none; background: #0d0f17; width: 10px; margin: 0; }
    QScrollBar::handle:vertical { background: #374151; min-height: 20px; border-radius: 5px; }
    QScrollBar::handle:vertical:hover { background: #4b5563; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

CHECKBOX_STYLE = """
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 2px solid #6366f1;
        background-color: #1f2937;
    }
    QCheckBox::indicator:checked {
        background-color: #6366f1;
        border: 2px solid #6366f1;
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
    }
    QCheckBox::indicator:hover {
        border: 2px solid #818cf8;
        background-color: #374151;
    }
"""


ANONIMO_SWITCH_STYLE = """
    QCheckBox {
        color: #94a3b8;
        font-size: 11px;
        spacing: 8px;
        font-weight: 500;
    }
    QCheckBox::indicator {
        width: 40px;
        height: 20px;
        border-radius: 10px;
        background-color: #374151;
        border: 2px solid #4b5563;
    }
    QCheckBox::indicator:checked {
        background-color: #a855f7;
        border: 2px solid #a855f7;
    }
    QCheckBox::indicator:hover {
        border: 2px solid #6b7280;
    }
"""

DEBATE_SWITCH_STYLE = """
    QCheckBox {
        color: #94a3b8;
        font-size: 11px;
        spacing: 8px;
        font-weight: 500;
    }
    QCheckBox::indicator {
        width: 40px;
        height: 20px;
        border-radius: 10px;
        background-color: #374151;
        border: 2px solid #4b5563;
    }
    QCheckBox::indicator:checked {
        background-color: #f43f5e;
        border: 2px solid #f43f5e;
    }
    QCheckBox::indicator:hover {
        border: 2px solid #6b7280;
    }
"""



LOAD_BRAIN_BUTTON_STYLE = """
    QPushButton { 
        background-color: #374151; 
        color: #e2e8f0; 
        border-radius: 4px; 
        font-size: 12px; 
    }
    QPushButton:hover { background-color: #4b5563; color: white; }
"""

TOGGLE_SIDEBAR_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #94a3b8;
        border: none;
        font-size: 18px;
    }
    QPushButton:hover {
        color: white;
        background-color: #1f2937;
        border-radius: 4px;
    }
"""

