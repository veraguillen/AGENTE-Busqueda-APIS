"""
Módulo para la gestión centralizada de la configuración de la aplicación.
Permite cargar configuraciones desde archivos JSON y acceder a ellas de forma jerárquica.
"""
import os
import json
import logging
from typing import Any, Dict, Optional, Union, List, TypeVar, Type
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)

T = TypeVar('T')

class ConfigManager:
    """
    Clase para gestionar la configuración de la aplicación.
    
    Permite cargar configuraciones desde un archivo JSON y acceder a ellas
    de forma jerárquica usando notación de puntos (ej: 'database.host').
    """
    
    _instance = None
    _config: Dict[str, Any] = {}
    _config_file: str = None
    
    def __new__(cls, config_file: str = None):
        """Implementa el patrón Singleton para tener una única instancia de ConfigManager."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            if config_file:
                cls._instance.load_config(config_file)
        return cls._instance
    
    def load_config(self, config_file: str) -> None:
        """
        Carga la configuración desde un archivo JSON.
        
        Args:
            config_file: Ruta al archivo de configuración JSON.
            
        Raises:
            FileNotFoundError: Si el archivo de configuración no existe.
            json.JSONDecodeError: Si el archivo no es un JSON válido.
        """
        self._config_file = config_file
        
        # Verificar si el archivo existe
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f"El archivo de configuración no existe: {config_file}")
        
        # Cargar el archivo JSON
        with open(config_file, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
        
        logger.info(f"Configuración cargada desde {os.path.abspath(config_file)}")
    
    def get(self, key: str, default: Any = None, required: bool = False) -> Any:
        """
        Obtiene un valor de configuración por su clave.
        
        Args:
            key: Clave de configuración en formato 'seccion.subseccion.valor'.
            default: Valor por defecto a devolver si la clave no existe.
            required: Si es True, lanza KeyError si la clave no existe.
            
        Returns:
            El valor de configuración o el valor por defecto si no existe.
            
        Raises:
            KeyError: Si la clave es requerida pero no existe.
        """
        if not key:
            if required:
                raise KeyError("Se requiere una clave de configuración")
            return default
        
        # Manejo especial para variables de entorno
        if key.startswith('env:'):
            env_var = key[4:]
            value = os.getenv(env_var)
            if value is None and required:
                raise KeyError(f"La variable de entorno '{env_var}' no está definida")
            return value if value is not None else default
        
        # Búsqueda jerárquica
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            
            # Procesar plantillas de strings (soporte para variables de entorno)
            if isinstance(value, str) and '${' in value and '}' in value:
                import re
                env_vars = re.findall(r'\${(.*?)}', value)
                for env_var in env_vars:
                    env_value = os.getenv(env_var)
                    if env_value is not None:
                        value = value.replace(f'${{{env_var}}}', env_value)
            
            return value
        except (KeyError, TypeError):
            if required:
                raise KeyError(f"La clave de configuración '{key}' es requerida pero no está definida")
            return default
    
    def get_as(self, key: str, type_hint: Type[T], default: Any = None, required: bool = False) -> T:
        """
        Obtiene un valor de configuración con conversión de tipo.
        
        Args:
            key: Clave de configuración.
            type_hint: Tipo al que convertir el valor.
            default: Valor por defecto si la clave no existe.
            required: Si es True, lanza KeyError si la clave no existe.
            
        Returns:
            El valor convertido al tipo especificado.
            
        Raises:
            ValueError: Si no se puede convertir el valor al tipo especificado.
        """
        value = self.get(key, default, required)
        
        if value is None and not required:
            return None
            
        try:
            # Manejo especial para booleanos (ya que bool('False') es True)
            if type_hint is bool and isinstance(value, str):
                return value.lower() in ('true', '1', 't', 'y', 'yes')
            return type_hint(value) if value is not None else None
        except (ValueError, TypeError) as e:
            if required:
                raise ValueError(f"No se pudo convertir el valor '{value}' a {type_hint.__name__} para la clave '{key}'") from e
            return default
    
    def get_section(self, section_key: str) -> Dict[str, Any]:
        """
        Obtiene una sección completa de la configuración.
        
        Args:
            section_key: Clave de la sección (ej: 'database').
            
        Returns:
            Un diccionario con la configuración de la sección.
            
        Raises:
            KeyError: Si la sección no existe.
        """
        return self.get(section_key, required=True)
    
    def reload(self) -> None:
        """Recarga la configuración desde el archivo."""
        if self._config_file:
            self.load_config(self._config_file)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Devuelve una copia del diccionario de configuración completo.
        
        Returns:
            Diccionario con toda la configuración.
        """
        return self._config.copy()
    
    def __str__(self) -> str:
        """Representación en string de la configuración (sin contraseñas)."""
        import copy
        
        def hide_sensitive_data(config):
            if not isinstance(config, dict):
                return config
                
            result = {}
            for k, v in config.items():
                if isinstance(v, dict):
                    result[k] = hide_sensitive_data(v)
                elif any(sensitive in k.lower() for sensitive in ['key', 'secret', 'password', 'token']):
                    result[k] = '***HIDDEN***' if v else None
                else:
                    result[k] = v
            return result
        
        safe_config = hide_sensitive_data(copy.deepcopy(self._config))
        return json.dumps(safe_config, indent=2, ensure_ascii=False)


# Instancia global para facilitar el acceso
global_config = ConfigManager()


def get_config() -> ConfigManager:
    """
    Obtiene la instancia global del ConfigManager.
    
    Returns:
        Instancia de ConfigManager.
    """
    return global_config


def init_config(config_file: str = None) -> ConfigManager:
    """
    Inicializa la configuración global.
    
    Args:
        config_file: Ruta al archivo de configuración.
        
    Returns:
        Instancia de ConfigManager.
    """
    if config_file:
        global_config.load_config(config_file)
    return global_config
