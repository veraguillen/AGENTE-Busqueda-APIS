"""
Script de prueba para verificar que las importaciones funcionan correctamente.
"""
import sys
import os
import logging

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath('.'))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Intentar importar las clases principales
    from app.config_manager import ConfigManager
    from agents.agente_ml import AgenteML
    from agents.agente_filtro import AgenteFiltro
    from agents.agente_ranking import AgenteRanking
    
    logger.info("¡Todas las importaciones se realizaron correctamente!")
    
    # Mostrar información de las clases importadas
    print("\nClases importadas correctamente:")
    print(f"- ConfigManager: {ConfigManager}")
    print(f"- AgenteML: {AgenteML}")
    print(f"- AgenteFiltro: {AgenteFiltro}")
    print(f"- AgenteRanking: {AgenteRanking}")
    
except ImportError as e:
    logger.error(f"Error al importar: {e}")
    raise
