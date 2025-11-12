#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de diagnóstico para la API de MercadoLibre en RapidAPI
Este script realiza una petición directa a la API para diagnosticar problemas
"""

import os
import json
import requests
import logging
import sys
import time
import dotenv
from pprint import pprint

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
dotenv.load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not RAPIDAPI_KEY:
    logger.error("No se encontró RAPIDAPI_KEY en variables de entorno")
    sys.exit(1)

# Constantes
RAPIDAPI_HOST = "mercado-libre7.p.rapidapi.com"
REQUEST_TIMEOUT = 15  # segundos

def test_search(query="televisor", country="mx"):
    """Prueba directa de búsqueda en MercadoLibre"""
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    # Intentar con varios endpoints
    endpoints = [
        "listings_for_search",
        "search_for_listings",
        "search_products"
    ]
    
    for endpoint in endpoints:
        url = f"https://{RAPIDAPI_HOST}/{endpoint}"
        logger.info(f"Probando endpoint: {url}")
        
        params = {
            "search_str": query,
            "country": country.lower()
        }
        
        try:
            logger.info(f"Enviando solicitud: {url} con params={params}")
            response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        logger.info(f"Respuesta es una lista con {len(data)} elementos")
                        # Mostrar primer elemento
                        if len(data) > 0:
                            logger.info("Primer elemento:")
                            pprint(data[0])
                    elif isinstance(data, dict):
                        logger.info(f"Respuesta es un diccionario con keys: {list(data.keys())}")
                        # Buscar resultados en todas las claves posibles
                        for key in ["results", "listings", "items", "data", "products"]:
                            if key in data and isinstance(data[key], list):
                                logger.info(f"Encontrados resultados en '{key}': {len(data[key])} elementos")
                                if len(data[key]) > 0:
                                    logger.info("Primer elemento:")
                                    pprint(data[key][0])
                    else:
                        logger.error(f"Tipo de respuesta desconocido: {type(data)}")
                except Exception as e:
                    logger.error(f"Error al procesar JSON: {e}")
                    logger.info(f"Contenido de respuesta: {response.text[:500]}...")
            else:
                logger.error(f"Error en respuesta: {response.text[:500]}...")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en solicitud: {e}")
        
        logger.info("-" * 50)
    
    return "Prueba completada"

def test_all():
    """Ejecuta todas las pruebas de diagnóstico"""
    logger.info("=== INICIANDO DIAGNÓSTICO DE API DE MERCADOLIBRE ===")
    
    # Lista de términos de búsqueda de prueba
    test_queries = [
        ("televisor", "mx"),
        ("celular", "mx"),
        ("laptop", "ar"),
        ("camara", "mx")
    ]
    
    for query, country in test_queries:
        logger.info(f"\n=== PRUEBA CON: {query.upper()} en {country.upper()} ===")
        test_search(query, country)
        time.sleep(1)  # Pausa para evitar límites de API
    
    logger.info("=== DIAGNÓSTICO FINALIZADO ===")

if __name__ == "__main__":
    test_all()
