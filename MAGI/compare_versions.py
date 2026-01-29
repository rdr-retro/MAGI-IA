#!/usr/bin/env python3
"""
Script de comparación entre versión original y refactorizada
"""
import os

def count_lines(filepath):
    """Cuenta las líneas de un archivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def main():
    base_path = "/Users/rauldiazgutierrez/Desktop/neurona/MAGI/src"
    
    # Archivos originales
    original = os.path.join(base_path, "gui_magi_pyside.py")
    
    # Archivos refactorizados
    refactored_files = {
        "Main": os.path.join(base_path, "gui_magi_refactored.py"),
        "Signals": os.path.join(base_path, "core/signals.py"),
        "Brain Manager": os.path.join(base_path, "core/brain_manager.py"),
        "Widgets": os.path.join(base_path, "ui/widgets.py"),
        "Styles": os.path.join(base_path, "ui/styles.py"),
    }
    
    print("=" * 70)
    print("📊 COMPARACIÓN: Original vs Refactorizado")
    print("=" * 70)
    print()
    
    # Original
    original_lines = count_lines(original)
    print(f"📄 VERSIÓN ORIGINAL")
    print(f"   Archivo: gui_magi_pyside.py")
    print(f"   Líneas: {original_lines:,}")
    print(f"   Archivos: 1")
    print()
    
    # Refactorizado
    print(f"📦 VERSIÓN REFACTORIZADA")
    total_lines = 0
    for name, filepath in refactored_files.items():
        lines = count_lines(filepath)
        total_lines += lines
        print(f"   {name:20s}: {lines:4,} líneas")
    
    print(f"   {'-' * 40}")
    print(f"   {'TOTAL':20s}: {total_lines:4,} líneas")
    print(f"   Archivos: {len(refactored_files)}")
    print()
    
    # Comparación
    print("=" * 70)
    print("📈 ANÁLISIS")
    print("=" * 70)
    print()
    
    main_reduction = ((original_lines - count_lines(refactored_files["Main"])) / original_lines) * 100
    print(f"✅ Reducción en archivo principal: {main_reduction:.1f}%")
    print(f"   De {original_lines:,} a {count_lines(refactored_files['Main']):,} líneas")
    print()
    
    print(f"📁 Modularización:")
    print(f"   Antes: 1 archivo monolítico")
    print(f"   Después: {len(refactored_files)} módulos especializados")
    print()
    
    print(f"🎯 Beneficios:")
    print(f"   ✓ Código más mantenible")
    print(f"   ✓ Mejor separación de responsabilidades")
    print(f"   ✓ Más fácil de testear")
    print(f"   ✓ Reutilizable")
    print(f"   ✓ Escalable")
    print()
    
    print("=" * 70)

if __name__ == "__main__":
    main()
