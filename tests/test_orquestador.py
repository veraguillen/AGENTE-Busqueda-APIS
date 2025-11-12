"""
Script de prueba para el orquestador principal.
"""
import sys
import os
import logging
from dotenv import load_dotenv

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath('.'))

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_orquestador():
    """Prueba básica del orquestador."""
    try:
        from app.orquestador import Orquestador
        from app.config_manager import ConfigManager
        
        # Inicializar configuración
        config = ConfigManager()
        
        # Preparar secretos
        secrets = {
            'RAPIDAPI_KEY': os.getenv('RAPIDAPI_KEY'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
            'GOOGLE_CSE_ID': os.getenv('GOOGLE_CSE_ID')
        }
        
        # Inicializar orquestador con los secretos necesarios
        orquestador = Orquestador(
            secrets=secrets,
            custom_config=config
        )
        
        logger.info("Orquestador inicializado correctamente")
        
        # Ejecutar una búsqueda de prueba
        query = "notebook"
        country_code = "AR"
        
        logger.info(f"Ejecutando búsqueda de prueba para: {query} en {country_code}")
        
        # Nota: Comentado temporalmente para evitar llamadas a la API
        # result = orquestador.execute_top_seller_search(query, country_code)
        # logger.info(f"Resultado de la búsqueda: {len(result)} productos encontrados")
        
        logger.info("Prueba completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en la prueba del orquestador: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Iniciando prueba del orquestador...")
    success = test_orquestador()
    if success:
        logger.info("¡Prueba del orquestador completada con éxito!")
    else:
        logger.error("La prueba del orquestador falló")
