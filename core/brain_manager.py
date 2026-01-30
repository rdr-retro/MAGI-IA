"""
Gestor de Cerebros MAGI
Maneja la lógica de los tres cerebros y el votante anónimo
"""
import os
import time
import numpy as np
import fitz
import whisper
import torch

from chat_interactivo import RedCrecimientoInfinito


class BrainManager:
    """Gestiona los tres cerebros MAGI y sus operaciones"""
    
    def __init__(self):
        self.archivo_melchor = "melchor.safetensors"
        self.archivo_gaspar = "gaspar.safetensors"
        self.archivo_casper = "casper.safetensors"
        
        # Cargar o crear cerebros
        self._load_brains()
        
        # Estado de activación
        self.melchor_activo = True
        self.gaspar_activo = True
        self.casper_activo = True
        self.votante_anonimo_activo = False
    
    def _load_brains(self):
        """Carga o crea los cerebros (soporte migración pkl -> safetensors)"""
        vocab_default = " abcdefghijklmnopqrstuvwxyzáéíóúñ,.¿?¡!0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ:;-_()[]{}\"'/@#$%&*+=\n\t"
        
        def cargar_o_crear(path_safetensors):
            # 1. Intentar cargar versión nueva (.safetensors)
            if os.path.exists(path_safetensors):
                try:
                    return RedCrecimientoInfinito.cargar(path_safetensors)
                except Exception as e:
                    print(f"Error cargando {path_safetensors}: {e}. Creando nuevo.")
                    return RedCrecimientoInfinito(vocabulario=vocab_default, n_oculta=128)
            
            # 2. Intentar migrar desde versión vieja (.pkl)
            path_pkl = path_safetensors.replace('.safetensors', '.pkl')
            if os.path.exists(path_pkl):
                try:
                    print(f"🔄 Migrando {path_pkl} a formato Safetensors...")
                    cerebro = RedCrecimientoInfinito.cargar(path_pkl)
                    # Guardar inmediatamente en nuevo formato
                    cerebro.guardar(path_safetensors)
                    return cerebro
                except Exception as e:
                    print(f"Error migrando {path_pkl}: {e}.")
                    return RedCrecimientoInfinito(vocabulario=vocab_default, n_oculta=128)
            
            # 3. Crear nuevo si no existe ninguno
            return RedCrecimientoInfinito(vocabulario=vocab_default, n_oculta=128)
        
        self.ia_melchor = cargar_o_crear(self.archivo_melchor)
        self.ia_gaspar = cargar_o_crear(self.archivo_gaspar)
        self.ia_casper = cargar_o_crear(self.archivo_casper)
    
    def set_expansion_callbacks(self, melchor=None, gaspar=None, casper=None):
        """Configura callbacks de expansión"""
        if melchor:
            self.ia_melchor.on_expand = melchor
        if gaspar:
            self.ia_gaspar.on_expand = gaspar
        if casper:
            self.ia_casper.on_expand = casper
    
    def toggle_brain(self, brain_name, active):
        """Activa o desactiva un cerebro"""
        if brain_name == "melchor":
            self.melchor_activo = active
        elif brain_name == "gaspar":
            self.gaspar_activo = active
        elif brain_name == "casper":
            self.casper_activo = active
    
    def get_active_brains(self):
        """Retorna lista de cerebros activos (ia, archivo, nombre)"""
        brains = []
        if self.melchor_activo:
            brains.append((self.ia_melchor, self.archivo_melchor, "MELCHOR"))
        if self.gaspar_activo:
            brains.append((self.ia_gaspar, self.archivo_gaspar, "GASPAR"))
        if self.casper_activo:
            brains.append((self.ia_casper, self.archivo_casper, "CASPER"))
        return brains
    
    
    def get_total_size_mb(self):
        """Calcula el tamaño total en MB"""
        peso = 0
        for f in [self.archivo_melchor, self.archivo_gaspar, self.archivo_casper]:
            if os.path.exists(f):
                peso += os.path.getsize(f) / (1024 * 1024)
        return peso
    
    def sleep_all_brains(self, signals, umbral_poda=0.01, factor_refuerzo=1.1):
        """Hace que todos los cerebros activos entren en fase de sueño"""
        try:
            cerebros_activos = self.get_active_brains()
            
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos para dormir")
                return
            
            nombres = [nombre for _, _, nombre in cerebros_activos]
            signals.respuesta_lista.emit("SISTEMA", f"💤 Iniciando fase de sueño para: {', '.join(nombres)}")
            
            resultados_totales = {
                'podadas': 0,
                'reforzadas': 0,
                'activas': 0
            }
            
            for ia, path, nombre in cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", f"💤 {nombre} entrando en sueño profundo...")
                
                # Ejecutar consolidación de memoria
                resultado = ia.dormir(umbral_poda=umbral_poda, factor_refuerzo=factor_refuerzo)
                
                # Acumular resultados
                resultados_totales['podadas'] += resultado['podadas']
                resultados_totales['reforzadas'] += resultado['reforzadas']
                resultados_totales['activas'] += resultado['activas']
                
                # Guardar cerebro después del sueño
                ia.guardar(path)
                
                signals.respuesta_lista.emit("ESTADÍSTICAS", 
                    f"   └─ {nombre}: {resultado['podadas']:,} podadas, {resultado['reforzadas']:,} reforzadas")
            
            # Resumen final
            signals.respuesta_lista.emit("ESTADÍSTICAS", 
                f"✨ Sueño completado - Total: {resultados_totales['podadas']:,} conexiones eliminadas, "
                f"{resultados_totales['reforzadas']:,} reforzadas, {resultados_totales['activas']:,} activas")
            
            # Actualizar estadísticas
            peso = self.get_total_size_mb()
            signals.stats_actualizadas.emit(0, peso)
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ Error durante el sueño: {str(e)}")

    def siesta_all_brains(self, signals, factor_refuerzo=1.05):
        """Hace que todos los cerebros activos entren en fase de siesta (sin poda)"""
        try:
            cerebros_activos = self.get_active_brains()
            
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos para la siesta")
                return
            
            nombres = [nombre for _, _, nombre in cerebros_activos]
            signals.respuesta_lista.emit("SISTEMA", f"🛌 Iniciando siesta reparadora para: {', '.join(nombres)}")
            
            resultados_totales = {
                'reforzadas': 0,
                'activas': 0
            }
            
            for ia, path, nombre in cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", f"🛌 {nombre} tomando una siesta...")
                resultado = ia.siesta(factor_refuerzo=factor_refuerzo)
                
                # Acumular resultados
                resultados_totales['reforzadas'] += resultado['reforzadas']
                resultados_totales['activas'] += resultado['activas']
                
                # Guardar cerebro
                ia.guardar(path)
                
                signals.respuesta_lista.emit("ESTADÍSTICAS", 
                    f"   └─ {nombre}: {resultado['reforzadas']:,} reforzadas, 0 podadas")
            
            # Resumen final
            signals.respuesta_lista.emit("ESTADÍSTICAS", 
                f"✨ Siesta terminada - Total: {resultados_totales['reforzadas']:,} conexiones reforzadas. "
                f"El conocimiento ha sido organizado.")
            
            # Actualizar estadísticas
            peso = self.get_total_size_mb()
            signals.stats_actualizadas.emit(0, peso)
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ Error durante la siesta: {str(e)}")
    
    def evaluar_texto(self, ia, texto):
        """Evalúa la confianza de un cerebro en un texto"""
        if not texto:
            return 0
        indices = [ia.char_to_int[c] for c in texto if c in ia.char_to_int]
        if len(indices) < 2:
            return 0.5
        
        probs = []
        for i in range(len(indices)-1):
            pred = ia.forward([indices[i]])
            probs.append(pred[0, indices[i+1]])
        return np.mean(probs) if probs else 0
    
    def process_message(self, texto, signals):
        """Procesa un mensaje del usuario con soporte para etiquetas @"""
        # Detectar etiquetas prioritarias en la última línea (el mensaje actual)
        lineas = [l for l in texto.split('\n') if l.strip()]
        ultima_linea = lineas[-1].lower() if lineas else texto.lower()
        
        tags = []
        if "@melchor" in ultima_linea: tags.append("MELCHOR")
        if "@gaspar" in ultima_linea: tags.append("GASPAR")
        if "@casper" in ultima_linea: tags.append("CASPER")
        
        # Fallback: si no hay en la última línea, buscar en todo (para inyecciones de Wiki/Sistema)
        if not tags:
            if "@melchor" in texto.lower(): tags.append("MELCHOR")
            if "@gaspar" in texto.lower(): tags.append("GASPAR")
            if "@casper" in texto.lower(): tags.append("CASPER")
        
        # Limpiar etiquetas del texto de forma insensible a mayúsculas
        texto_limpio = texto
        import re
        for tag in ["@melchor", "@gaspar", "@casper"]:
            texto_limpio = re.sub(re.escape(tag), "", texto_limpio, flags=re.IGNORECASE).strip()

        # Mostrar animación de pensamiento
        signals.pensando.emit(True)
        
        # Filtrar cerebros activos que deben responder
        brains_to_respond = []
        activos = self.get_active_brains()
        
        if tags:
            # Solo los cerebros etiquetados que estén activos
            brains_to_respond = [b for b in activos if b[2] in tags]
            if not brains_to_respond:
                signals.pensando.emit(False)
                signals.respuesta_lista.emit("SISTEMA", f"⚠️ Los cerebros {', '.join(tags)} no están activos.")
                return
        else:
            # Si no hay tags, todos los activos participan (comportamiento normal)
            brains_to_respond = activos

        if not brains_to_respond:
            signals.pensando.emit(False)
            signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos para responder.")
            return

        max_intentos = 3
        propuestas = []
        
        # Si solo hay un cerebro objetivo, no hay votación, responde él directamente
        if len(brains_to_respond) == 1:
            ia, path, nombre = brains_to_respond[0]
            # Usar parámetros optimizados
            respuesta_final = ia.generar_respuesta(texto_limpio, temperatura=0.75, top_p=0.85, penalty=1.3)
            signals.pensando.emit(False)
            signals.respuesta_lista.emit(nombre, respuesta_final)
            
            # Solo aprende el cerebro objetivo
            ia.aprender(texto_limpio)
            ia.aprender(respuesta_final, epocas=1)
            ia.guardar(path)
            return

        # Si hay varios, generamos propuestas de cada uno y evaluamos
        signals.respuesta_lista.emit("SISTEMA", f"🤝 MAGI iniciando debate entre {len(brains_to_respond)} cerebros...")
        
        for ia, path, nombre in brains_to_respond:
            propuesta = ia.generar_respuesta(texto_limpio, temperatura=0.8, top_p=0.9)
            # Evaluar propuesta con todos los cerebros involucrados
            confianzas = []
            for ia_eval, _, _ in brains_to_respond:
                confianzas.append(self.evaluar_texto(ia_eval, propuesta))
            
            confianza_media = np.mean(confianzas)
            propuestas.append({
                'texto': propuesta,
                'nombre': nombre,
                'confianza': confianza_media
            })
            time.sleep(0.1)

        # Elegir la mejor propuesta
        propuestas.sort(key=lambda x: x['confianza'], reverse=True)
        mejor = propuestas[0]
        respuesta_final = mejor['texto']
        
        # Determinar nivel de consenso
        consenso = "UNANIMIDAD" if mejor['confianza'] > 0.15 else "CONSENSO"
        if mejor['confianza'] < 0.05: consenso = "DIVERGENCIA (Mejor opción)"

        signals.pensando.emit(False)
        nombres_votos = [b[2] for b in brains_to_respond]
        if self.votante_anonimo_activo and not tags: nombres_votos.append("ANÓNIMO")
        
        signals.respuesta_lista.emit("MAGI", f"[{consenso}] {respuesta_final}")
        
        # Entrenar solo a los cerebros que participaron
        for ia, path, _ in brains_to_respond:
            ia.aprender(texto_limpio)
            ia.aprender(respuesta_final, epocas=1)
            ia.guardar(path)

    def process_message_separate(self, texto, signals):
        """Cada cerebro activo responde de forma independiente"""
        # Limpiar etiquetas del texto
        texto_limpio = texto
        import re
        for tag in ["@melchor", "@gaspar", "@casper"]:
            texto_limpio = re.sub(re.escape(tag), "", texto_limpio, flags=re.IGNORECASE).strip()

        activos = self.get_active_brains()
        if not activos:
            signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos.")
            return

        signals.pensando.emit(True)
        
        for ia, path, nombre in activos:
            # Generar respuesta individual
            respuesta = ia.generar_respuesta(texto_limpio, temperatura=0.8, top_p=0.9, penalty=1.2)
            
            # Emitir respuesta con el nombre del cerebro
            signals.respuesta_lista.emit(nombre, respuesta)
            
            # Cada uno aprende de su propia respuesta
            ia.aprender(texto_limpio)
            ia.aprender(respuesta, epocas=1)
            ia.guardar(path)
            
            # Pequeña pausa para no saturar la UI
            time.sleep(0.5)
            
        signals.pensando.emit(False)

    def process_debate_message(self, texto, brain_name, signals):
        """Procesa un mensaje en modo debate, haciendo que un cerebro específico responda"""
        signals.pensando.emit(True)
        
        # Identificar cerebro
        ia_obj = None
        ia_path = ""
        
        if brain_name == "MELCHOR" and self.melchor_activo:
            ia_obj, ia_path = self.ia_melchor, self.archivo_melchor
        elif brain_name == "GASPAR" and self.gaspar_activo:
            ia_obj, ia_path = self.ia_gaspar, self.archivo_gaspar
        elif brain_name == "CASPER" and self.casper_activo:
            ia_obj, ia_path = self.ia_casper, self.archivo_casper
            
        if not ia_obj:
            # Si el cerebro actual no está activo, buscar el siguiente activo
            activos = self.get_active_brains()
            if not activos:
                signals.pensando.emit(False)
                return
            ia_obj, ia_path, brain_name = activos[0]

        # Generar respuesta
        respuesta = ia_obj.generar_respuesta(texto)
        
        # En modo debate, TAMBIÉN aprenden todos los cerebros activos
        # para que la experiencia sea compartida y evolucionen juntos
        for ia, path, _ in self.get_active_brains():
            ia.aprender(texto)
            ia.aprender(respuesta, epocas=1)
            ia.guardar(path)
        
        signals.pensando.emit(False)
        signals.respuesta_lista.emit(brain_name, respuesta)

        # Opcional: Notificar que todos han aprendido (para que el usuario lo sepa)
        activos = [n for _, _, n in self.get_active_brains()]
        if len(activos) > 1:
            signals.respuesta_lista.emit("SISTEMA", f"🧠 Aprendizaje compartido: {', '.join(activos)}")
    
    def train_massive(self, texto, signals):
        """Entrenamiento masivo con progreso basado en caracteres"""
        try:
            cerebros_activos = self.get_active_brains()
            
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos para entrenar")
                return
            
            nombres = ", ".join([nombre for _, _, nombre in cerebros_activos])
            signals.respuesta_lista.emit("SISTEMA", f"📚 Entrenando: {nombres}")
            
            lineas = texto.split('\n')
            total_chars = max(1, len(texto))
            chars_procesados = 0
            ultimo_progreso_chars = 0
            
            for i, linea in enumerate(lineas):
                if linea.strip():
                    for ia, _, _ in cerebros_activos:
                        ia.aprender(linea, epocas=1)
                
                chars_procesados += len(linea) + 1 # +1 por el \n
                
                # Emitir progreso cada 5000 caracteres, cada 50 líneas, o al final
                if (chars_procesados - ultimo_progreso_chars) >= 5000 or i % 50 == 0 or i == len(lineas) - 1:
                    progreso = int((min(chars_procesados, total_chars) / total_chars) * 100)
                    signals.progreso_entrenamiento.emit(min(progreso, 100))
                    ultimo_progreso_chars = chars_procesados
            
            for ia, path, _ in cerebros_activos:
                ia.guardar(path)
            
            signals.progreso_entrenamiento.emit(100)
            signals.entrenamiento_terminado.emit()
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"Error en entrenamiento: {str(e)}")
            signals.progreso_entrenamiento.emit(0)
    
    def train_from_file(self, path, signals):
        """Entrena desde archivo de texto"""
        try:
            cerebros_activos = self.get_active_brains()
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos")
                return
            
            signals.respuesta_lista.emit("SISTEMA", "📄 Leyendo archivo de texto...")
            
            # Leer todo el archivo
            with open(path, 'rt', encoding='utf-8', errors='ignore') as f:
                texto_completo = f.read()
            
            # Dividir en bloques de ~1000 caracteres para procesamiento eficiente
            chunk_size = 1000
            bloques = []
            
            # Intentar dividir por párrafos primero
            parrafos = texto_completo.split('\n\n')
            bloque_actual = ""
            
            for parrafo in parrafos:
                parrafo = parrafo.strip()
                if not parrafo:
                    continue
                
                if len(bloque_actual) + len(parrafo) < chunk_size:
                    bloque_actual += " " + parrafo if bloque_actual else parrafo
                else:
                    if bloque_actual:
                        bloques.append(bloque_actual)
                    bloque_actual = parrafo
            
            # Agregar último bloque
            if bloque_actual:
                bloques.append(bloque_actual)
            
            # Si no hay bloques, dividir por tamaño fijo
            if not bloques:
                for i in range(0, len(texto_completo), chunk_size):
                    chunk = texto_completo[i:i+chunk_size].strip()
                    if chunk:
                        bloques.append(chunk)
            
            total_caracteres = sum(len(b) for b in bloques)
            signals.respuesta_lista.emit("SISTEMA", f"📚 Procesando {len(bloques)} bloques ({total_caracteres} caracteres)...")
            
            # Entrenar
            caracteres_procesados = 0
            for idx, bloque in enumerate(bloques):
                if bloque.strip():
                    for ia, _, _ in cerebros_activos:
                        ia.aprender(bloque, epocas=5)
                    
                    caracteres_procesados += len(bloque)
                
                progress = int((caracteres_procesados / total_caracteres) * 100)
                signals.progreso_entrenamiento.emit(min(progress, 100))
                
                # Guardar cada 100 bloques
                if (idx + 1) % 100 == 0:
                    for ia, path_save, _ in cerebros_activos:
                        ia.guardar(path_save)
                    signals.respuesta_lista.emit("SISTEMA", f"💾 Guardado intermedio ({idx+1}/{len(bloques)} bloques)")
            
            # Guardar final
            for ia, path_save, _ in cerebros_activos:
                ia.guardar(path_save)
            
            signals.progreso_entrenamiento.emit(100)
            signals.entrenamiento_terminado.emit()
            signals.respuesta_lista.emit("SISTEMA", f"✅ Texto completado: {len(bloques)} bloques, {total_caracteres} caracteres procesados")
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ Error: {str(e)}")
    
    def train_from_text_folder(self, folder_path, signals):
        """Entrena desde carpeta de archivos TXT"""
        try:
            cerebros_activos = self.get_active_brains()
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos")
                return
            
            # Buscar todos los archivos .txt en la carpeta
            archivos_txt = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                           if f.lower().endswith('.txt')]
            
            if not archivos_txt:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No se encontraron archivos .txt en la carpeta")
                return
            
            signals.respuesta_lista.emit("SISTEMA", f"📁 Encontrados {len(archivos_txt)} archivos TXT")
            
            total_caracteres_global = 0
            total_bloques_global = 0
            
            for idx, archivo_path in enumerate(archivos_txt):
                nombre_archivo = os.path.basename(archivo_path)
                signals.respuesta_lista.emit("SISTEMA", f"📄 [{idx+1}/{len(archivos_txt)}] Procesando: {nombre_archivo}")
                
                try:
                    # Leer archivo
                    with open(archivo_path, 'rt', encoding='utf-8', errors='ignore') as f:
                        texto_completo = f.read()
                    
                    if not texto_completo.strip():
                        signals.respuesta_lista.emit("SISTEMA", f"⚠️ Archivo vacío: {nombre_archivo}")
                        continue
                    
                    # Dividir en bloques de ~1000 caracteres
                    chunk_size = 1000
                    bloques = []
                    
                    # Intentar dividir por párrafos
                    parrafos = texto_completo.split('\n\n')
                    bloque_actual = ""
                    
                    for parrafo in parrafos:
                        parrafo = parrafo.strip()
                        if not parrafo:
                            continue
                        
                        if len(bloque_actual) + len(parrafo) < chunk_size:
                            bloque_actual += " " + parrafo if bloque_actual else parrafo
                        else:
                            if bloque_actual:
                                bloques.append(bloque_actual)
                            bloque_actual = parrafo
                    
                    if bloque_actual:
                        bloques.append(bloque_actual)
                    
                    # Si no hay bloques, dividir por tamaño fijo
                    if not bloques:
                        for i in range(0, len(texto_completo), chunk_size):
                            chunk = texto_completo[i:i+chunk_size].strip()
                            if chunk:
                                bloques.append(chunk)
                    
                    if not bloques:
                        signals.respuesta_lista.emit("SISTEMA", f"⚠️ No se pudo procesar: {nombre_archivo}")
                        continue
                    
                    total_caracteres = sum(len(b) for b in bloques)
                    signals.respuesta_lista.emit("SISTEMA", f"   └─ {len(bloques)} bloques, {total_caracteres} caracteres")
                    
                    # Entrenar con bloques
                    for bloque in bloques:
                        if bloque.strip():
                            for ia, _, _ in cerebros_activos:
                                ia.aprender(bloque, epocas=5)
                    
                    total_bloques_global += len(bloques)
                    total_caracteres_global += total_caracteres
                    
                    # Actualizar progreso
                    progreso = int(((idx + 1) / len(archivos_txt)) * 100)
                    signals.progreso_entrenamiento.emit(progreso)
                    
                    # Guardar después de cada archivo
                    for ia, path_save, _ in cerebros_activos:
                        ia.guardar(path_save)
                    
                except Exception as e:
                    signals.respuesta_lista.emit("SISTEMA", f"❌ Error en {nombre_archivo}: {str(e)}")
                    continue
            
            signals.progreso_entrenamiento.emit(100)
            signals.entrenamiento_terminado.emit()
            signals.respuesta_lista.emit("SISTEMA", 
                f"✅ Carpeta completada: {len(archivos_txt)} archivos, {total_bloques_global} bloques, {total_caracteres_global} caracteres")
        
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ Error en carpeta: {str(e)}")
    
    def train_from_pdf(self, path, signals):
        """Entrena desde PDF"""
        try:
            cerebros_activos = self.get_active_brains()
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos")
                return
            
            signals.respuesta_lista.emit("SISTEMA", f"📖 Extrayendo texto del PDF...")
            doc = fitz.open(path)
            total_pages = len(doc)
            
            # Extraer todo el texto primero
            texto_completo = []
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    texto_completo.append(text)
                
                # Actualizar progreso de extracción (primera mitad)
                progress = int(((page_num + 1) / total_pages) * 50)
                signals.progreso_entrenamiento.emit(progress)
            
            doc.close()
            
            # Unir todo el texto
            texto_total = "\n".join(texto_completo)
            
            # Limpiar y preparar el texto
            # Eliminar líneas muy cortas que probablemente sean ruido
            lineas = texto_total.split('\n')
            lineas_limpias = [l.strip() for l in lineas if len(l.strip()) > 10]
            
            # Reconstruir en bloques (párrafos)
            bloques = []
            bloque_actual = []
            
            for linea in lineas_limpias:
                bloque_actual.append(linea)
                # Si la línea termina con punto, crear un bloque
                if linea.endswith('.') or linea.endswith('!') or linea.endswith('?'):
                    bloques.append(' '.join(bloque_actual))
                    bloque_actual = []
            
            # Agregar último bloque si existe
            if bloque_actual:
                bloques.append(' '.join(bloque_actual))
            
            if not bloques:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No se pudo extraer texto significativo del PDF")
                return
            
            total_caracteres = sum(len(b) for b in bloques)
            signals.respuesta_lista.emit("SISTEMA", f"📚 Procesando {len(bloques)} bloques de texto ({total_caracteres} caracteres)...")
            
            # Entrenar con bloques (similar al chat)
            caracteres_procesados = 0
            for idx, bloque in enumerate(bloques):
                if bloque.strip():
                    for ia, _, _ in cerebros_activos:
                        # Usar 5 épocas para aprendizaje profundo de archivos
                        ia.aprender(bloque, epocas=5)
                    
                    caracteres_procesados += len(bloque)
                
                # Actualizar progreso (segunda mitad: 50-100%)
                progress = 50 + int((caracteres_procesados / total_caracteres) * 50)
                signals.progreso_entrenamiento.emit(min(progress, 100))
                
                # Guardar cada 50 bloques
                if (idx + 1) % 50 == 0:
                    for ia, path_save, _ in cerebros_activos:
                        ia.guardar(path_save)
                    signals.respuesta_lista.emit("SISTEMA", f"💾 Guardado intermedio ({idx+1}/{len(bloques)} bloques)")
            
            # Guardar final
            for ia, path_save, _ in cerebros_activos:
                ia.guardar(path_save)
            
            signals.progreso_entrenamiento.emit(100)
            signals.entrenamiento_terminado.emit()
            signals.respuesta_lista.emit("SISTEMA", f"✅ PDF completado: {len(bloques)} bloques, {total_caracteres} caracteres procesados")
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ PDF Error: {str(e)}")
    
    def train_from_video(self, path, signals):
        """Entrena desde video/audio"""
        try:
            cerebros_activos = self.get_active_brains()
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos")
                return
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            signals.respuesta_lista.emit("SISTEMA", f"Cargando modelo Whisper en {device.upper()}...")
            model = whisper.load_model("base", device=device).float()
            
            result = model.transcribe(path, verbose=False, language="es", fp16=False)
            text = result["text"]
            
            if not text.strip():
                signals.respuesta_lista.emit("SISTEMA", "No se detectó habla en el archivo.")
                return
            
            # Guardar transcripción
            txt_path = os.path.splitext(path)[0] + ".txt"
            try:
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                signals.respuesta_lista.emit("SISTEMA", f"Transcripción guardada en: {os.path.basename(txt_path)}")
            except:
                pass
            
            signals.respuesta_lista.emit("SISTEMA", "Iniciando aprendizaje...")
            
            # Entrenar en bloques
            chunk_size = 2000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]
                if len(chunk) < 2:
                    continue
                
                for ia, _, _ in cerebros_activos:
                    ia.aprender(chunk, epocas=1)
                
                progress = int((min(i + chunk_size, len(text)) / len(text)) * 100)
                signals.progreso_entrenamiento.emit(progress)
                
                if (i // chunk_size + 1) % 5 == 0:
                    for ia, path_save, _ in cerebros_activos:
                        ia.guardar(path_save)
            
            for ia, path_save, _ in cerebros_activos:
                ia.guardar(path_save)
            
            signals.progreso_entrenamiento.emit(100)
            signals.entrenamiento_terminado.emit()
            signals.respuesta_lista.emit("SISTEMA", "Video training completed.")
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ Video Error: {str(e)}")
    
    def train_from_video_folder(self, folder_path, signals):
        """Entrena desde carpeta de videos"""
        try:
            cerebros_activos = self.get_active_brains()
            if not cerebros_activos:
                signals.respuesta_lista.emit("SISTEMA", "⚠️ No hay cerebros activos")
                return
            
            extensiones = ('.mp4', '.mkv', '.avi', '.mov', '.mp3', '.wav')
            archivos = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                       if f.lower().endswith(extensiones)]
            
            if not archivos:
                signals.respuesta_lista.emit("SISTEMA", "No video files found.")
                return
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            signals.respuesta_lista.emit("SISTEMA", f"Processing {len(archivos)} files ({device.upper()})...")
            
            model = whisper.load_model("base", device=device).float()
            
            for idx, path_archivo in enumerate(archivos):
                nombre = os.path.basename(path_archivo)
                signals.respuesta_lista.emit("SISTEMA", f"🚀 Procesando [{idx+1}/{len(archivos)}]: {nombre}")
                
                result = model.transcribe(path_archivo, verbose=False, language="es", fp16=False)
                text = result["text"].strip()
                
                if text:
                    # Entrenar
                    chunk_size = 2000
                    for c_idx in range(0, len(text), chunk_size):
                        chunk = text[c_idx:c_idx + chunk_size]
                        if len(chunk) >= 2:
                            for ia, _, _ in cerebros_activos:
                                ia.aprender(chunk, epocas=1)
                
                progreso = int(((idx + 1) / len(archivos)) * 100)
                signals.progreso_entrenamiento.emit(progreso)
                
                for ia, path_save, _ in cerebros_activos:
                    ia.guardar(path_save)
            
            signals.progreso_entrenamiento.emit(100)
            signals.entrenamiento_terminado.emit()
            signals.respuesta_lista.emit("SISTEMA", "Bulk training complete.")
            
        except Exception as e:
            signals.respuesta_lista.emit("SISTEMA", f"❌ Folder Error: {str(e)}")
    
    def load_external_brain(self, nombre_cerebro, filename):
        """Carga un cerebro externo"""
        try:
            cerebro_cargado = RedCrecimientoInfinito.cargar(filename)
            
            if nombre_cerebro == "melchor":
                self.ia_melchor = cerebro_cargado
                self.ia_melchor.guardar(self.archivo_melchor)
                return True, f"✅ MELCHOR cargado exitosamente ({self.ia_melchor.n_oculta} neuronas)"
            elif nombre_cerebro == "gaspar":
                self.ia_gaspar = cerebro_cargado
                self.ia_gaspar.guardar(self.archivo_gaspar)
                return True, f"✅ GASPAR cargado exitosamente ({self.ia_gaspar.n_oculta} neuronas)"
            elif nombre_cerebro == "casper":
                self.ia_casper = cerebro_cargado
                self.ia_casper.guardar(self.archivo_casper)
                return True, f"✅ CASPER cargado exitosamente ({self.ia_casper.n_oculta} neuronas)"
            
            return False, "Nombre de cerebro inválido"
            
        except Exception as e:
            return False, f"Error cargando cerebro: {str(e)}"

    def train_from_text_folder_gpu(self, folder_path, signals=None, console_mode=False, stop_event=None):
        """
        Entrena desde carpeta de archivos TXT usando GPU MPS.
        Soporta modo consola (headless) y stop_event para interrupción segura.
        """
        def log(msg):
            if console_mode:
                print(msg)
            elif signals:
                signals.respuesta_lista.emit("SISTEMA", msg)

        def update_progress(val):
            if not console_mode and signals:
                signals.progreso_entrenamiento.emit(val)

        try:
            cerebros_activos = self.get_active_brains()
            if not cerebros_activos:
                log("⚠️ No hay cerebros activos")
                return
            
            # Verificar disponibilidad de MPS
            try:
                import torch
                if not torch.backends.mps.is_available():
                    log("⚠️ GPU MPS no detectada. Usando CPU (Lento)...")
                else:
                    log("🚀 GPU MPS PERSISTENTE ACTIVADA - MODO HYPER-SPEED")
            except ImportError:
                 log("⚠️ PyTorch no encontrado. Usando CPU...")

            # Buscar archivos
            archivos_txt = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
            if not archivos_txt:
                log("⚠️ No se encontraron archivos .txt")
                return
            
            log(f"📁 BATCH JOB: {len(archivos_txt)} archivos TXT en cola")
            
            # 1. INICIAR SESIÓN GPU PERSISTENTE
            for ia, _, nombre in cerebros_activos:
                if stop_event and stop_event.is_set(): break
                if hasattr(ia, 'iniciar_sesion_gpu'):
                    success = ia.iniciar_sesion_gpu()
                    if success: log(f"   └─ {nombre}: VRAM cargada OK")

            total_caracteres_global = 0
            
            try:
                # 2. PROCESAR ARCHIVOS (Bucle rápido)
                for idx, archivo_path in enumerate(archivos_txt):
                    # Chequear interrupción
                    if stop_event and stop_event.is_set():
                        log("\n🛑 INTERRUPTED BY USER (ESC DETECTED)")
                        break

                    try:
                        with open(archivo_path, 'rt', encoding='utf-8', errors='ignore') as f:
                            texto_completo = f.read()
                        
                        if not texto_completo.strip(): continue
                        
                        # MEGA-CHUNKS para M4: 200,000 caracteres
                        chunk_size = 200000 
                        bloques = [texto_completo[i:i+chunk_size] for i in range(0, len(texto_completo), chunk_size)]
                        
                        for bloque in bloques:
                            if stop_event and stop_event.is_set(): break
                            if bloque.strip():
                                for ia, _, _ in cerebros_activos:
                                    if hasattr(ia, 'aprender_bloque_gpu'):
                                        ia.aprender_bloque_gpu(bloque, epocas=2)
                                    else:
                                        ia.aprender(bloque, epocas=1)
                        
                        total_caracteres_global += len(texto_completo)
                        
                        # Progreso UI / Console Log
                        if console_mode:
                            sys.stdout.write(f"\r✅ Processed {idx+1}/{len(archivos_txt)} files | Total Chars: {total_caracteres_global:,}")
                            sys.stdout.flush()
                        else:
                            if (idx + 1) % 5 == 0 or idx == len(archivos_txt) - 1:
                                progreso = int(((idx + 1) / len(archivos_txt)) * 100)
                                update_progress(progreso)
                        
                        # Guardado periódico
                        if (idx + 1) % 50 == 0:
                            log(f"💾 Checkpoint: Sincronizando RAM...")
                            for ia, path_save, _ in cerebros_activos:
                                if hasattr(ia, 'sincronizar_gpu_a_cpu'):
                                    ia.sincronizar_gpu_a_cpu()
                                ia.guardar(path_save)
                                
                    except Exception as e:
                        log(f"❌ Error en archivo {idx}: {str(e)}")
                        continue
            
            finally:
                # 3. FINALIZAR SESIÓN GPU (Siempre ejecutar, incluso si hay error)
                log("\n🏁 Finalizando sesión GPU y liberando memoria...")
                for ia, path_save, _ in cerebros_activos:
                    if hasattr(ia, 'finalizar_sesion_gpu'):
                        ia.finalizar_sesion_gpu()
                    ia.guardar(path_save)

            if not console_mode and signals:
                update_progress(100)
                signals.entrenamiento_terminado.emit()
            
            log(f"\n✅ FINALIZADO: {len(archivos_txt)} archivos procesados a velocidad luz. Total: {total_caracteres_global:,} caracteres.")
            
        except Exception as e:
            log(f"❌ CRITICAL GPU ERROR: {str(e)}")
