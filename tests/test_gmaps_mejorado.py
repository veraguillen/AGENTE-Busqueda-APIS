#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de prueba para el AgenteGMaps mejorado con mecanismo de fallback.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Agregar el directorio raíz al path para poder importar los módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar el AgenteGMaps
from agents.agente_gmaps import AgenteGMaps, search_business

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cargar_variables_entorno():
    """Carga variables de entorno desde archivo .env"""
    load_dotenv()
    print("Variables de entorno cargadas")
    
    # Verificar claves API necesarias
    rapidapi_key = os.environ.get("RAPIDAPI_KEY") or os.environ.get("GOOGLE_MAPS_DATA_API_KEY")
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    
    if rapidapi_key:
        print(f"✅ RapidAPI Key encontrada: {rapidapi_key[:4]}...{rapidapi_key[-4:]}")
    else:
        print("❌ No se encontró RapidAPI Key en las variables de entorno")
    
    if google_api_key:
        print(f"✅ Google API Key encontrada: {google_api_key[:4]}...{google_api_key[-4:]}")
    else:
        print("❌ No se encontró Google API Key en las variables de entorno")
    
    return rapidapi_key, google_api_key

def test_rapidapi_maps_data(api_key, seller_name):
    """Prueba la funcionalidad de RapidAPI Maps Data"""
    print(f"\n1. Probando RapidAPI Maps Data con vendedor: '{seller_name}'")
    
    try:
        # Crear instancia del agente con la clave de RapidAPI
        agente = AgenteGMaps(google_api_key=api_key)
        
        # Intentar búsqueda solo con RapidAPI (sin fallback)
        print("2. Intentando buscar negocio usando solo RapidAPI Maps Data...")
        resultado = agente._try_rapidapi_maps_data(seller_name)
        
        # Mostrar resultado
        print(f"3. Resultado: status={resultado.get('status')}")
        print(json.dumps(resultado, indent=2, ensure_ascii=False)[:500])
        
        return resultado.get("status") == "ok"
    
    except Exception as e:
        print(f"❌ Error probando RapidAPI Maps Data: {str(e)}")
        return False

def test_google_places_direct(api_key, seller_name):
    """Prueba la búsqueda directa con Google Places API"""
    print(f"\n1. Probando Google Places API directa con vendedor: '{seller_name}'")
    
    try:
        # Crear instancia del agente (clave no importa para este test)
        agente = AgenteGMaps(google_api_key="dummy")
        
        # Intentar búsqueda directa con Google Places
        print("2. Intentando buscar negocio usando Google Places API directamente...")
        resultado = agente._try_google_places_direct(seller_name, api_key)
        
        # Mostrar resultado
        print(f"3. Resultado: status={resultado.get('status')}")
        print(json.dumps(resultado, indent=2, ensure_ascii=False)[:500])
        
        return resultado.get("status") == "ok"
    
    except Exception as e:
        print(f"❌ Error probando Google Places API directa: {str(e)}")
        return False

def test_full_integration_with_fallback(rapidapi_key, google_api_key, seller_name):
    """Prueba la integración completa con mecanismo de fallback"""
    print(f"\n1. Probando integración completa con fallback para vendedor: '{seller_name}'")
    
    try:
        # Crear instancia del agente con ambas claves
        agente = AgenteGMaps(google_api_key=rapidapi_key)
        
        # Intentar búsqueda con mecanismo de fallback
        print("2. Intentando buscar negocio con mecanismo de fallback...")
        resultado = agente.find_business(seller_name, google_api_key=google_api_key)
        
        # Mostrar resultado
        print(f"3. Resultado: status={resultado.get('status')}")
        
        if resultado.get("status") == "ok" and resultado.get("data"):
            print("✅ Búsqueda exitosa con datos encontrados")
            print(json.dumps(resultado, indent=2, ensure_ascii=False)[:500])
            return True
        else:
            print(f"❌ No se encontraron datos. Mensaje: {resultado.get('message')}")
            return False
    
    except Exception as e:
        print(f"❌ Error en integración completa: {str(e)}")
        return False

def test_convenience_function(api_key, seller_name):
    """Prueba la función de conveniencia search_business"""
    print(f"\n1. Probando función search_business con vendedor: '{seller_name}'")
    
    try:
        # Usar la función de conveniencia
        print("2. Llamando a search_business...")
        resultado = search_business(seller_name, api_key, use_fallback=True)
        
        # Mostrar resultado
        print(f"3. Resultado: status={resultado.get('status')}")
        
        if resultado.get("status") == "ok" and resultado.get("data"):
            print("✅ Búsqueda exitosa con datos encontrados")
            print(json.dumps(resultado, indent=2, ensure_ascii=False)[:500])
            return True
        else:
            print(f"❌ No se encontraron datos. Mensaje: {resultado.get('message')}")
            return False
    
    except Exception as e:
        print(f"❌ Error usando search_business: {str(e)}")
        return False

if __name__ == "__main__":
    # Cargar variables de entorno
    rapidapi_key, google_api_key = cargar_variables_entorno()
    
    if not rapidapi_key and not google_api_key:
        print("❌ No se encontraron claves API necesarias para ejecutar las pruebas")
        sys.exit(1)
    
    # Nombres de vendedores para pruebas
    vendedores = [
        "Al Click",
        "Nisuta Argentina", 
        "DarksoftShop"
    ]
    
    # Ejecutar pruebas para cada vendedor
    for vendedor in vendedores:
        print("\n" + "=" * 80)
        print(f"PROBANDO VENDEDOR: '{vendedor}'")
        print("=" * 80)
        
        # Prueba 1: RapidAPI Maps Data
        if rapidapi_key:
            success_rapidapi = test_rapidapi_maps_data(rapidapi_key, vendedor)
            print(f"Resultado RapidAPI Maps Data: {'✅ ÉXITO' if success_rapidapi else '❌ FALLÓ'}")
        
        # Prueba 2: Google Places API directa
        if google_api_key:
            success_google = test_google_places_direct(google_api_key, vendedor)
            print(f"Resultado Google Places API: {'✅ ÉXITO' if success_google else '❌ FALLÓ'}")
        
        # Prueba 3: Integración completa con fallback
        if rapidapi_key and google_api_key:
            success_integration = test_full_integration_with_fallback(rapidapi_key, google_api_key, vendedor)
            print(f"Resultado integración con fallback: {'✅ ÉXITO' if success_integration else '❌ FALLÓ'}")
        
        # Prueba 4: Función de conveniencia
        if rapidapi_key or google_api_key:
            key_to_use = rapidapi_key if rapidapi_key else google_api_key
            success_convenience = test_convenience_function(key_to_use, vendedor)
            print(f"Resultado función search_business: {'✅ ÉXITO' if success_convenience else '❌ FALLÓ'}")
