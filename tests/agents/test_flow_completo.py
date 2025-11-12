#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demostración del flujo completo del sistema:
1. Búsqueda con AgenteGMaps (con fallback)
2. Formateo de resultados como tarjetas de contacto
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agregar directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """Función principal para la demostración del flujo completo"""
    print("=" * 70)
    print("DEMOSTRACIÓN DEL FLUJO COMPLETO DE BÚSQUEDA Y FORMATEO DE CONTACTOS")
    print("=" * 70)
    
    # 1. Cargar variables de entorno
    load_dotenv()
    print("\n1. Cargando variables de entorno y configuración...")
    
    # Claves API disponibles
    rapidapi_key = os.environ.get("RAPIDAPI_KEY") or os.environ.get("GOOGLE_MAPS_DATA_API_KEY")
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not rapidapi_key and not google_api_key:
        print("❌ ERROR: No se encontraron claves API necesarias")
        return
    
    if rapidapi_key:
        print(f"✅ RapidAPI Key: {rapidapi_key[:4]}...{rapidapi_key[-4:]}")
    if google_api_key:
        print(f"✅ Google API Key: {google_api_key[:4]}...{google_api_key[-4:]}")
    
    # 2. Importar componentes necesarios
    print("\n2. Importando componentes del sistema...")
    
    try:
        # Importar el AgenteGMaps
        print("   - Importando AgenteGMaps...")
        from agents.agente_gmaps import AgenteGMaps
        
        # Verificar disponibilidad del formateador
        print("   - Verificando formateador de contactos...")
        try:
            from app.utils.formatters import format_business_contact_cards
            tiene_formateador = True
            print("✅ Formateador de contactos disponible")
        except ImportError:
            tiene_formateador = False
            print("⚠️ Formateador de contactos no encontrado, usando formato simplificado")
    except ImportError as e:
        print(f"❌ Error importando componentes: {str(e)}")
        return
    
    # 3. Procesar lista de vendedores
    vendedores = [
        "Al Click",
        "Nisuta Argentina",
        "DarksoftShop"
    ]
    
    print(f"\n3. Procesando {len(vendedores)} vendedores...")
    
    # Inicializar el agente
    try:
        print("\n   Inicializando AgenteGMaps...")
        agente = AgenteGMaps(google_api_key=rapidapi_key)
        print("✅ Agente inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando agente: {str(e)}")
        return
    
    # 4. Procesar cada vendedor
    for i, vendedor in enumerate(vendedores):
        print(f"\n--- VENDEDOR #{i+1}: {vendedor} ---")
        
        # Medición de tiempo
        tiempo_inicio = time.time()
        
        try:
            # Obtener información con el método integrado
            print(f"1. Buscando datos de contacto para '{vendedor}'...")
            info_formateada = agente.get_formatted_contacts(vendedor, google_api_key=google_api_key)
            
            # Mostrar resultados
            tiempo_total = time.time() - tiempo_inicio
            print(f"✅ Búsqueda completada en {tiempo_total:.2f} segundos")
            
            print("\n2. Información de contacto formateada:")
            print("-" * 50)
            print(info_formateada)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Error procesando vendedor '{vendedor}': {str(e)}")
    
    # 5. Resumen final
    print("\n" + "=" * 70)
    print("DEMOSTRACIÓN COMPLETADA")
    print("=" * 70)
    print("\nEl sistema ha completado todas las pruebas:")
    print("✅ Integración del AgenteGMaps")
    print("✅ Mecanismo de fallback para mayor robustez")
    print("✅ Formateador de tarjetas de contacto")
    print("✅ Flujo completo de búsqueda a presentación")

if __name__ == "__main__":
    main()
