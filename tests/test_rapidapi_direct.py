#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar directamente la API de MercadoLibre a través de RapidAPI
"""

import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rapidapi_direct_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_rapidapi_direct():
    """Prueba la conexión directa con la API de MercadoLibre a través de RapidAPI"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Obtener credenciales
        rapidapi_key = os.getenv("RAPIDAPI_KEY")
        rapidapi_host = os.getenv("RAPIDAPI_HOST", "mercado-libre7.p.rapidapi.com")
        
        if not rapidapi_key:
            logger.error("No se encontró RAPIDAPI_KEY en las variables de entorno")
            return False
        
        logger.info(f"Probando conexión directa con RapidAPI - Host: {rapidapi_host}")
        
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
        
        # Mostrar el contenido de la respuesta
        logger.info("Contenido de la respuesta:")
        logger.info(response.text[:1000])  # Mostrar primeros 1000 caracteres
        
        # Intentar decodificar la respuesta como JSON
        try:
            data = response.json()
            logger.info("\nRespuesta JSON decodificada:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Guardar respuesta en archivo
            with open('rapidapi_direct_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("\nRespuesta guardada en 'rapidapi_direct_response.json'")
            
        except ValueError as e:
            logger.error(f"No se pudo decodificar la respuesta como JSON: {e}")
            logger.info(f"Contenido de la respuesta: {response.text[:2000]}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error al probar la conexión: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("="*80)
    print("PRUEBA DIRECTA DE CONEXIÓN CON RAPIDAPI - MERCADO LIBRE")
    print("="*80)
    
    print("\nIniciando prueba de conexión directa...\n")
    
    if test_rapidapi_direct():
        print("\n" + "="*80)
        print("✅ Prueba completada. Revisa el archivo 'rapidapi_direct_test.log' para más detalles.")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ La prueba falló. Revisa el archivo 'rapidapi_direct_test.log' para más detalles.")
        print("="*80)
