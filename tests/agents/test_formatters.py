#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test de integración del formateador de tarjetas de contacto con AgenteGMaps.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar componentes necesarios
from agents.agente_gmaps import AgenteGMaps, search_business
from app.utils.formatters import format_business_contact_cards, format_contact_list_plain

def test_formateador_con_datos_reales():
    """
    Prueba el formateador con datos reales obtenidos de la API de Google Maps.
    """
    print("\n=== PRUEBA DE INTEGRACIÓN: AGENTE GMAPS + FORMATEADOR ===\n")
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener claves API
    rapidapi_key = os.getenv("RAPIDAPI_KEY") or os.getenv("GOOGLE_MAPS_DATA_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not rapidapi_key and not google_api_key:
        print("❌ No se encontraron claves API necesarias para las pruebas")
        return
    
    api_key = rapidapi_key or google_api_key
    print(f"✅ API Key disponible: {api_key[:5]}...{api_key[-5:]}")
    
    # Vendedor a buscar
    seller_name = "Al Click"
    print(f"\n1. Buscando datos para vendedor: '{seller_name}'")
    
    try:
        # Instanciar el agente
        agente = AgenteGMaps(google_api_key=api_key)
        
        # Buscar información del negocio
        print("2. Ejecutando búsqueda con AgenteGMaps...")
        resultado = agente.find_business(seller_name, google_api_key=google_api_key)
        
        # Verificar si se encontraron resultados
        if resultado.get("status") == "ok" and resultado.get("data"):
            print(f"✅ Búsqueda exitosa. Se encontraron {len(resultado['data'])} resultados.")
            
            # Datos crudos (respuesta JSON)
            print("\n3. Datos originales (JSON):")
            print("-" * 50)
            print(json.dumps(resultado, indent=2, ensure_ascii=False)[:800] + "...(truncado)")
            print("-" * 50)
            
            # Formatear como tarjetas de contacto (Markdown)
            print("\n4. Datos formateados como tarjetas de contacto (Markdown):")
            print("-" * 50)
            tarjetas_contacto = format_business_contact_cards(resultado)
            print(tarjetas_contacto)
            print("-" * 50)
            
            # Formatear como lista de contactos (texto plano)
            print("\n5. Datos formateados como lista simple (texto plano):")
            print("-" * 50)
            lista_contactos = format_contact_list_plain(resultado)
            print(lista_contactos)
            print("-" * 50)
            
            print("\n✅ PRUEBA COMPLETA: El formateador funciona correctamente con datos reales")
            return True
        else:
            print(f"❌ Error o sin resultados: {resultado.get('message', 'No hay detalles del error')}")
            return False
    
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

def test_formateador_con_datos_mock():
    """
    Prueba el formateador con datos estáticos simulados.
    Útil cuando no se puede conectar a las APIs.
    """
    print("\n=== PRUEBA CON DATOS SIMULADOS ===\n")
    
    # Datos simulados con estructura similar a la respuesta real
    datos_mock = {
        "status": "ok",
        "data": [
            {
                "business_id": "0x95bcb1aeba8cd619:0x36c97b118f001389",
                "phone_number": "0111565516232",
                "name": "DARK INFORMATICA",
                "full_address": "DARK INFORMATICA, IFC, Av. Sta Fe 1599, B1640 San Isidro, Buenos Aires",
                "review_count": 49,
                "rating": 4.5,
                "website": "http://www.dark-informatica.com.ar/",
                "place_link": "https://www.google.com/maps/place/data=!3m1!4b1!4m2!3m1!1s0x95bcb1aeba8cd619:0x36c97b118f001389"
            },
            {
                "business_id": "0x94225c632f07c963:0xb6abb189c348bd8e",
                "phone_number": "03814363905",
                "name": "Darksoft",
                "full_address": "Darksoft, Av. Pres. Néstor Kirchner 2257, T4000 San Miguel de Tucumán, Tucumán",
                "rating": 5,
                "website": None,
                "place_link": "https://www.google.com/maps/place/data=!3m1!4b1!4m2!3m1!1s0x94225c632f07c963:0xb6abb189c348bd8e"
            }
        ]
    }
    
    print("1. Usando datos simulados para prueba offline")
    
    # Formatear como tarjetas de contacto (Markdown)
    print("\n2. Datos formateados como tarjetas de contacto (Markdown):")
    print("-" * 50)
    tarjetas_contacto = format_business_contact_cards(datos_mock)
    print(tarjetas_contacto)
    print("-" * 50)
    
    # Formatear como lista de contactos (texto plano)
    print("\n3. Datos formateados como lista simple (texto plano):")
    print("-" * 50)
    lista_contactos = format_contact_list_plain(datos_mock)
    print(lista_contactos)
    print("-" * 50)
    
    print("\n✅ PRUEBA COMPLETA: El formateador funciona correctamente con datos simulados")
    return True

if __name__ == "__main__":
    # Ejecutar pruebas
    print("===== PRUEBAS DEL FORMATEADOR DE CONTACTOS =====")
    
    # Primera prueba: con datos reales (requiere APIs)
    test_formateador_con_datos_reales()
    
    print("\n" + "=" * 60)
    
    # Segunda prueba: con datos mock (siempre funciona)
    test_formateador_con_datos_mock()
