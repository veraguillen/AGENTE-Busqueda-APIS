"""
Cliente HTTP centralizado con manejo robusto de errores y reintentos.
"""
import requests
import logging
from typing import Dict, Any, Optional, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Excepciones que justifican un reintento
RETRYABLE_EXCEPTIONS = (
    requests.exceptions.RequestException,
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.HTTPError
)

class HTTPClient:
    """
    Cliente HTTP centralizado con manejo robusto de errores y reintentos.
    
    Esta clase encapsula toda la lógica de comunicación HTTP, incluyendo:
    - Manejo de reintentos con backoff exponencial
    - Manejo de errores y excepciones
    - Logging de solicitudes y respuestas
    - Manejo de timeouts
    """
    
    def __init__(self, base_url: str = "", default_headers: Optional[Dict[str, str]] = None, 
                 timeout: int = 30, max_retries: int = 3):
        """
        Inicializa el cliente HTTP.
        
        Args:
            base_url: URL base para todas las solicitudes
            default_headers: Headers por defecto para todas las solicitudes
            timeout: Timeout por defecto en segundos
            max_retries: Número máximo de reintentos
        """
        self.base_url = base_url.rstrip('/') if base_url else ""
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True
    )
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Realiza una solicitud HTTP con reintentos automáticos.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Ruta del endpoint (sin la URL base)
            **kwargs: Argumentos adicionales para requests.request()
            
        Returns:
            Response: Objeto de respuesta de requests
            
        Raises:
            requests.exceptions.RequestException: Si la solicitud falla después de los reintentos
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}" if self.base_url else endpoint
        
        # Configurar headers
        headers = self.default_headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        # Configurar timeout si no se especifica
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        logger.debug(f"Enviando solicitud {method} a {url}")
        
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                **kwargs
            )
            
            # Loguear respuesta
            logger.debug(f"Respuesta de {url}: {response.status_code}")
            
            # Verificar códigos de error
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la solicitud a {url}: {str(e)}")
            raise
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Realiza una solicitud GET."""
        return self.request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Realiza una solicitud POST."""
        return self.request('POST', endpoint, json=json, **kwargs)
    
    def put(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """Realiza una solicitud PUT."""
        return self.request('PUT', endpoint, json=json, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """Realiza una solicitud DELETE."""
        return self.request('DELETE', endpoint, **kwargs)
    
    def close(self):
        """Cierra la sesión de requests."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
