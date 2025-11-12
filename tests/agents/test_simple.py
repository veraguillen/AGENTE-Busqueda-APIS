#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para verificar que la estructura del proyecto y las importaciones funcionan correctamente
"""

import sys
import os
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_project_structure():
    """Prueba la estructura del proyecto verificando las importaciones"""
    # Verificar importación de agentes
    from agents import AgenteML, AgenteFiltro, AgenteGoogle, AgenteRanking
    
    # Verificar acceso a versiones de AgenteML
    from agents import AgenteMlSimple, AgenteMlComplex
    
    # Verificar servicios
    from services import cache_manager, config_manager
    
    # Verificar estructura de directorios
    dirs_to_check = ["agents", "app", "services", "functions"]
    for dir_name in dirs_to_check:
        assert os.path.isdir(dir_name), f"Directorio {dir_name} no encontrado"
    
    # Verificar archivo puente de AgenteML
    assert os.path.exists(os.path.join("app", "agente_ml.py")), \
           "Archivo puente app/agente_ml.py no encontrado"

if __name__ == "__main__":
    print("=" * 80)
    print("PRUEBA DE ESTRUCTURA DEL PROYECTO AGENTE BÚSQUEDA")
    print("=" * 80)
    
    try:
        test_project_structure()
        print("\n" + "=" * 80)
        print("✅ La estructura del proyecto es correcta")
        print("""
Para cambiar entre versiones del AgenteML:
1. Editar el archivo agents/__init__.py
2. Comentar/descomentar las líneas correspondientes:
   - Para versión simple (actual): from .agente_ml_simple import AgenteML
   - Para versión compleja: from .agente_ml_complex import AgenteML
""")
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        print("❌ Hay problemas en la estructura del proyecto")
    finally:
        print("=" * 80)
