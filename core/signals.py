"""
Señales para comunicación entre hilos en el sistema MAGI
"""
from PySide6.QtCore import QObject, Signal


class IAWorkerSignals(QObject):
    """Señales para comunicación entre el worker de IA y la GUI"""
    respuesta_lista = Signal(str, str)  # autor, mensaje
    stats_actualizadas = Signal(int, float)  # neuronas (melchor), peso_mb (total)
    voto_magi = Signal(str, bool)  # nombre_cerebro, voto
    error_ocurrido = Signal(str)
    entrenamiento_terminado = Signal()
    cerebro_expandido = Signal(str, int)  # nombre, neuronas
    progreso_entrenamiento = Signal(int)  # porcentaje
    texto_transcrito = Signal(str)  # Para cargar en el massive_input
    pensando = Signal(bool)  # True para mostrar, False para ocultar
