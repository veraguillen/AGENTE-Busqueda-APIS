#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prueba específica de búsqueda de "televisor" en MercadoLibre
"""

import os
import sys
import dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Asegurar que podemos acceder a los módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Cargar variables de entorno
dotenv.load_dotenv()

def test_televisor_search():
    """Prueba específica para buscar televisores"""
    from agents.agente_ml_simple import AgenteML
    
    # Obtener API key
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.error("No se encontró RAPIDAPI_KEY en las variables de entorno")
        return
        
    # Crear instancia del agente
    agent = AgenteML(rapidapi_key=api_key)
    
    # Probar 3 búsquedas diferentes
    test_queries = [
        ("televisor", "mx"),
        ("tv", "mx"),
        ("laptop", "mx")
    ]
    
    for query, country in test_queries:
        logger.info(f"--- Probando búsqueda de '{query}' en {country} ---")
        
        # Ejecutar búsqueda con parámetros específicos
        results = agent.search(
            query=query,
            country=country,
            max_pages=2,  # Solo probamos 2 páginas para diagnóstico
            sort="relevance",
            min_results=1  # Mínimo de resultados esperados
        )
        
        # Mostrar resultados
        logger.info(f"Resultados encontrados: {len(results)}")
        
        # Si hay resultados, mostrar el primero
        if results:
            first = results[0]
            logger.info(f"Primer resultado - ID: {first.get('id')}")
            logger.info(f"Título: {first.get('title')}")
            
            # Verificar información del vendedor
            seller = first.get('seller', {})
            if isinstance(seller, dict):
                logger.info(f"Vendedor: {seller.get('nickname', 'No disponible')}")
            elif isinstance(seller, str):
                logger.info(f"Vendedor (string): {seller}")
            else:
                logger.info(f"Vendedor no encontrado o tipo desconocido: {type(seller)}")
        
        logger.info("-" * 50)

if __name__ == "__main__":
    test_televisor_search()
