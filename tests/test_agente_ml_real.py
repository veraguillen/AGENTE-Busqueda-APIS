"""
Script de prueba para el AgenteML con la API real de MercadoLibre.
Uso: python test_agente_ml_real.py [término] [país] [límite]
Ejemplo: python test_agente_ml_real.py "televisor" AR 5
"""
import os
import sys
import logging
import json
from dotenv import load_dotenv
from utils.api_client import APIClient
from agents.agente_ml import AgenteML
from app.config_manager import ConfigManager

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,  # Cambiado a DEBUG para ver más detalles
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_agente_ml.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener la clave de la API
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if not rapidapi_key:
        logger.error("No se encontró la variable de entorno RAPIDAPI_KEY")
        print("ERROR: Debes configurar la variable de entorno RAPIDAPI_KEY")
        return
    
    # Obtener parámetros de línea de comandos o solicitar al usuario
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = input("Término de búsqueda (ej: 'televisor'): ") or "televisor"
    
    if len(sys.argv) > 2:
        country = sys.argv[2].upper()
    else:
        country = input("Código de país (ej: 'AR', 'BR'): ").upper() or "AR"
    
    if len(sys.argv) > 3:
        try:
            limit = int(sys.argv[3])
        except ValueError:
            limit = 5
    else:
        try:
            limit = int(input("Número de resultados (máx 50): ") or "5")
        except ValueError:
            limit = 5
    
    # Asegurar que el límite esté en el rango correcto
    limit = max(1, min(50, limit))
    
    logger.info(f"Iniciando prueba con parámetros: query='{query}', country={country}, limit={limit}")
    
    # Inicializar dependencias
    api_client = APIClient()
    config = ConfigManager()
    
    # Configurar el logger del APIClient para ver las peticiones
    api_client_logger = logging.getLogger('utils.api_client')
    api_client_logger.setLevel(logging.DEBUG)
    
    # Crear instancia del agente
    logger.info("Creando instancia de AgenteML...")
    agente_ml = AgenteML(
        rapidapi_key=rapidapi_key,
        api_client=api_client,
        config=config
    )
    
    logger.info(f"Realizando búsqueda de '{query}' en {country}...")
    
    try:
        # Realizar búsqueda
        logger.info("Ejecutando búsqueda...")
        productos, total = agente_ml.search(
            query=query,
            country=country,
            limit=limit,
            sort="relevance"
        )
        
        # Mostrar resultados
        print(f"\n=== RESULTADOS DE BÚSQUEDA ===")
        print(f"Término: {query}")
        print(f"País: {country}")
        print(f"Total de resultados: {total}")
        print(f"Resultados obtenidos: {len(productos)}")
        
        if not productos:
            print("\nNo se encontraron resultados.")
            return
            
        print("\n--- Productos encontrados ---")
        for i, producto in enumerate(productos, 1):
            print(f"\n--- Producto {i} ---")
            print(f"ID: {producto.get('id', 'N/A')}")
            print(f"Título: {producto.get('title', 'Sin título')}")
            print(f"Precio: {producto.get('price', 'No disponible')} {producto.get('currency_id', '')}")
            print(f"Condición: {producto.get('condition', 'No especificada')}")
            
            # Mostrar información del vendedor si está disponible
            seller = producto.get('seller')
            if seller:
                print(f"Vendedor: {seller.get('nickname', 'No disponible')}")
                print(f"Reputación: {seller.get('seller_reputation', {}).get('power_seller_status', 'No disponible')}")
            
            # Mostrar información de envío
            shipping = producto.get('shipping', {})
            print(f"Envío: {'Gratis' if shipping.get('free_shipping', False) else 'Con costo'}")
            
            # Mostrar URL del producto si está disponible
            if 'permalink' in producto:
                print(f"URL: {producto['permalink']}")
            
            # Mostrar miniaturas si están disponibles
            if 'thumbnail' in producto:
                print(f"Miniatura: {producto['thumbnail']}")
            
            print("-" * 50)
            
    except Exception as e:
        logger.error(f"Error al realizar la búsqueda: {str(e)}", exc_info=True)
        print(f"\nERROR: {str(e)}")
        print("\nRevisa el archivo debug_agente_ml.log para más detalles.")
    
    print("\nPrueba completada.")

if __name__ == "__main__":
    main()
