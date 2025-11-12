#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script simple para depurar las importaciones y funcionamiento básico
"""

import os
import sys
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Asegurar que podemos acceder a los módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("Verificando importaciones...")

try:
    # Verificar importación del orquestador
    print("Importando Orquestador...")
    from app.orquestador import Orquestador
    print("Importación exitosa")
    
    # Intentar crear una instancia del orquestador
    print("Creando instancia del Orquestador...")
    orq = Orquestador()
    print("Instancia creada correctamente")
    
    # Verificar acceso al agente de contactos
    print("Verificando AgenteContacts...")
    if hasattr(orq, 'agente_contacts'):
        print("AgenteContacts disponible")
    else:
        print("Error: AgenteContacts no está disponible en el orquestador")
    
    # Verificar configuración de variables de entorno
    print("\nVerificando variables de entorno necesarias:")
    env_vars = ["GOOGLE_API_KEY", "GOOGLE_CSE_ID", "RAPIDAPI_KEY"]
    for var in env_vars:
        if var in os.environ:
            print(f"✓ {var} está configurada")
        else:
            print(f"✗ {var} NO está configurada")
    
except Exception as e:
    print(f"Error durante la verificación: {str(e)}")

print("\nVerificación completada")
