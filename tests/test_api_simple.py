#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test simple de la API de MercadoLibre
"""

import os
import requests
import dotenv
import sys

# Cargar variables de entorno
dotenv.load_dotenv()

# Obtener la clave de API
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("ERROR: No se encontró RAPIDAPI_KEY en variables de entorno")
    sys.exit(1)

# Configuración
RAPIDAPI_HOST = "mercado-libre7.p.rapidapi.com"
url = f"https://{RAPIDAPI_HOST}/listings_for_search"

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": RAPIDAPI_HOST
}

params = {
    "search_str": "televisor",
    "country": "mx",
    "page_num": 1,
    "sort_by": "relevance"  # Parámetro requerido por la API
}

print(f"Enviando solicitud a: {url}")
print(f"Con headers: {headers}")
print(f"Con params: {params}")

try:
    # Realizar la solicitud
    response = requests.get(url, headers=headers, params=params, timeout=15)
    
    # Imprimir información de la respuesta
    print(f"Status code: {response.status_code}")
    print(f"Content type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        # Analizar la respuesta
        data = response.json()
        
        if isinstance(data, list):
            print(f"Respuesta es una lista con {len(data)} elementos")
        elif isinstance(data, dict):
            print(f"Respuesta es un diccionario con keys: {list(data.keys())}")
            
            # Buscar resultados en diferentes claves
            for key in ["results", "listings", "items", "data", "products"]:
                if key in data and isinstance(data[key], list):
                    print(f"Encontrados {len(data[key])} elementos en la clave '{key}'")
    else:
        print(f"Error en la respuesta: {response.text[:200]}")
        
except Exception as e:
    print(f"Excepción: {str(e)}")
