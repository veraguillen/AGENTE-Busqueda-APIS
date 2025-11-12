#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Diagnóstico completo de la API de MercadoLibre
Este script guarda todos los resultados en un archivo de log para análisis
"""

import os
import sys
import requests
import logging
import time
import json
import dotenv
from datetime import datetime

# Configurar logging a archivo y consola
LOG_FILE = f"diagnostico_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
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

def test_api_endpoint(endpoint, query="televisor", country="mx"):
    """Prueba un endpoint específico de la API de MercadoLibre"""
    url = f"https://{RAPIDAPI_HOST}/{endpoint}"
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    
    params = {
        "search_str": query,
        "country": country.lower(),
        "page_num": 1,
        "sort_by": "relevance"  # Parámetro requerido
    }
    
    logger.info(f"TEST ENDPOINT: {endpoint} - Query: {query}")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        
        # Guardar toda la información relevante
        log_info = {}
        log_info["endpoint"] = endpoint
        log_info["query"] = query
        log_info["status_code"] = response.status_code
        log_info["headers"] = dict(response.headers)
        log_info["request_params"] = params
        
        # Log del resultado
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Content-Type: {response.headers.get('Content-Type')}")
        
        # Si la respuesta es exitosa, analizar el contenido
        if response.status_code == 200:
            try:
                data = response.json()
                
                if isinstance(data, list):
                    logger.info(f"Respuesta es una lista con {len(data)} elementos")
                    
                    # Guardar primer elemento como ejemplo
                    if data:
                        log_info["first_item"] = data[0]
                        with open(f"response_{endpoint}_{query}_first_item.json", "w", encoding="utf-8") as f:
                            json.dump(data[0], f, ensure_ascii=False, indent=2)
                    
                elif isinstance(data, dict):
                    logger.info(f"Respuesta es un diccionario con claves: {list(data.keys())}")
                    
                    # Buscar resultados en claves conocidas
                    found_results = False
                    for key in ["results", "listings", "items", "data", "products"]:
                        if key in data and isinstance(data[key], list):
                            found_results = True
                            result_count = len(data[key])
                            logger.info(f"Encontrados {result_count} elementos en '{key}'")
                            
                            # Guardar primer elemento de resultados como ejemplo
                            if result_count > 0:
                                log_info[f"first_{key}_item"] = data[key][0]
                                with open(f"response_{endpoint}_{query}_first_{key}_item.json", "w", encoding="utf-8") as f:
                                    json.dump(data[key][0], f, ensure_ascii=False, indent=2)
                    
                    if not found_results:
                        logger.warning("No se encontraron resultados en ninguna clave conocida")
                    
                    # Guardar respuesta completa
                    with open(f"response_{endpoint}_{query}_full.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                else:
                    logger.error(f"Tipo de respuesta desconocido: {type(data)}")
                    log_info["response_type"] = str(type(data))
            
            except ValueError as e:
                logger.error(f"Error al parsear JSON: {e}")
                # Guardar respuesta cruda
                with open(f"response_{endpoint}_{query}_raw.txt", "w", encoding="utf-8") as f:
                    f.write(response.text[:10000])  # Limitar a 10K chars
                log_info["parse_error"] = str(e)
                log_info["raw_response"] = response.text[:1000]  # Primeros 1000 chars para el log
        
        else:
            logger.error(f"Error en respuesta HTTP: {response.status_code}")
            logger.error(f"Contenido: {response.text[:500]}")
            log_info["error_response"] = response.text[:1000]
        
        # Guardar log completo
        with open(f"log_{endpoint}_{query}.json", "w", encoding="utf-8") as f:
            json.dump(log_info, f, ensure_ascii=False, indent=2)
        
    except requests.RequestException as e:
        logger.error(f"Error de conexión: {e}")
    
    logger.info("-" * 60)
    return None

def diagnose_all():
    """Ejecuta diagnóstico con todos los endpoints y consultas de prueba"""
    logger.info("=== INICIANDO DIAGNÓSTICO COMPLETO ===")
    
    # Endpoints a probar
    endpoints = [
        "listings_for_search", 
        "search_for_listings", 
        "search_products"
    ]
    
    # Consultas de prueba (producto, país)
    queries = [
        ("televisor", "mx"),
        ("television", "mx"),  # Variación de término
        ("tv", "mx"),         # Término corto
        ("laptop", "mx")      # Término diferente
    ]
    
    # Probar cada combinación
    for endpoint in endpoints:
        for query, country in queries:
            test_api_endpoint(endpoint, query, country)
            time.sleep(1)  # Evitar límites de tasa
    
    logger.info("=== DIAGNÓSTICO COMPLETO FINALIZADO ===")
    logger.info(f"Resultados guardados en: {LOG_FILE} y archivos JSON/TXT asociados")
    
    return True

if __name__ == "__main__":
    diagnose_all()
