#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Este script prueba la integración final de los agentes y el orquestador.
Versión mejorada para utilizar el mecanismo de fallback del AgenteGMaps.
"""

import os
import sys
import json
import logging
import time
import traceback
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar directorio padre al path para poder importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print(f"Python path: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))}")

def main():
    try:
        # Importar agentes
        from agents.agente_gmaps import AgenteGMaps, search_business
        
        # Ejecución de pruebas
        test_agente_gmaps_con_fallback()
        test_integrado_con_search_business()
    
    except Exception as e:
        print(f"\n❌ ERROR GENERAL: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

def cargar_claves_api():
    """Carga y verifica las claves API del archivo .env"""
    # Cargar variables de entorno
    load_dotenv()
    print("Variables de entorno cargadas")
    
    # Obtener claves API
    rapidapi_key = os.getenv("RAPIDAPI_KEY") or os.getenv("GOOGLE_MAPS_DATA_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    # Verificar disponibilidad de claves
    if rapidapi_key:
        print(f"✅ RapidAPI Key encontrada: {rapidapi_key[:4]}...{rapidapi_key[-5:]}")
    else:
        print("⚠️ No se encontró clave de RapidAPI")
    
    if google_api_key:
        print(f"✅ Google API Key encontrada: {google_api_key[:4]}...{google_api_key[-5:]}")
    else:
        print("⚠️ No se encontró clave de Google API")
    
    return rapidapi_key, google_api_key

def test_agente_gmaps_con_fallback():
    """Prueba el AgenteGMaps con mecanismo de fallback"""
    print("\n=== PRUEBA 1: AgenteGMaps con fallback ====")
    
    from agents.agente_gmaps import AgenteGMaps
    
    # Cargar claves API
    rapidapi_key, google_api_key = cargar_claves_api()
    
    if not rapidapi_key and not google_api_key:
        print("❌ ERROR: No se encontraron claves API necesarias para la prueba")
        return
    
    # Lista de vendedores para probar
    vendedores = [
        "Al Click",
        "Nisuta Argentina",
        "DarksoftShop"
    ]
    
    # Probar con cada vendedor
    for vendedor in vendedores:
        print(f"\n==== Probando vendedor: '{vendedor}' ====")
        
        try:
            start_time = time.time()
            
            # Crear instancia del agente con ambas claves para probar el mecanismo de fallback
            print("1. Creando instancia del agente con mecanismo de fallback...")
            agente = AgenteGMaps(google_api_key=rapidapi_key)
            
            print(f"2. Buscando información del vendedor: '{vendedor}'")
            resultado = agente.find_business(vendedor, google_api_key=google_api_key)
            
            # Verificar resultado
            if resultado.get("status") == "ok" and resultado.get("data"):
                print(f"✅ Búsqueda exitosa en {time.time() - start_time:.2f} segundos")
                print(f"   Se encontraron {len(resultado['data'])} resultados")
                
                # Mostrar información del primer resultado
                if resultado['data']:
                    first_result = resultado['data'][0]
                    print(f"   Primer resultado: {first_result['name']}")
                    print(f"   Dirección: {first_result['full_address']}")
                    if first_result['phone_number']:
                        print(f"   Teléfono: {first_result['phone_number']}")
                    print(f"   Enlace: {first_result['place_link']}")
            else:
                print(f"❌ No se encontraron resultados: {resultado.get('message')}")
            
            print("\nRespuesta completa:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False)[:1000])
        
        except Exception as e:
            print(f"❌ Error procesando vendedor '{vendedor}': {str(e)}")

def test_integrado_con_search_business():
    """Prueba la función de conveniencia search_business"""
    print("\n=== PRUEBA 2: Función de conveniencia search_business ====")
    
    from agents.agente_gmaps import search_business
    
    # Cargar claves API
    rapidapi_key, google_api_key = cargar_claves_api()
    
    if not rapidapi_key and not google_api_key:
        print("❌ ERROR: No se encontraron claves API necesarias para la prueba")
        return
    
    # Clave a utilizar (preferir RapidAPI, fallback a Google)
    api_key_to_use = rapidapi_key or google_api_key
    
    # Vendedor a buscar
    vendedor = "Al Click"
    
    print(f"\n==== Usando search_business() para '{vendedor}' ====")
    try:
        # Usar la función de conveniencia con fallback automático
        resultado = search_business(vendedor, api_key_to_use, use_fallback=True)
        
        # Verificar resultado
        if resultado.get("status") == "ok" and resultado.get("data"):
            print(f"✅ Búsqueda exitosa con search_business()")
            print(f"   Se encontraron {len(resultado['data'])} resultados")
        else:
            print(f"❌ No se encontraron resultados: {resultado.get('message')}")
        
        print("Respuesta:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False)[:500])
    
    except Exception as e:
        print(f"❌ Error usando search_business: {str(e)}")

# Punto de entrada principal
if __name__ == "__main__":
    main()