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
            self.w_eo = np.random.randn(n_vocab, self.n_oculta) * np.sqrt(1. / n_vocab)
            self.w_os = np.random.randn(self.n_oculta, n_vocab) * np.sqrt(1. / self.n_oculta)
            self.b_o = np.zeros((1, self.n_oculta))
            self.b_s = np.zeros((1, n_vocab))
            
            # Buffers para Adam
            self.m_w_eo, self.v_w_eo = np.zeros_like(self.w_eo), np.zeros_like(self.w_eo)
            self.m_w_os, self.v_w_os = np.zeros_like(self.w_os), np.zeros_like(self.w_os)
            self.m_b_o, self.v_b_o = np.zeros_like(self.b_o), np.zeros_like(self.b_o)
            self.m_b_s, self.v_b_s = np.zeros_like(self.b_s), np.zeros_like(self.b_s)

    def expandir_cerebro(self):
        """Añade neuronas nuevas manteniendo lo aprendido"""
        with self.lock:
            incremento = 64
            n_vocab = len(self.vocab)
            nueva_n_oculta = self.n_oculta + incremento
            
            print(f"\n🧠 ¡EVOLUCIÓN! Expandiendo a {nueva_n_oculta} neuronas...")
            
            # Expandir Pesos Entada-Oculta
            nuevos_w_eo = np.random.randn(n_vocab, nueva_n_oculta) * np.sqrt(1. / n_vocab)
            nuevos_w_eo[:, :self.n_oculta] = self.w_eo
            self.w_eo = nuevos_w_eo
            
            # Expandir Pesos Oculta-Salida
            nuevos_w_os = np.random.randn(nueva_n_oculta, n_vocab) * np.sqrt(1. / nueva_n_oculta)
            nuevos_w_os[:self.n_oculta, :] = self.w_os
            self.w_os = nuevos_w_os
            
            # Expandir Sesgos
            self.b_o = np.concatenate([self.b_o, np.zeros((1, incremento))], axis=1)
            
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
        e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e_x / e_x.sum(axis=1, keepdims=True)

    def forward(self, x_indices):
        """Forward optimizado"""
        with self.lock:
            # self.hidden es un buffer compartido, debe protegerse por el lock de aprender()
            self.hidden = np.tanh(self.w_eo[x_indices] + self.b_o)
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
            
            for _ in range(epocas):
                self.t += 1
                probabilidades = self.forward(X)
                
                dz_salida = probabilidades.copy()
                dz_salida[np.arange(len(Y)), Y] -= 1
                dz_salida /= len(Y)
                
                dw_os = np.dot(self.hidden.T, dz_salida)
                db_s = np.sum(dz_salida, axis=0, keepdims=True)
                
                d_hidden = np.dot(dz_salida, self.w_os.T) * (1 - self.hidden**2)
                
                dw_eo = np.zeros_like(self.w_eo)
                np.add.at(dw_eo, X, d_hidden)
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

            ultimo_bloque = self.caracteres_totales // 500
            self.caracteres_totales += len(X)
            nuevo_bloque = self.caracteres_totales // 500
            
            if nuevo_bloque > ultimo_bloque:
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
            if not semilla or semilla[-1] not in self.char_to_int:
                char_actual = np.random.choice(self.vocab)
            else:
                char_actual = semilla[-1]
                
            res = ""
            for _ in range(longitud):
                idx = self.char_to_int[char_actual]
                prediccion = self.forward([idx])
                
                preds = prediccion[0]
                preds = np.log(preds + self.eps) / 0.7
                exp_preds = np.exp(preds)
                probabilidades = exp_preds / np.sum(exp_preds)
                
                siguiente_idx = np.random.choice(len(self.vocab), p=probabilidades)
                char_actual = self.int_to_char[siguiente_idx]
                res += char_actual
                if char_actual in ".\n" or (char_actual == " " and len(res) > 50): break
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
