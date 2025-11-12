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
        Inicializa el gestor de caché con una conexión a Redis.
        
        Args:
            redis_url: URL de conexión a Redis (opcional, si no se proporciona 
                      usará variable de entorno REDIS_URL o fallback a caché en memoria)
        """
        self.use_redis = False
        self._memory_cache = {}  # Caché en memoria como fallback
        
        # Intentar conectar a Redis
        try:
            redis_connection = redis_url or os.getenv('REDIS_URL')
            
            if redis_connection:
                self.redis = redis.from_url(redis_connection)
                # Verificar conexión
                self.redis.ping()
                self.use_redis = True
                logger.info("Caché distribuida (Redis) conectada correctamente")
            else:
                logger.warning("No se encontró URL de Redis, usando caché en memoria")
        except Exception as e:
            logger.warning(f"Error al conectar a Redis: {e}. Se usará caché en memoria")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un valor de la caché.
        
        Args:
            key: Clave a buscar en la caché
            
        Returns:
            Valor almacenado o None si no existe o ha expirado
        """
        try:
            if self.use_redis:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
                return None
            else:
                # Caché en memoria con expiración
                if key in self._memory_cache:
                    item = self._memory_cache[key]
                    # Verificar expiración
                    if item['expiry'] > time.time():
                        return item['data']
                    else:
                        # Expirado, eliminarlo
                        del self._memory_cache[key]
                return None
        except Exception as e:
            logger.error(f"Error al leer de caché para clave {key}: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], expire_seconds: int = 86400) -> bool:
        """
        Guarda un valor en la caché con tiempo de expiración.
        
        Args:
            key: Clave única para almacenar el valor
            value: Valor a almacenar (debe ser serializable a JSON)
            expire_seconds: Tiempo de expiración en segundos (default: 24 horas)
            
        Returns:
            Boolean indicando si se guardó correctamente
        """
        try:
            if self.use_redis:
                self.redis.setex(
                    key,
                    expire_seconds,
                    json.dumps(value)
                )
            else:
                # Guardar en memoria con tiempo de expiración
                self._memory_cache[key] = {
                    'data': value,
                    'expiry': time.time() + expire_seconds
                }
            return True
        except Exception as e:
            logger.error(f"Error al guardar en caché para clave {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Elimina un valor de la caché.
        
        Args:
            key: Clave a eliminar
            
        Returns:
            Boolean indicando si se eliminó correctamente
        """
        try:
            if self.use_redis:
                self.redis.delete(key)
            else:
                if key in self._memory_cache:
                    del self._memory_cache[key]
            return True
        except Exception as e:
            logger.error(f"Error al eliminar de caché para clave {key}: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Limpia toda la caché (solo para desarrollo/testing).
        
        Returns:
            Boolean indicando si se limpió correctamente
        """
        try:
            if self.use_redis:
                self.redis.flushdb()
            else:
                self._memory_cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error al limpiar caché: {e}")
            return False

# Decorador para cachear resultados de funciones
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
            # Obtener instancia de caché (debe estar disponible en el primer argumento self)
            if len(args) > 0 and hasattr(args[0], 'cache'):
                cache_manager = args[0].cache
            else:
                # No hay caché disponible, ejecutar función normalmente
                return func(*args, **kwargs)
                
            # Generar clave de caché basada en argumentos
            cache_key = f"{cache_key_prefix}:{func.__name__}:"
            
            # Añadir args y kwargs a la clave
            for arg in args[1:]:  # Omitir self
                if isinstance(arg, (str, int, float, bool)):
                    cache_key += f":{str(arg)}"
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    cache_key += f":{k}={v}"
            
            # Intentar obtener de caché
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Caché hit para {cache_key}")
                return cached_result
            
            # No está en caché, ejecutar función
            result = func(*args, **kwargs)
            
            # Guardar en caché
            if result is not None:
                cache_manager.set(cache_key, result, expire_seconds)
                logger.debug(f"Guardado en caché: {cache_key}")
            
            return result
        return wrapper
    return decorator


# Instancia global del cache manager
cache_manager = CacheManager()
