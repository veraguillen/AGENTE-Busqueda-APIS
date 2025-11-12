#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de diagnóstico para RapidAPI
"""

import os
import sys
import json
import requests
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener clave API de RapidAPI
api_key = os.environ.get("RAPIDAPI_KEY")
if not api_key:
    logger.error("No se encontró RAPIDAPI_KEY en las variables de entorno")
    sys.exit(1)

print(f"Usando clave API: {api_key[:4]}...{api_key[-4:]}")

def test_rapidapi_hosts():
    """Prueba diferentes hosts de RapidAPI para verificar tu clave y suscripciones"""
    
    # Lista de hosts de API para probar
    hosts = [
        {
            "name": "Maps Data API",
            "host": "maps-data.p.rapidapi.com",
            "endpoint": "/searchmaps.php",
            "params": {"query": "Test", "country": "ar"}
        },
        {
            "name": "MercadoLibre API",
            "host": "mercado-libre7.p.rapidapi.com",
            "endpoint": "/offers",
            "params": {"api_version": "2", "region": "ar"}
        }
    ]
    
    for api in hosts:
        print(f"\n===== Probando {api['name']} =====")
        print(f"Host: {api['host']}")
        print(f"Endpoint: {api['endpoint']}")
        print(f"Parámetros: {api['params']}")
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api['host']
        }
        
        url = f"https://{api['host']}{api['endpoint']}"
        
        try:
            print(f"Enviando solicitud a {url}...")
            response = requests.get(
                url, 
                headers=headers, 
                params=api['params'], 
                timeout=5
            )
            
            print(f"Código de estado: {response.status_code}")
            
            # Mostrar encabezados de respuesta
            print("Encabezados de respuesta:")
            for header, value in response.headers.items():
                print(f"  {header}: {value}")
            
            # Intentar parsear respuesta JSON
            try:
                data = response.json()
                print("Respuesta recibida (primeros 500 caracteres):")
                print(json.dumps(data, indent=2)[:500] + "...")
            except json.JSONDecodeError:
                print("La respuesta no es JSON válido. Contenido (primeros 500 caracteres):")
                print(response.text[:500])
        
        except requests.exceptions.Timeout:
            print("⚠️ Timeout - La solicitud excedió el tiempo de espera")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en la solicitud: {str(e)}")
        
        print(f"===== Fin de prueba {api['name']} =====\n")

if __name__ == "__main__":
    test_rapidapi_hosts()
