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

class APIClient:
    """
    Cliente HTTP centralizado con manejo robusto de errores y reintentos.
    
    Esta clase encapsula toda la lógica de comunicación HTTP, incluyendo:
    - Reintentos con backoff exponencial
    - Manejo de timeouts
    - Logging de peticiones/respuestas
    - Validación de respuestas
    """
    
    def __init__(self, default_timeout: int = 15, max_retries: int = 3):
        """
        Inicializa el cliente API con configuraciones por defecto.
        
        Args:
            default_timeout: Tiempo máximo de espera por defecto en segundos
            max_retries: Número máximo de reintentos para peticiones fallidas
        """
        self.session = requests.Session()
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        
        # Configurar headers por defecto
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
        })
        
        # Configurar la sesión
        self.session.verify = True  # Verificar certificados SSL
        self.session.allow_redirects = True  # Permitir redirecciones
        self.session.max_redirects = 5  # Límite de redirecciones
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True
    )
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, 
            headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> requests.Response:
        """
        Realiza una petición GET con manejo robusto de errores y reintentos.
        
        Args:
            url: URL del endpoint
            params: Parámetros de consulta
            headers: Headers adicionales para esta petición
            timeout: Tiempo máximo de espera en segundos (sobreescribe el timeout por defecto)
            
        Returns:
            Response: Objeto respuesta de requests
            
        Raises:
            requests.exceptions.RequestException: Si la petición falla después de los reintentos
        """
        final_headers = {**self.session.headers, **(headers or {})}
        final_timeout = timeout or self.default_timeout
        
        try:
            logger.debug(f"Realizando petición GET a {url} con params: {params}")
            response = self.session.get(
                url,
                params=params,
                headers=final_headers,
                timeout=final_timeout
            )
            
            # Forzar el lanzamiento de excepción para códigos 4xx/5xx
            response.raise_for_status()
            
            logger.debug(f"Respuesta exitosa de {url} - Status: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a {url}: {str(e)}")
            raise
    
    def post(self, url: str, json_data: Optional[Dict[str, Any]] = None, 
             headers: Optional[Dict[str, str]] = None, timeout: Optional[int] = None) -> requests.Response:
        """
        Realiza una petición POST con manejo robusto de errores y reintentos.
        
        Args:
            url: URL del endpoint
            json_data: Datos a enviar en formato JSON
            headers: Headers adicionales para esta petición
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Response: Objeto respuesta de requests
        """
        final_headers = {**self.session.headers, **(headers or {})}
        final_headers['Content-Type'] = 'application/json'
        final_timeout = timeout or self.default_timeout
        
        try:
            logger.debug(f"Realizando petición POST a {url} con datos: {json_data}")
            response = self.session.post(
                url,
                json=json_data,
                headers=final_headers,
                timeout=final_timeout
            )
            
            response.raise_for_status()
            logger.debug(f"Respuesta exitosa de {url} - Status: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición POST a {url}: {str(e)}")
            raise
    
    def close(self):
        """Cierra la sesión de requests."""
        self.session.close()
    
    def __enter__(self):
        """Permite usar la clase en un contexto with."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Asegura que la sesión se cierre correctamente."""
        self.close()
