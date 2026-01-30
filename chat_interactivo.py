import numpy as np
import pickle
import time
import sys
import os
import threading
try:
    from safetensors.numpy import save_file, load_file
except ImportError:
    save_file = None
    load_file = None

# --- IA OPTIMIZADA CON APRENDIZAJE ACELERADO ---
class RedCrecimientoInfinito:
    def __init__(self, vocabulario=None, n_oculta=128):
        self.eps = 1e-8
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.lr = 0.001 # Adam suele usar un lr más pequeño que SGD
        self.n_oculta = n_oculta
        self.interacciones = 0
        self.caracteres_totales = 0
        self.t = 0
        self.lock = threading.RLock()
        
        if vocabulario:
            self.vocab = sorted(list(set(vocabulario)))
            self.char_to_int = {char: i for i, char in enumerate(self.vocab)}
            self.int_to_char = {i: char for i, char in enumerate(self.vocab)}
            n_vocab = len(self.vocab)
            
            # Inicialización Xavier/Glorot
            # Inicialización Xavier/Glorot con float32
            self.w_eo = (np.random.randn(n_vocab, self.n_oculta) * np.sqrt(1. / n_vocab)).astype(np.float32)
            self.w_os = (np.random.randn(self.n_oculta, n_vocab) * np.sqrt(1. / self.n_oculta)).astype(np.float32)
            self.b_o = np.zeros((1, self.n_oculta), dtype=np.float32)
            self.b_s = np.zeros((1, n_vocab), dtype=np.float32)
            
            # Buffers para Adam en float32
            self.m_w_eo, self.v_w_eo = np.zeros_like(self.w_eo, dtype=np.float32), np.zeros_like(self.w_eo, dtype=np.float32)
            self.m_w_os, self.v_w_os = np.zeros_like(self.w_os, dtype=np.float32), np.zeros_like(self.w_os, dtype=np.float32)
            self.m_b_o, self.v_b_o = np.zeros_like(self.b_o, dtype=np.float32), np.zeros_like(self.b_o, dtype=np.float32)
            self.m_b_s, self.v_b_s = np.zeros_like(self.b_s, dtype=np.float32), np.zeros_like(self.b_s, dtype=np.float32)

    def expandir_vocabulario(self, nuevos_chars):
        """Añade caracteres nuevos al vocabulario y expande las matrices de E/S"""
        with self.lock:
            for char in nuevos_chars:
                if char not in self.vocab:
                    idx = len(self.vocab)
                    self.vocab.append(char)
                    self.char_to_int[char] = idx
                    self.int_to_char[idx] = char
                    
                    print(f"✨ VOCABULARIO: Nuevo carácter aprendido: '{char}'")
                    
                    # Expandir w_eo (Nuevas filas)
                    nueva_fila_eo = (np.random.randn(1, self.n_oculta) * np.sqrt(1. / self.n_oculta)).astype(np.float32)
                    self.w_eo = np.vstack([self.w_eo, nueva_fila_eo])
                    self.m_w_eo = np.vstack([self.m_w_eo, np.zeros((1, self.n_oculta), dtype=np.float32)])
                    self.v_w_eo = np.vstack([self.v_w_eo, np.zeros((1, self.n_oculta), dtype=np.float32)])
                    
                    # Expandir w_os (Nuevas columnas)
                    nueva_col_os = (np.random.randn(self.n_oculta, 1) * np.sqrt(1. / self.n_oculta)).astype(np.float32)
                    self.w_os = np.hstack([self.w_os, nueva_col_os])
                    self.m_w_os = np.hstack([self.m_w_os, np.zeros((self.n_oculta, 1), dtype=np.float32)])
                    self.v_w_os = np.hstack([self.v_w_os, np.zeros((self.n_oculta, 1), dtype=np.float32)])
                    
                    # Expandir b_s
                    self.b_s = np.append(self.b_s, [[0]], axis=1)
                    self.m_b_s = np.append(self.m_b_s, [[0]], axis=1)
                    self.v_b_s = np.append(self.v_b_s, [[0]], axis=1)

    def expandir_cerebro(self):
        """Añade neuronas nuevas con crecimiento logarítmico para evitar lentitud extrema"""
        with self.lock:
            # Límite de seguridad mucho más alto para supercomputación
            if self.n_oculta >= 1000000:
                return
                
            # Crecimiento más inteligente: cuanto más grande, más lento crece (logarítmico)
            incremento = max(8, int(128 / (1 + np.log1p(self.n_oculta / 128))))
            
            n_vocab = len(self.vocab)
            nueva_n_oculta = self.n_oculta + incremento
            
            print(f"\n🧠 OPTIMIZACIÓN: Expandiendo a {nueva_n_oculta} neuronas (crecimiento controlado)...")
            
            # Expandir Pesos Entada-Oculta (float32)
            nuevos_w_eo = (np.random.randn(n_vocab, nueva_n_oculta) * np.sqrt(1. / n_vocab)).astype(np.float32)
            nuevos_w_eo[:, :self.n_oculta] = self.w_eo
            self.w_eo = nuevos_w_eo
            
            # Expandir Pesos Oculta-Salida
            nuevos_w_os = (np.random.randn(nueva_n_oculta, n_vocab) * np.sqrt(1. / nueva_n_oculta)).astype(np.float32)
            nuevos_w_os[:self.n_oculta, :] = self.w_os
            self.w_os = nuevos_w_os
            
            # Expandir Sesgos (Sincronizado)
            self.b_o = np.concatenate([self.b_o, np.zeros((1, incremento), dtype=np.float32)], axis=1)
            # b_s NO se expande aquí porque depende del vocabulario, no de las neuronas ocultas
            
            # Expandir Buffers Adam
            self.m_w_eo = np.pad(self.m_w_eo, ((0,0), (0, incremento)))
            self.v_w_eo = np.pad(self.v_w_eo, ((0,0), (0, incremento)))
            self.m_w_os = np.pad(self.m_w_os, ((0, incremento), (0,0)))
            self.v_w_os = np.pad(self.v_w_os, ((0, incremento), (0,0)))
            self.m_b_o = np.pad(self.m_b_o, ((0,0), (0, incremento)))
            self.v_b_o = np.pad(self.v_b_o, ((0,0), (0, incremento)))

            self.n_oculta = nueva_n_oculta
            
            if hasattr(self, 'on_expand') and self.on_expand:
                self.on_expand(self.n_oculta)

    def softmax(self, x):
        # x es float32, max es float32
        x_max = np.max(x, axis=1, keepdims=True)
        e_x = np.exp(x - x_max)
        return (e_x / (e_x.sum(axis=1, keepdims=True) + 1e-8)).astype(np.float32)

    def forward(self, x_indices):
        """Forward optimizado con Ventana de Contexto (Causal Mean Pooling)"""
        with self.lock:
            # Embeddings de los caracteres actuales
            embeddings = self.w_eo[x_indices] # (L, D)
            
            # Aplicar Ventana de Contexto (Media móvil causal)
            # Esto permite que cada caracter "tenga memoria" de los N anteriores
            self.window_size = 10
            L = len(x_indices)
            
            if L > 1:
                # Calculo de media móvil rápida (O(L))
                cumsum = np.cumsum(embeddings, axis=0)
                context_embeddings = cumsum.copy()
                # Restar el elemento que sale de la ventana
                k = self.window_size
                context_embeddings[k:] -= cumsum[:-k]
                
                # Divisores dinámicos para el inicio de la secuencia
                divisores = np.arange(1, L + 1)
                divisores[divisores > k] = k
                self.emb_with_context = (context_embeddings / divisores[:, None]).astype(np.float32)
            else:
                self.emb_with_context = embeddings
            
            # --- CODIFICACIÓN POSICIONAL (Sin/Cos) ---
            # Ayuda a la IA a entender el orden de los caracteres en la ventana
            posiciones = np.arange(L)[:, None]
            div_term = np.exp(np.arange(0, self.n_oculta, 2) * -(np.log(10000.0) / self.n_oculta))
            pe = np.zeros((L, self.n_oculta), dtype=np.float32)
            pe[:, 0::2] = np.sin(posiciones * div_term)
            pe[:, 1::2] = np.cos(posiciones * div_term[:self.n_oculta//2])
            
            self.emb_with_context += pe
            
            # --- ACTIVACIÓN SWISH (x * sigmoid(x)) ---
            # Más fluida que tanh para redes profundas
            x_hidden = self.emb_with_context + self.b_o
            self.hidden = (x_hidden * (1 / (1 + np.exp(-x_hidden)))).astype(np.float32)
            
            self.output = self.softmax(np.dot(self.hidden, self.w_os) + self.b_s)
            return self.output

    def aprender(self, texto, lr=None, epocas=3):
        with self.lock:
            # 1. Chequear caracteres desconocidos
            desconocidos = [c for c in texto if c not in self.char_to_int]
            if desconocidos:
                self.expandir_vocabulario(list(set(desconocidos)))

            if lr: self.lr = lr
            self.interacciones += 1
            
            # Convertir texto a índices
            indices = [self.char_to_int[c] for c in texto if c in self.char_to_int]
            if len(indices) < 2: return
            
            X = indices[:-1]
            Y = indices[1:]
            L = len(X)
            
            for _ in range(epocas):
                self.t += 1
                probabilidades = self.forward(X)
                
                # Gradiente de salida (Loss: Cross-Entropy)
                dz_salida = probabilidades.copy()
                dz_salida[np.arange(len(Y)), Y] -= 1
                dz_salida /= len(Y)
                
                # Gradientes de la capa de salida
                dw_os = np.dot(self.hidden.T, dz_salida)
                db_s = np.sum(dz_salida, axis=0, keepdims=True)
                
                # Gradiente hacia la capa oculta (Swish gradient)
                # Swish grad: sig(x) + x * sig(x) * (1 - sig(x)) = swish(x) + sig(x)*(1-swish(x))
                sig_x = 1 / (1 + np.exp(-(self.emb_with_context + self.b_o)))
                swish_grad = sig_x + self.hidden * (1 - sig_x)
                d_hidden = np.dot(dz_salida, self.w_os.T) * swish_grad
                
                # --- DISTRIBUCIÓN DE GRADIENTES POR VENTANA DE CONTEXTO ---
                # Como usamos el promedio de una ventana, el gradiente en cada posición
                # se distribuye equitativamente entre los caracteres de esa ventana.
                d_embeddings = d_hidden.copy()
                if L > 1:
                    k = self.window_size
                    # Inversa del promedio móvil (propagación de gradiente causal)
                    # Cada posición t recibe gradiente de d_hidden[t...t+k-1]
                    d_emb_distribuido = np.zeros_like(d_embeddings)
                    
                    # Divisores dinámicos para normalizar el gradiente
                    divisores = np.arange(1, L + 1)
                    divisores[divisores > k] = k
                    d_hidden_normalized = d_hidden / divisores[:, None]
                    
                    # Acumular gradientes (ventana deslizante inversa)
                    # Este bloque simula la distribución del gradiente del promedio
                    for t in range(L):
                        end_idx = min(t + k, L)
                        d_emb_distribuido[t] = np.sum(d_hidden_normalized[t:end_idx], axis=0)
                    d_embeddings = d_emb_distribuido

                dw_eo = np.zeros_like(self.w_eo)
                np.add.at(dw_eo, X, d_embeddings)
                db_o = np.sum(d_hidden, axis=0, keepdims=True)
                
                # --- OPTIMIZADOR ADAM ---
                for param, grad, m, v in [
                    (self.w_eo, dw_eo, self.m_w_eo, self.v_w_eo),
                    (self.w_os, dw_os, self.m_w_os, self.v_w_os),
                    (self.b_o, db_o, self.m_b_o, self.v_b_o),
                    (self.b_s, db_s, self.m_b_s, self.v_b_s)
                ]:
                    m[:] = self.beta1 * m + (1 - self.beta1) * grad
                    v[:] = self.beta2 * v + (1 - self.beta2) * (grad**2)
                    m_hat = m / (1 - self.beta1**self.t + self.eps)
                    v_hat = v / (1 - self.beta2**self.t + self.eps)
                    param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

            # Lógica de crecimiento mejorada para textos largos (PDF/Cargas masivas)
                # Expande una vez por cada 500 caracteres procesados
                caracteres_a_contar = len(X)
                while caracteres_a_contar > 0:
                    # Cuánto falta para el próximo bloque de 500
                    falta_para_bloque = 500 - (self.caracteres_totales % 500)
                    if falta_para_bloque == 0: falta_para_bloque = 500
                    
                    avance = min(caracteres_a_contar, falta_para_bloque)
                    self.caracteres_totales += avance
                    caracteres_a_contar -= avance
                    
                    if self.caracteres_totales % 500 == 0:
                        self.expandir_cerebro()

    def dormir(self, umbral_poda=0.01, factor_refuerzo=1.1):
        """Simula el sueño: consolida memoria (con poda)"""
        return self._procesar_descanso(umbral_poda, factor_refuerzo, decay=0.9995, fase="profundo")

    def siesta(self, factor_refuerzo=1.05):
        """Simula una siesta: organiza y refuerza sin borrar (sin poda)"""
        return self._procesar_descanso(umbral_poda=0.0, factor_refuerzo=factor_refuerzo, decay=0.9999, fase="ligero")

    def _procesar_descanso(self, umbral_poda, factor_refuerzo, decay, fase):
        """Lógica compartida para sueño y siesta"""
        with self.lock:
            print(f"\n💤 MAGI entrando en fase de descanso {fase}...")
            
            pesos_eo_abs = np.abs(self.w_eo)
            pesos_os_abs = np.abs(self.w_os)
            
            conexiones_antes_eo = np.count_nonzero(pesos_eo_abs > 1e-10)
            conexiones_antes_os = np.count_nonzero(pesos_os_abs > 1e-10)
            
            # Poda (solo si umbral_poda > 0)
            podadas_eo = 0
            podadas_os = 0
            if umbral_poda > 0:
                umbral_eo = np.percentile(pesos_eo_abs[pesos_eo_abs > 1e-10], umbral_poda * 100) if conexiones_antes_eo > 0 else 0
                umbral_os = np.percentile(pesos_os_abs[pesos_os_abs > 1e-10], umbral_poda * 100) if conexiones_antes_os > 0 else 0
                
                mascara_poda_eo = (pesos_eo_abs < umbral_eo) & (pesos_eo_abs > 1e-10)
                mascara_poda_os = (pesos_os_abs < umbral_os) & (pesos_os_abs > 1e-10)
                
                self.w_eo[mascara_poda_eo] = 0
                self.w_os[mascara_poda_os] = 0
                
                self.m_w_eo[mascara_poda_eo] = 0
                self.v_w_eo[mascara_poda_eo] = 0
                self.m_w_os[mascara_poda_os] = 0
                self.v_w_os[mascara_poda_os] = 0
                
                podadas_eo = np.count_nonzero(mascara_poda_eo)
                podadas_os = np.count_nonzero(mascara_poda_os)
            
            # Refuerzo (90 percentil para arriba)
            umbral_fuerte_eo = np.percentile(pesos_eo_abs, 90) if conexiones_antes_eo > 0 else 0
            umbral_fuerte_os = np.percentile(pesos_os_abs, 90) if conexiones_antes_os > 0 else 0
            
            mascara_refuerzo_eo = pesos_eo_abs > umbral_fuerte_eo
            mascara_refuerzo_os = pesos_os_abs > umbral_fuerte_os
            
            self.w_eo[mascara_refuerzo_eo] *= factor_refuerzo
            self.w_os[mascara_refuerzo_os] *= factor_refuerzo
            
            reforzadas_eo = np.count_nonzero(mascara_refuerzo_eo)
            reforzadas_os = np.count_nonzero(mascara_refuerzo_os)
            
            # Organización (Weight Decay)
            self.w_eo *= decay
            self.w_os *= decay
            
            self.b_o = np.clip(self.b_o, -2, 2)
            self.b_s = np.clip(self.b_s, -2, 2)
            
            conexiones_finales = np.count_nonzero(np.abs(self.w_eo) > 1e-10) + np.count_nonzero(np.abs(self.w_os) > 1e-10)
            
            return {
                'podadas': podadas_eo + podadas_os,
                'reforzadas': reforzadas_eo + reforzadas_os,
                'activas': conexiones_finales
            }

    def generar_respuesta(self, semilla, longitud=120, temperatura=0.7, top_p=0.9, penalty=1.2):
        """Generación avanzada con Top-p (Nucleus) Sampling y Penalización de Repetición"""
        with self.lock:
            indices_contexto = [self.char_to_int[c] for c in semilla if c in self.char_to_int]
            if not indices_contexto:
                indices_contexto = [self.char_to_int[np.random.choice(self.vocab)]]
                
            res = ""
            counts = {} # Para penalización de repetición
            
            for _ in range(longitud):
                input_seq = indices_contexto[-10:]
                prediccion_batch = self.forward(input_seq)
                logits = prediccion_batch[-1]
                
                # 1. Aplicar temperatura
                logits = np.log(logits + self.eps) / max(0.1, temperatura)
                
                # 2. Penalización de repetición
                for idx, count in counts.items():
                    if logits[idx] > 0: logits[idx] /= (penalty * count)
                    else: logits[idx] *= (penalty * count)
                
                # 3. Softmax manual para aplicar Top-p
                exp_l = np.exp(logits - np.max(logits))
                probs = exp_l / np.sum(exp_l)
                
                # 4. Top-p (Nucleus) Sampling
                sorted_indices = np.argsort(probs)[::-1]
                sorted_probs = probs[sorted_indices]
                cumulative_probs = np.cumsum(sorted_probs)
                
                # Identificar cuántos tokens entran en el top-p
                idx_to_remove = cumulative_probs > top_p
                # Guardar al menos el primero
                idx_to_remove[0] = False 
                
                # Filtrar
                indices_to_remove = sorted_indices[idx_to_remove]
                probs[indices_to_remove] = 0
                probs = probs / np.sum(probs)
                
                # 5. Muestreo final
                siguiente_idx = np.random.choice(len(self.vocab), p=probs)
                char_nuevo = self.int_to_char[siguiente_idx]
                
                res += char_nuevo
                indices_contexto.append(siguiente_idx)
                counts[siguiente_idx] = counts.get(siguiente_idx, 0) + 1
                
                if len(indices_contexto) > 20:
                    indices_contexto.pop(0)

                if char_nuevo == "\n" or (char_nuevo in ".!?" and len(res) > 20): break
                if char_nuevo == " " and len(res) > 80: break
                
            return res

    def aprender_gpu(self, texto, epocas=3):
        """Versión acelerada por GPU (MPS en Mac) para entrenamiento masivo"""
        try:
            import torch
            if not torch.backends.mps.is_available():
                print("⚠️ MPS acceleration not available, using CPU...")
                self.aprender(texto, epocas=epocas)
                return
        except ImportError:
            print("⚠️ PyTorch not found, using CPU...")
            self.aprender(texto, epocas=epocas)
            return

        with self.lock: # Bloquear igual que en CPU para thread-safety
            # 1. Chequear caracteres desconocidos
            desconocidos = [c for c in texto if c not in self.char_to_int]
            if desconocidos:
                self.expandir_vocabulario(list(set(desconocidos)))
                if getattr(self, 'en_sesion_gpu', False):
                    self.iniciar_sesion_gpu() # Re-iniciar si estaba activa para actualizar shapes

            device = torch.device("mps")
            self.interacciones += 1
            
            # Convertir texto a índices
            indices = [self.char_to_int[c] for c in texto if c in self.char_to_int]
            if len(indices) < 2: return
            
            # Convertir datos a tensores en GPU
            X_data = np.array(indices[:-1], dtype=np.int64)
            Y_data = np.array(indices[1:], dtype=np.int64)
            
            X_tensor = torch.from_numpy(X_data).to(device)
            Y_tensor = torch.from_numpy(Y_data).to(device)
            
            # Convertir pesos a tensores GPU (si no lo están ya)
            # Nota: Esto es costoso si se hace en cada llamada pequeña, 
            # pero para "masivo" asumimos bloques grandes.
            # Para máxima eficiencia deberíamos mantener los pesos en GPU,
            # pero para compatibilidad híbrida los movemos ida y vuelta.
            
            w_eo_torch = torch.from_numpy(self.w_eo).to(device).requires_grad_(True)
            w_os_torch = torch.from_numpy(self.w_os).to(device).requires_grad_(True)
            b_o_torch = torch.from_numpy(self.b_o).to(device).requires_grad_(True)
            b_s_torch = torch.from_numpy(self.b_s).to(device).requires_grad_(True)
            
            # Optimizador Adam en PyTorch
            optimizer = torch.optim.Adam([w_eo_torch, w_os_torch, b_o_torch, b_s_torch], lr=self.lr)
            loss_fn = torch.nn.CrossEntropyLoss()
            
            L = len(X_data)
            
            for _ in range(epocas):
                optimizer.zero_grad()
                
                # Embeddings: (L, D)
                embeddings = w_eo_torch[X_tensor]
                
                # Codificación Posicional GPU
                with torch.no_grad():
                    posiciones = torch.arange(L, device=device).unsqueeze(1)
                    div_term = torch.exp(torch.arange(0, self.n_oculta, 2, device=device) * -(np.log(10000.0) / self.n_oculta))
                    pe = torch.zeros((L, self.n_oculta), device=device)
                    pe[:, 0::2] = torch.sin(posiciones * div_term)
                    pe[:, 1::2] = torch.cos(posiciones * div_term)
                
                embeddings = embeddings + pe
                
                # Capa Oculta con Swish (SiLU en PyTorch)
                hidden = torch.nn.functional.silu(embeddings + b_o_torch)
                
                # Capa Salida
                logits = torch.matmul(hidden, w_os_torch) + b_s_torch
                
                # Loss
                loss = loss_fn(logits, Y_tensor)
                
                # Backward
                loss.backward()
                optimizer.step()
            
            # Sincronizar pesos de vuelta a CPU con detach
            self.w_eo = w_eo_torch.detach().cpu().numpy()
            self.w_os = w_os_torch.detach().cpu().numpy()
            self.b_o = b_o_torch.detach().cpu().numpy()
            self.b_s = b_s_torch.detach().cpu().numpy()
            
            # Actualizar contadores de expansión
            self.caracteres_totales += len(texto)
            if self.caracteres_totales % 2000 == 0: # Chequear expansión menos frecuente en GPU
                self.expandir_cerebro()
                # Nota: Si el cerebro se expande, los punteros self.w_eo cambian de tamaño
                # y en la próxima llamada a aprender_gpu se volverán a cargar con el nuevo tamaño.

    # --- OPTIMIZACIÓN PERSISTENTE GPU (Zero-Copy + Fast Tokenization) ---
    def iniciar_sesion_gpu(self):
        """Carga pesos en GPU y prepara tablas de traducción rápida"""
        try:
            import torch
            if not torch.backends.mps.is_available(): return False
            
            with self.lock:
                self.device = torch.device("mps")
                
                # Pre-calcular mapa de caracteres para vectorización rápida
                # Creamos un array numpy que actúa como Look-Up Table (LUT)
                # Asumimos unicode max 65536 para texto normal, o usamos dict.
                # Para máxima velocidad (aunque gasta RAM), un array directo:
                self.max_char_val = 128 # ASCII extendido basico
                for c in self.char_to_int:
                    self.max_char_val = max(self.max_char_val, ord(c))
                
                self.char_map_array = np.zeros(self.max_char_val + 1, dtype=np.int32) - 1
                for c, i in self.char_to_int.items():
                    if ord(c) <= self.max_char_val:
                        self.char_map_array[ord(c)] = i

                self.gpu_cache = {
                    'w_eo': torch.from_numpy(self.w_eo).to(self.device).requires_grad_(True),
                    'w_os': torch.from_numpy(self.w_os).to(self.device).requires_grad_(True),
                    'b_o': torch.from_numpy(self.b_o).to(self.device).requires_grad_(True),
                    'b_s': torch.from_numpy(self.b_s).to(self.device).requires_grad_(True),
                    'optimizer_state': None
                }
                
                self.gpu_optimizer = torch.optim.Adam(
                    [self.gpu_cache['w_eo'], self.gpu_cache['w_os'], 
                     self.gpu_cache['b_o'], self.gpu_cache['b_s']], 
                    lr=self.lr
                )
                self.gpu_loss_fn = torch.nn.CrossEntropyLoss()
                
                self.en_sesion_gpu = True
                print("🧠 SESIÓN GPU (V2) INICIADA: LUT compilada.")
                return True
        except Exception as e:
            print(f"Error iniciando sesión GPU: {e}")
            return False

    def aprender_bloque_gpu(self, texto, epocas=2):
        """Entrena bloque con Tokenización Vectorizada y Expansión Dinámica"""
        if not getattr(self, 'en_sesion_gpu', False):
            self.aprender_gpu(texto, epocas)
            return

        with self.lock:
            import torch
            # 1. Chequear caracteres desconocidos
            desconocidos = [c for c in texto if c not in self.char_to_int]
            if desconocidos:
                self.expandir_vocabulario(list(set(desconocidos)))
                self.iniciar_sesion_gpu() # Actualizar sesión con nuevos shapes

            self.interacciones += 1
            
            # --- TOKENIZACIÓN ULTRARÁPIDA ---
            # 1. Convertir string a buffer int32 (Unicode)
            # En Python str es unicode, difícil de acceder directo sin C.
            # Método híbrido rápido: encode utf-32 (4 bytes) y leer numpy
            # Ojo: esto es complejo. Método "Dumb but Fast":
            # Usar bytearray si es ASCII, o lista si es mix.
            # OPTIMIZACIÓN: Solo chars conocidos.
            
            # Revertimos a lista por compatibilidad unicode segura, pero optimizada
            # Si el texto es muy largo, str.translate es más rápido que loops
            # Pero necesitamos mapear a ints.
            
            # Intento de vectorización con numpy
            # codigos = np.array([ord(c) for c in texto], dtype=np.int32)
            # indices = self.char_map_array[codigos]
            # indices = indices[indices >= 0]
            
            # Fallback seguro y mejorado:
            indices = [self.char_to_int[c] for c in texto if c in self.char_to_int]
            if len(indices) < 2: return
            
            X_tensor = torch.tensor(indices[:-1], dtype=torch.long, device=self.device)
            Y_tensor = torch.tensor(indices[1:], dtype=torch.long, device=self.device)
            
            w_eo = self.gpu_cache['w_eo']
            w_os = self.gpu_cache['w_os']
            b_o = self.gpu_cache['b_o']
            b_s = self.gpu_cache['b_s']
            
            for _ in range(epocas):
                self.gpu_optimizer.zero_grad()
                embeddings = w_eo[X_tensor]
                
                # Codificación Posicional
                L_batch = X_tensor.size(0)
                posiciones = torch.arange(L_batch, device=self.device).unsqueeze(1)
                div_term = torch.exp(torch.arange(0, self.n_oculta, 2, device=self.device) * -(np.log(10000.0) / self.n_oculta))
                pe = torch.zeros((L_batch, self.n_oculta), device=self.device)
                pe[:, 0::2] = torch.sin(posiciones * div_term)
                pe[:, 1::2] = torch.cos(posiciones * div_term)
                
                embeddings = embeddings + pe
                
                hidden = torch.nn.functional.silu(embeddings + b_o)
                logits = torch.matmul(hidden, w_os) + b_s
                loss = self.gpu_loss_fn(logits, Y_tensor)
                loss.backward()
                self.gpu_optimizer.step()
                if L_batch > 1000: torch.mps.empty_cache() # Evitar fragmentación en bloques gigantes
            
            self.caracteres_totales += len(texto)
            
            # --- EXPANSIÓN DINÁMICA (Exponential Throttling) ---
            # Antes: if self.caracteres_totales % 2000 == 0
            # Ahora: Cuanto más grande la red, menos frecuentemente expande.
            # Umbral = 2000 * (1 + neuronas/500)
            umbral_expansion = 2000 * (1 + (self.n_oculta // 500))
            if self.caracteres_totales % umbral_expansion < len(texto): # Deteción aproximada de cruce
                 self.expandir_cerebro_gpu() # Nueva versión interna para GPU

    def expandir_cerebro_gpu(self):
        """Versión especial de expansión que actualiza los tensores en VRAM"""
        print(f"🚀 EXPANDING BRAIN ON GPU: {self.n_oculta} neurons...")
        # 1. Traer a CPU
        self.sincronizar_gpu_a_cpu()
        # 2. Expandir lógica CPU standard
        self.expandir_cerebro()
        # 3. Recargar a GPU (Re-init tensors)
        import torch
        with torch.no_grad():
            self.gpu_cache['w_eo'] = torch.from_numpy(self.w_eo).to(self.device).requires_grad_(True)
            self.gpu_cache['w_os'] = torch.from_numpy(self.w_os).to(self.device).requires_grad_(True)
            self.gpu_cache['b_o'] = torch.from_numpy(self.b_o).to(self.device).requires_grad_(True)
            # Recrear optimizador con nuevos parámetros
            self.gpu_optimizer = torch.optim.Adam(
                [self.gpu_cache['w_eo'], self.gpu_cache['w_os'], 
                 self.gpu_cache['b_o'], self.gpu_cache['b_s']], lr=self.lr
            )

    def sincronizar_gpu_a_cpu(self):
        """Trae los pesos de la GPU a la RAM (CPU) sin cerrar la sesión"""
        if not getattr(self, 'en_sesion_gpu', False): return

        with self.lock:
            # Detach y copy a CPU numpy
            self.w_eo = self.gpu_cache['w_eo'].detach().cpu().numpy()
            self.w_os = self.gpu_cache['w_os'].detach().cpu().numpy()
            self.b_o = self.gpu_cache['b_o'].detach().cpu().numpy()
            self.b_s = self.gpu_cache['b_s'].detach().cpu().numpy()

    def finalizar_sesion_gpu(self):
        """Cierra la sesión GPU, libera VRAM y asegura que la CPU tenga lo último"""
        if not getattr(self, 'en_sesion_gpu', False): return
        
        print("🧠 FINALIZANDO SESIÓN GPU: Sincronizando y liberando VRAM...")
        self.sincronizar_gpu_a_cpu()
        
        # Limpiar
        self.gpu_cache = {}
        self.gpu_optimizer = None
        self.en_sesion_gpu = False
        
        import torch
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

    def guardar(self, archivo):
        with self.lock:
            # Detectar si safetensors está disponible y si el archivo debe ser safetensors
            usar_safetensors = save_file is not None and archivo.endswith('.safetensors')
            
            if usar_safetensors:
                # 1. Preparar Tensores
                tensors = {
                    'w_eo': self.w_eo, 'w_os': self.w_os, 
                    'b_o': self.b_o, 'b_s': self.b_s, 
                    'm_w_eo': self.m_w_eo, 'v_w_eo': self.v_w_eo,
                    'm_w_os': self.m_w_os, 'v_w_os': self.v_w_os,
                    'm_b_o': self.m_b_o, 'v_b_o': self.v_b_o,
                    'm_b_s': self.m_b_s, 'v_b_s': self.v_b_s
                }
                
                # Sincronizar con GPU si está activa antes de guardar
                if getattr(self, 'en_sesion_gpu', False):
                    self.sincronizar_gpu_a_cpu()

                # 2. Preparar Metadata (Todo debe ser string)
                metadata = {
                    't': str(self.t),
                    'vocab': "".join(self.vocab), # String único
                    'n_oculta': str(self.n_oculta),
                    'interacciones': str(self.interacciones),
                    'caracteres_totales': str(self.caracteres_totales)
                }
                
                save_file(tensors, archivo, metadata=metadata)
                
            else:
                # Fallback a Pickle (Legacy)
                with open(archivo, 'wb') as f:
                    pickle.dump({
                        'w_eo': self.w_eo, 'w_os': self.w_os, 
                        'b_o': self.b_o, 'b_s': self.b_s, 
                        'm_w_eo': self.m_w_eo, 'v_w_eo': self.v_w_eo,
                        'm_w_os': self.m_w_os, 'v_w_os': self.v_w_os,
                        'm_b_o': self.m_b_o, 'v_b_o': self.v_b_o,
                        'm_b_s': self.m_b_s, 'v_b_s': self.v_b_s,
                        't': self.t,
                        'vocab': self.vocab, 'n_oculta': self.n_oculta,
                        'interacciones': self.interacciones,
                        'caracteres_totales': self.caracteres_totales
                    }, f)

    @staticmethod
    def cargar(archivo):
        # Detectar formato
        es_safetensors = archivo.endswith('.safetensors') and load_file is not None
        
        if es_safetensors:
            with open(archivo, 'rb') as f:
                # Leemos tensores
                tensores = load_file(archivo)
                # Hack para leer metadata: safetensors-python no expone metadata en load_file directamente de forma fácil
                # pero podemos re-instanciar con los datos conocidos.

            # RE-IMPLEMENTACIÓN MEJORADA CON safe_open SI ES POSIBLE O FALLBACK
            # Como `load_file` devuelve solo tensores, necesitamos la librería `safe_open` para metadata
            # Si no, tenemos que guardar vocab en un archivo separado o codificarlo en tensores (feo).
            # SOLUCIÓN: Usaremos `safe_open` del módulo `safetensors` base si está disponible.
            from safetensors import safe_open
            
            tensors = {}
            metadata = {}
            with safe_open(archivo, framework="numpy", device="cpu") as f:
                metadata = f.metadata()
                for k in f.keys():
                    tensors[k] = f.get_tensor(k)
            
            # Reconstruir
            n_oculta = int(metadata['n_oculta'])
            vocab_str = metadata['vocab']
            red = RedCrecimientoInfinito(vocabulario=list(vocab_str), n_oculta=n_oculta)
            
            # Asignar tensores
            red.w_eo = tensors['w_eo']
            red.w_os = tensors['w_os']
            red.b_o = tensors['b_o']
            red.b_s = tensors['b_s']
            
            red.m_w_eo = tensors.get('m_w_eo', np.zeros_like(red.w_eo))
            red.v_w_eo = tensors.get('v_w_eo', np.zeros_like(red.w_eo))
            red.m_w_os = tensors.get('m_w_os', np.zeros_like(red.w_os))
            red.v_w_os = tensors.get('v_w_os', np.zeros_like(red.w_os))
            red.m_b_o = tensors.get('m_b_o', np.zeros_like(red.b_o))
            red.v_b_o = tensors.get('v_b_o', np.zeros_like(red.b_o))
            red.m_b_s = tensors.get('m_b_s', np.zeros_like(red.b_s))
            red.v_b_s = tensors.get('v_b_s', np.zeros_like(red.b_s))
            
            # Restaurar escalares
            red.t = int(metadata.get('t', 0))
            red.interacciones = int(metadata.get('interacciones', 0))
            red.caracteres_totales = int(metadata.get('caracteres_totales', 0))
            
            return red

        else:
            # Legacy Pickle
            with open(archivo, 'rb') as f:
                d = pickle.load(f)
            red = RedCrecimientoInfinito(n_oculta=d['n_oculta'])
            red.vocab = d['vocab']
            red.char_to_int = {char: i for i, char in enumerate(red.vocab)}
            red.int_to_char = {i: char for i, char in enumerate(red.vocab)}
            red.w_eo, red.w_os, red.b_o, red.b_s = d['w_eo'], d['w_os'], d['b_o'], d['b_s']
            
            # Cargar buffers de Adam si existen
            red.m_w_eo = d.get('m_w_eo', np.zeros_like(red.w_eo))
            red.v_w_eo = d.get('v_w_eo', np.zeros_like(red.w_eo))
            red.m_w_os = d.get('m_w_os', np.zeros_like(red.w_os))
            red.v_w_os = d.get('v_w_os', np.zeros_like(red.w_os))
            red.m_b_o = d.get('m_b_o', np.zeros_like(red.b_o))
            red.v_b_o = d.get('v_b_o', np.zeros_like(red.b_o))
            red.m_b_s = d.get('m_b_s', np.zeros_like(red.b_s))
            red.v_b_s = d.get('v_b_s', np.zeros_like(red.b_s))
            red.t = d.get('t', 0)
            
            red.interacciones = d.get('interacciones', 0)
            red.caracteres_totales = d.get('caracteres_totales', 0)
            
            # Forzar float32 para optimización
            red.w_eo = red.w_eo.astype(np.float32)
            red.w_os = red.w_os.astype(np.float32)
            red.b_o = red.b_o.astype(np.float32)
            red.b_s = red.b_s.astype(np.float32)
            red.m_w_eo = red.m_w_eo.astype(np.float32)
            red.v_w_eo = red.v_w_eo.astype(np.float32)
            red.m_w_os = red.m_w_os.astype(np.float32)
            red.v_w_os = red.v_w_os.astype(np.float32)
            red.m_b_o = red.m_b_o.astype(np.float32)
            red.v_b_o = red.v_b_o.astype(np.float32)
            red.m_b_s = red.m_b_s.astype(np.float32)
            red.v_b_s = red.v_b_s.astype(np.float32)
            
            return red

if __name__ == "__main__":
    archivo = "cerebro_ia.safetensors"
    if os.path.exists(archivo): ia = RedCrecimientoInfinito.cargar(archivo)
    elif os.path.exists("cerebro_ia.pkl"): ia = RedCrecimientoInfinito.cargar("cerebro_ia.pkl")
    else: ia = RedCrecimientoInfinito(" abcdefghijklmnopqrstuvwxyzáéíóúñ,.¿?¡! ")
    
    while True:
        u = input("Tu: ").lower()
        if u == "adiós": break
        ia.aprender(u)
        print("IA:", ia.generar_respuesta(u))
        ia.guardar(archivo)
