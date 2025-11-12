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
    DEFAULTS = {
        'app': {
            'name': 'SearchAgent',
            'version': '1.0.0',
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
        },
        'api': {
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 1,
        },
        'cache': {
            'enabled': True,
            'ttl': 3600,  # 1 hora
            'max_size': 1000,
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': None,
        },
        'mercadolibre': {
            'api': {
                'host': 'mercado-libre7.p.rapidapi.com',
                'endpoints': {
                    'search': '/listings_for_search',
                    'item': '/items',
                    'seller': '/sellers',
                },
                'default_limit': 10,
                'max_limit': 50,
            },
            'search': {
                'sort_options': ['relevance', 'price_asc', 'price_desc'],
                'default_sort': 'relevance',
            },
        },
        'google': {
            'api': {
                'host': 'www.googleapis.com',
                'endpoints': {
                    'custom_search': '/customsearch/v1',
                },
            },
        },
        'maps': {
            'api': {
                'host': 'maps-data.p.rapidapi.com',
                'endpoints': {
                    'search': '/search',
                    'place_details': '/place-details',
                },
            },
        },
    }
    
    def __init__(self, config_path: str = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_path: Ruta al archivo de configuración JSON (opcional).
                        Si no se proporciona, se usan los valores por defecto.
        """
        self._config = self._load_config(config_path) if config_path else {}
        self._config = self._merge_configs(self.DEFAULTS, self._config)
        
        # Cargar configuración desde variables de entorno
        self._load_from_env()
        
        logger.info(f"Configuración cargada. Entorno: {self.get('app.environment')}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carga la configuración desde un archivo JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"Configuración cargada desde {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Archivo de configuración no encontrado: {config_path}. Usando valores por defecto.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar el archivo de configuración {config_path}: {e}")
            return {}
    
    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """Combina la configuración por defecto con la personalizada."""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _load_from_env(self):
        """Carga configuración desde variables de entorno."""
        # Actualizar configuración de la API desde variables de entorno
        for key, value in os.environ.items():
            if key.startswith('APP_'):
                # Convertir APP_API_TIMEOUT a api.timeout
                parts = key.lower().split('_')[1:]  # Eliminar el prefijo 'APP_'
                self._set_nested(self._config, parts, value)
    
    def _set_nested(self, config: Dict[str, Any], path: List[str], value: Any):
        """Establece un valor anidado en la configuración."""
        if len(path) == 1:
            # Convertir tipos básicos
            if isinstance(value, str):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                    value = float(value)
            
            config[path[0]] = value
        else:
            if path[0] not in config:
                config[path[0]] = {}
            self._set_nested(config[path[0]], path[1:], value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración por su clave.
        
        Args:
            key: Clave en formato 'seccion.subseccion.clave'
            default: Valor por defecto si la clave no existe
            
        Returns:
            El valor de la configuración o el valor por defecto si no existe
        """
        try:
            parts = key.split('.')
            value = self._config
            
            for part in parts:
                value = value[part]
                
            return value
        except (KeyError, AttributeError):
            return default
    
    def update(self, key: str, value: Any):
        """
        Actualiza un valor de configuración.
        
        Args:
            key: Clave en formato 'seccion.subseccion.clave'
            value: Nuevo valor
        """
        parts = key.split('.')
        self._set_nested(self._config, parts, value)
        logger.debug(f"Configuración actualizada: {key} = {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Devuelve la configuración como un diccionario."""
        return self._config.copy()


# Instancia global del gestor de configuración
config_path = os.getenv('CONFIG_PATH', 'config.json')
config_manager = ConfigManager(config_path)
