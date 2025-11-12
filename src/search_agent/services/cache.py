"""
Módulo para gestión de caché distribuida usando Redis.
Permite compartir resultados de búsquedas entre diferentes instancias del servicio.
"""
import redis
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Union
from functools import wraps

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

class CacheManager:
    """Gestor de caché distribuida para el sistema de agentes."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Inicializa el gestor de caché.
        
        Args:
            redis_url: URL de conexión a Redis (opcional).
                      Si no se proporciona, se intentará obtener de la variable de entorno REDIS_URL.
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._client = None
        self._connect()
    
    def _connect(self):
        """Establece la conexión con Redis."""
        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Verificar la conexión
            self._client.ping()
            logger.info(f"Conectado a Redis en {self.redis_url}")
        except Exception as e:
            logger.error(f"Error al conectar con Redis: {e}")
            self._client = None
    
    def is_connected(self) -> bool:
        """Verifica si la conexión con Redis está activa."""
        try:
            return self._client is not None and self._client.ping()
        except:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de la caché.
        
        Args:
            key: Clave del valor a obtener
            default: Valor por defecto si la clave no existe
            
        Returns:
            El valor almacenado o el valor por defecto
        """
        if not self.is_connected():
            return default
            
        try:
            value = self._client.get(key)
            if value is None:
                return default
                
            # Intentar deserializar JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error al obtener clave {key} de caché: {e}")
            return default
    
    def set(self, key: str, value: Any, expire_seconds: int = 3600) -> bool:
        """
        Almacena un valor en la caché.
        
        Args:
            key: Clave para almacenar el valor
            value: Valor a almacenar (debe ser serializable a JSON)
            expire_seconds: Tiempo de expiración en segundos (0 para sin expiración)
            
        Returns:
            True si se almacenó correctamente, False en caso contrario
        """
        if not self.is_connected():
            return False
            
        try:
            # Serializar a JSON si es necesario
            if not isinstance(value, (str, int, float, bool)):
                value = json.dumps(value, ensure_ascii=False)
                
            if expire_seconds > 0:
                return self._client.setex(key, expire_seconds, value)
            else:
                return self._client.set(key, value)
        except Exception as e:
            logger.error(f"Error al almacenar clave {key} en caché: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """
        Elimina una o más claves de la caché.
        
        Args:
            *keys: Claves a eliminar
            
        Returns:
            Número de claves eliminadas
        """
        if not self.is_connected() or not keys:
            return 0
            
        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Error al eliminar claves de caché: {e}")
            return 0
    
    def clear(self) -> bool:
        """
        Elimina todas las claves de la caché.
        
        Returns:
            True si se eliminaron todas las claves, False en caso contrario
        """
        if not self.is_connected():
            return False
            
        try:
            self._client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Error al limpiar la caché: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verifica si una clave existe en la caché.
        
        Args:
            key: Clave a verificar
            
        Returns:
            True si la clave existe, False en caso contrario
        """
        if not self.is_connected():
            return False
            
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Error al verificar existencia de clave {key}: {e}")
            return False

def cache_result(expire_seconds: int = 86400, cache_key_prefix: str = "func"):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        expire_seconds: Tiempo de expiración en segundos
        cache_key_prefix: Prefijo para la clave de caché
        
    Returns:
        Función decorada con caché
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Si el primer argumento es 'self', usamos la instancia de la clase
            # para acceder a su caché, si existe
            if args and hasattr(args[0], 'cache'):
                cache = args[0].cache
            else:
                # Usar la instancia global por defecto
                cache = cache_manager
            
            # Crear una clave única para esta llamada
            key_parts = [cache_key_prefix, func.__name__]
            
            # Incluir argumentos posicionales
            key_parts.extend(str(arg) for arg in args[1:])  # Saltar 'self'
            
            # Incluir argumentos con nombre
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = ":".join(key_parts)
            
            # Intentar obtener el resultado de la caché
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Resultado obtenido de caché para {cache_key}")
                return cached_result
            
            # Si no está en caché, ejecutar la función
            result = func(*args, **kwargs)
            
            # Almacenar el resultado en caché
            if result is not None:
                cache.set(cache_key, result, expire_seconds)
            
            return result
        return wrapper
    return decorator


# Instancia global del cache manager
cache_manager = CacheManager()
