#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para depurar la estructura de los productos de MercadoLibre.
"""

import sys
import os
import json
import logging

# Añadir directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.orquestador import Orquestador

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def main():
    print("Inicializando orquestador...")
    orquestador = Orquestador()
    
    query = "notebook"
    print(f"Realizando búsqueda para: {query}")
    
    # Realizar búsqueda
    results = orquestador.buscar_productos(query)
    
    if results.get("status") == "success" and results.get("top_products"):
        # Mostrar estructura del primer producto
        print("\nEstructura del primer producto:")
        first_product = results["top_products"][0]
        print(json.dumps(first_product, indent=4, ensure_ascii=False))
        
        # Mostrar específicamente la estructura del vendedor
        print("\nEstructura del vendedor:")
        seller_info = first_product.get("seller", "No disponible")
        print(type(seller_info))
        print(json.dumps(seller_info, indent=4, ensure_ascii=False))
    else:
        print("Error en la búsqueda o no se encontraron productos.")

if __name__ == "__main__":
    main()
