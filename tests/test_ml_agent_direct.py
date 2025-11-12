#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prueba directa del AgenteML con logging detallado
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Añadir el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ml_agent_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_ml_agent():
    """Prueba directa del AgenteML"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        
        # Importar después de configurar el entorno
        from agents.agente_ml_simple import AgenteML
        
        # Inicializar agente
        logger.info("Inicializando AgenteML...")
        agente_ml = AgenteML(
            rapidapi_key=os.getenv("RAPIDAPI_KEY"),
            cache=None,
            config=None,
            monitor=None
        )
        
        # Configurar el host de la API si es necesario
        if os.getenv("RAPIDAPI_HOST"):
            agente_ml.rapidapi_host = os.getenv("RAPIDAPI_HOST")
        
        # Realizar búsqueda
        logger.info("Realizando búsqueda...")
        query = "smartphone samsung"
        country_code = "ar"
        max_pages = 1
        
        logger.info(f"Buscando: '{query}' en {country_code} (máx. {max_pages} páginas)")
        
        # Llamar al método search directamente
        results = agente_ml.search(query, country_code, max_pages)
        
        # Mostrar resultados
        logger.info(f"\n{'='*80}")
        logger.info(f"RESULTADOS DE LA BÚSQUEDA ({len(results)} productos)")
        logger.info(f"{'='*80}")
        
        for i, product in enumerate(results[:5], 1):  # Mostrar solo los primeros 5 para no saturar
            logger.info(f"\nProducto #{i}:")
            logger.info(f"  ID: {product.get('id')}")
            logger.info(f"  Título: {product.get('title')}")
            logger.info(f"  Precio: {product.get('price')} {product.get('currency')}")
            
            seller = product.get('seller', {})
            if seller:
                logger.info(f"  Vendedor: {seller.get('nickname')} (ID: {seller.get('id')})")
            else:
                logger.info("  Sin información de vendedor")
            
            logger.info(f"  URL: {product.get('listing_url')}")
        
        # Guardar resultados completos en archivo
        output_file = 'ml_agent_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nResultados completos guardados en: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en la prueba del AgenteML: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("="*80)
    print("PRUEBA DIRECTA DEL AGENTE ML")
    print("="*80)
    
    print("\nIniciando prueba...\n")
    
    if test_ml_agent():
        print("\n" + "="*80)
        print("✅ Prueba completada. Revisa el archivo 'ml_agent_test.log' para más detalles.")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ La prueba falló. Revisa el archivo 'ml_agent_test.log' para más detalles.")
        print("="*80)
