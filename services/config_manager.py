"""
Módulo para gestión centralizada de la configuración del sistema.
Permite acceder a todos los parámetros configurables desde un único punto.
"""
import os
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

class ConfigManager:
    """Gestor centralizado de configuración para el sistema de agentes."""
    
    # Valores predeterminados para la configuración
    DEFAULT_CONFIG = {
        # Configuración general
        "country_default": "AR",
        "search_max_pages": 30,
        "request_timeout": 15,  # segundos
        
        # Configuración de API
        "rapidapi_hosts": [
            "mercado-libre7.p.rapidapi.com",
            "mercadolibre1.p.rapidapi.com",
            "mercadolibre.p.rapidapi.com"
        ],
        "google_api_host": "https://www.googleapis.com/customsearch/v1",
        
        # Filtros
        "excluded_brands": [
            "apple", "sony", "samsung", "lg", 
            "microsoft", "hp", "huawei"
        ],
        
        # Caché
        "cache_ttl_search": 3600,  # 1 hora para resultados de búsqueda
        "cache_ttl_contacts": 86400,  # 24 horas para información de contacto
        
        # Búsqueda
        "search_sort_default": "relevance",
        "search_limit_per_page": 50,
        
        # Google CSE
        "google_search_results": 10,
        "google_region_code": "ar",
        
        # Teléfonos
        "phone_min_digits": 8,
        "argentina_country_code": "54",
        
        # Resultados
        "max_top_products": 5
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración JSON (opcional)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Cargar configuración desde archivo si existe
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # Actualizar solo los valores presentes en el archivo
                    for key, value in file_config.items():
                        self.config[key] = value
                logger.info(f"Configuración cargada desde {config_path}")
            except Exception as e:
                logger.error(f"Error al cargar configuración desde {config_path}: {e}")
        
        # Sobrescribir con variables de entorno
        self._load_from_env()
        
        logger.info("Gestor de configuración inicializado correctamente")
    
    def _load_from_env(self):
        """Carga configuración desde variables de entorno."""
        # Mapeo de variables de entorno a claves de configuración
        env_mappings = {
            "DEFAULT_COUNTRY": "country_default",
            "SEARCH_MAX_PAGES": "search_max_pages",
            "REQUEST_TIMEOUT": "request_timeout",
            "CACHE_TTL_SEARCH": "cache_ttl_search",
            "CACHE_TTL_CONTACTS": "cache_ttl_contacts",
            "GOOGLE_REGION_CODE": "google_region_code",
            "MAX_TOP_PRODUCTS": "max_top_products"
        }
        
        for env_var, config_key in env_mappings.items():
            if os.getenv(env_var):
                try:
                    # Convertir a número si es posible
                    value = os.getenv(env_var)
                    if value.isdigit():
                        value = int(value)
                    elif value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    self.config[config_key] = value
                except Exception as e:
                    logger.warning(f"Error al cargar variable de entorno {env_var}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración en tiempo de ejecución.
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self.config[key] = value
        logger.debug(f"Configuración actualizada: {key}={value}")
    
    def save_to_file(self, config_path: str) -> bool:
        """
        Guarda la configuración actual en un archivo JSON.
        
        Args:
            config_path: Ruta donde guardar el archivo
            
        Returns:
            Boolean indicando si se guardó correctamente
        """
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuración guardada en {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración en {config_path}: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Obtiene toda la configuración actual.
        
        Returns:
            Diccionario con toda la configuración
        """
        return self.config.copy()


# Instancia global del gestor de configuración
config_path = os.getenv('CONFIG_PATH', 'config.json')
config_manager = ConfigManager(config_path)
