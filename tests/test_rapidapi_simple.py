#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba simple para la API de MercadoLibre a través de RapidAPI
"""

import os
import json
import logging
from dotenv import load_dotenv
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rapidapi_simple_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_rapidapi_connection():
    """Prueba la conexión con la API de MercadoLibre a través de RapidAPI"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Obtener credenciales
        rapidapi_key = os.getenv("RAPIDAPI_KEY")
        rapidapi_host = os.getenv("RAPIDAPI_HOST", "mercado-libre7.p.rapidapi.com")
        
        if not rapidapi_key:
            logger.error("No se encontró RAPIDAPI_KEY en las variables de entorno")
            return False
        
        logger.info(f"Probando conexión con RapidAPI - Host: {rapidapi_host}")
        
        # Configurar headers
        headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": rapidapi_host
        }
        
        # Endpoint de búsqueda
        url = f"https://{rapidapi_host}/listings_for_search"
        
        # Parámetros de búsqueda
        params = {
            'search_str': 'smartphone',
            'country': 'ar',
            'sort_by': 'relevance',
            'page_num': 1
        }
        
        logger.info(f"Enviando solicitud a: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Params: {params}")
        
        # Realizar solicitud
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Mostrar respuesta
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Headers: {dict(response.headers)}")
        
        # Mostrar contenido de la respuesta
        logger.info("Contenido de la respuesta:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        logger.error(f"Error al probar la conexión: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("="*80)
    print("PRUEBA SIMPLE DE CONEXIÓN CON RAPIDAPI - MERCADO LIBRE")
    print("="*80)
    
    print("\nIniciando prueba de conexión...\n")
    
    if test_rapidapi_connection():
        print("\n" + "="*80)
        print("✅ Prueba completada. Revisa el archivo 'rapidapi_simple_test.log' para más detalles.")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ La prueba falló. Revisa el archivo 'rapidapi_simple_test.log' para más detalles.")
        print("="*80)
