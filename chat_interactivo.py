import numpy as np
import pickle
import time
import sys
import os
import threading

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
            
            # Expandir Sesgos
            self.b_o = np.concatenate([self.b_o, np.zeros((1, incremento), dtype=np.float32)], axis=1)
            
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
            
            self.hidden = np.tanh(self.emb_with_context + self.b_o).astype(np.float32)
            self.output = self.softmax(np.dot(self.hidden, self.w_os) + self.b_s)
            return self.output

    def aprender(self, texto, lr=None, epocas=3):
        with self.lock:
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
                
                # Gradiente hacia la capa oculta
                d_hidden = np.dot(dz_salida, self.w_os.T) * (1 - self.hidden**2)
                
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
        """Simula el sueño: consolida memoria"""
        with self.lock:
            print(f"\n💤 MAGI entrando en fase de sueño profundo...")
            
            pesos_eo_abs = np.abs(self.w_eo)
            pesos_os_abs = np.abs(self.w_os)
            
            umbral_eo = np.percentile(pesos_eo_abs, umbral_poda * 100)
            umbral_os = np.percentile(pesos_os_abs, umbral_poda * 100)
            
            conexiones_antes_eo = np.count_nonzero(pesos_eo_abs > 1e-10)
            conexiones_antes_os = np.count_nonzero(pesos_os_abs > 1e-10)
            
            mascara_poda_eo = pesos_eo_abs < umbral_eo
            mascara_poda_os = pesos_os_abs < umbral_os
            
            self.w_eo[mascara_poda_eo] = 0
            self.w_os[mascara_poda_os] = 0
            
            self.m_w_eo[mascara_poda_eo] = 0
            self.v_w_eo[mascara_poda_eo] = 0
            self.m_w_os[mascara_poda_os] = 0
            self.v_w_os[mascara_poda_os] = 0
            
            conexiones_despues_eo = np.count_nonzero(np.abs(self.w_eo) > 1e-10)
            conexiones_despues_os = np.count_nonzero(np.abs(self.w_os) > 1e-10)
            
            podadas_eo = conexiones_antes_eo - conexiones_despues_eo
            podadas_os = conexiones_antes_os - conexiones_despues_os
            
            umbral_fuerte_eo = np.percentile(pesos_eo_abs, 90)
            umbral_fuerte_os = np.percentile(pesos_os_abs, 90)
            
            mascara_refuerzo_eo = pesos_eo_abs > umbral_fuerte_eo
            mascara_refuerzo_os = pesos_os_abs > umbral_fuerte_os
            
            self.w_eo[mascara_refuerzo_eo] *= factor_refuerzo
            self.w_os[mascara_refuerzo_os] *= factor_refuerzo
            
            reforzadas_eo = np.count_nonzero(mascara_refuerzo_eo)
            reforzadas_os = np.count_nonzero(mascara_refuerzo_os)
            
            decay = 0.9995
            self.w_eo *= decay
            self.w_os *= decay
            
            self.b_o = np.clip(self.b_o, -2, 2)
            self.b_s = np.clip(self.b_s, -2, 2)
            
            return {
                'podadas': podadas_eo + podadas_os,
                'reforzadas': reforzadas_eo + reforzadas_os,
                'activas': conexiones_despues_eo + conexiones_despues_os
            }

    def generar_respuesta(self, semilla, longitud=80):
        with self.lock:
            # Convertir semilla a índices (máximo los últimos 10 para contexto inicial)
            indices_contexto = [self.char_to_int[c] for c in semilla if c in self.char_to_int]
            if not indices_contexto:
                indices_contexto = [self.char_to_int[np.random.choice(self.vocab)]]
                
            res = ""
            for _ in range(longitud):
                # Usar los últimos N caracteres como contexto para la predicción
                # Pasamos la ventana actual al forward
                input_seq = indices_contexto[-10:]
                prediccion_batch = self.forward(input_seq)
                
                # La predicción para el siguiente caracter es la última del batch
                preds = prediccion_batch[-1]
                
                # Aplicar temperatura para variabilidad
                preds = np.log(preds + self.eps) / 0.7
                exp_preds = np.exp(preds)
                probabilidades = exp_preds / np.sum(exp_preds)
                
                # Muestreo
                siguiente_idx = np.random.choice(len(self.vocab), p=probabilidades)
                char_nuevo = self.int_to_char[siguiente_idx]
                
                res += char_nuevo
                indices_contexto.append(siguiente_idx)
                
                # Mantener buffer de contexto manejable
                if len(indices_contexto) > 20:
                    indices_contexto.pop(0)

                if char_nuevo in ".\n" or (char_nuevo == " " and len(res) > 50): break
            return res

    def guardar(self, archivo):
        with self.lock:
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
    archivo = "cerebro_ia.pkl"
    if os.path.exists(archivo): ia = RedCrecimientoInfinito.cargar(archivo)
    else: ia = RedCrecimientoInfinito(" abcdefghijklmnopqrstuvwxyzáéíóúñ,.¿?¡! ")
    
    while True:
        u = input("Tu: ").lower()
        if u == "adiós": break
        ia.aprender(u)
        print("IA:", ia.generar_respuesta(u))
        ia.guardar(archivo)
