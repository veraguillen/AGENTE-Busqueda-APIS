"""
Script para probar búsquedas reales con el orquestador.
Este script realiza búsquedas utilizando la API de MercadoLibre y muestra los resultados.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_busqueda(query: str, country: str = "AR", limit: int = 10):
    """
    Realiza una búsqueda de prueba utilizando el orquestador.
    
    Args:
        query: Término de búsqueda
        country: Código de país (ej: 'AR', 'MX', 'BR')
        limit: Número máximo de resultados a mostrar
    """
    try:
        from app.orquestador import Orquestador
        from app.config_manager import ConfigManager
        
        logger.info(f"Iniciando búsqueda: '{query}' en {country}")
        
        # Obtener secretos de las variables de entorno
        secrets = {
            'RAPIDAPI-KEY': os.getenv('RAPIDAPI_KEY'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
            'GOOGLE_CSE_ID': os.getenv('GOOGLE_CSE_ID')
        }
        
        # Inicializar el orquestador
        orquestador = Orquestador(secrets=secrets)
        
        # Realizar la búsqueda
        logger.info("Ejecutando búsqueda...")
        resultados = orquestador.execute_top_seller_search(query, country)
        
        # Mostrar resultados
        if not resultados:
            logger.warning("No se encontraron resultados")
            return
            
        logger.info(f"\n=== RESULTADOS DE BÚSQUEDA ({len(resultados)}) ===")
        
        # Mostrar un resumen de los resultados
        for i, producto in enumerate(resultados[:limit], 1):
            print(f"\n--- Producto #{i} ---")
            print(f"Título: {producto.get('title', 'Sin título')}")
            print(f"Precio: {producto.get('price', 'N/A')} {producto.get('currency_id', '')}")
            print(f"Condición: {producto.get('condition', 'N/A')}")
            print(f"Ventas: {producto.get('sold_quantity', 0)}")
            print(f"Vendedor: {producto.get('seller', {}).get('nickname', 'N/A')}")
            print(f"Enlace: {producto.get('permalink', 'N/A')}")
        
        logger.info("\nBúsqueda completada exitosamente!")
        
    except Exception as e:
        logger.error(f"Error durante la búsqueda: {str(e)}", exc_info=True)

if __name__ == "__main__":
    import argparse
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Realizar búsquedas en MercadoLibre')
    parser.add_argument('query', type=str, help='Término de búsqueda')
    parser.add_argument('--country', type=str, default='AR', help='Código de país (ej: AR, MX, BR)')
    parser.add_argument('--limit', type=int, default=10, help='Número máximo de resultados a mostrar')
    
    args = parser.parse_args()
    
    # Ejecutar la búsqueda
    test_busqueda(args.query, args.country, args.limit)
