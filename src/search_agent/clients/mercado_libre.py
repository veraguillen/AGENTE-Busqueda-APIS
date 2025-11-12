"""
Agente para búsqueda en MercadoLibre.
Este agente se encarga de buscar productos en MercadoLibre utilizando la API de mercado-libre7.
"""
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union

# Importar dependencias
from app.config_manager import ConfigManager
from utils.api_client import APIClient

# Configurar logging
logger = logging.getLogger(__name__)

class AgenteML:
    """Agente especializado en búsquedas en MercadoLibre."""
    
    def __init__(
        self, 
        rapidapi_key: str,
        api_client: APIClient,
        config: ConfigManager,
        cache=None,
        monitor=None
    ):
        """
        Inicializa el agente con la clave de API de RapidAPI.
        
        Args:
            rapidapi_key: Clave de API de RapidAPI
            api_client: Instancia de APIClient para realizar peticiones HTTP
            config: Instancia de ConfigManager
            cache: Instancia de caché (opcional)
            monitor: Instancia de monitor (opcional)
        """
        self.rapidapi_key = rapidapi_key
        self.api_client = api_client
        self.config = config
        self.cache = cache
        self.monitor = monitor
        
        # Cargar configuración
        self.api_config = self.config.get('mercadolibre.api', {})
        self.search_config = self.config.get('mercadolibre.search', {})
        
        # Validar configuración requerida
        if not self.api_config.get('host'):
            logger.warning("No se configuró el host de la API de MercadoLibre. Usando valor por defecto.")
            self.api_config['host'] = 'mercado-libre7.p.rapidapi.com'
            
        if not self.api_config.get('endpoints', {}).get('search'):
            logger.warning("No se configuró el endpoint de búsqueda. Usando valor por defecto.")
            if 'endpoints' not in self.api_config:
                self.api_config['endpoints'] = {}
            self.api_config['endpoints']['search'] = '/listings_for_search'
        
        # Configurar headers específicos para MercadoLibre
        self.headers = {
            'X-RapidAPI-Key': self.rapidapi_key,
            'X-RapidAPI-Host': self.api_config['host'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Actualizar headers del cliente HTTP
        self.api_client.session.headers.update(self.headers)
        
        # Configurar timeout por defecto
        self.timeout = self.api_config.get('timeout', 30)
        
        logger.info(f"AgenteML inicializado correctamente. Host: {self.api_config['host']}")
        logger.debug(f"Configuración de búsqueda: {self.search_config}")
        logger.debug(f"Headers de la API: {self.headers}")
    
    def search(
        self, 
        query: str, 
        country: str = "AR",
        limit: int = None, 
        offset: int = 0,
        sort: str = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Busca productos en MercadoLibre utilizando la API de mercado-libre7.
        
        Args:
            query: Término de búsqueda (ej: 'iphone')
            country: Código de país de 2 letras (ej: 'AR', 'BR', 'MX')
            limit: Número máximo de resultados por página (opcional, usa el valor por defecto de la configuración)
            offset: Desplazamiento para paginación
            sort: Criterio de ordenación ('relevance', 'price_asc', 'price_desc')
            
        Returns:
            Tupla con (lista de productos normalizados, total de resultados)
        """
        # Obtener configuración
        default_limit = self.api_config.get('default_limit', 10)
        max_limit = self.api_config.get('max_limit', 50)
        valid_sorts = self.search_config.get('sort_options', ['relevance', 'price_asc', 'price_desc'])
        default_sort = self.search_config.get('default_sort', 'relevance')
        
        # Validar y normalizar parámetros
        country = country.upper()
        limit = min(max(1, limit if limit is not None else default_limit), max_limit)
        page_num = (offset // limit) + 1
        sort = sort if sort in valid_sorts else default_sort
        
        # Configurar los parámetros de la consulta
        params = {
            'search_str': query,
            'country': country.lower(),
            'page_num': str(page_num),
            'sort_by': sort,
            'limit': str(limit)
        }
        
        # Construir URL base
        endpoint = self.api_config.get('endpoints', {}).get('search', '/listings_for_search')
        base_url = f"https://{self.api_config.get('host', 'mercado-libre7.p.rapidapi.com')}{endpoint}"
        
        # Mostrar información de depuración
        logger.debug(f"URL de la petición: {base_url}")
        logger.debug(f"Headers: {self.headers}")
        logger.debug(f"Parámetros: {params}")
        
        # Realizar la petición
        try:
            start_time = time.time()
            
            # Usar el APIClient para realizar la petición
            response = self.api_client.get(
                url=base_url,
                params=params,
                headers=self.headers,
                timeout=self.api_config.get('timeout', 30)
            )
            
            # Calcular tiempo de respuesta
            response_time = time.time() - start_time
            
            # Mostrar información de la respuesta
            logger.info(f"Respuesta de la API - Status: {response.status_code}")
            logger.debug(f"URL de respuesta: {response.url}")
            logger.debug(f"Headers de respuesta: {dict(response.headers)}")
            
            # Registrar métricas
            if self.monitor:
                self.monitor.log_metric('ml_search_response_time', response_time)
            
            # Procesar la respuesta
            return self._process_search_response(response)
                
        except Exception as e:
            error_msg = f"Error al realizar la búsqueda: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if self.monitor:
                self.monitor.log_error('search_request_error', error_msg)
            return [], 0
    
    def _process_search_response(self, response) -> Tuple[List[Dict[str, Any]], int]:
        """
        Procesa la respuesta de la API de búsqueda.
        
        Args:
            response: Objeto de respuesta de la API
            
        Returns:
            Tupla con (lista de productos normalizados, total de resultados)
        """
        try:
            # Intentar decodificar la respuesta JSON
            data = response.json()
            logger.debug(f"Respuesta JSON recibida")
            
            if response.status_code != 200:
                error_msg = f"Error en la búsqueda: {response.status_code} - {data}"
                logger.error(error_msg)
                if self.monitor:
                    self.monitor.log_error('ml_search_error', error_msg)
                return [], 0
            
            # Extraer resultados de la respuesta
            results = self._extract_results(data)
            
            # Normalizar los resultados
            normalized_results = [self._normalize_result(item) for item in results]
            
            # Obtener el total de resultados
            total = self._extract_total_results(data, len(normalized_results))
            
            logger.info(f"Resultados encontrados: {len(normalized_results)} de {total} totales")
            
            # Registrar conteo de resultados
            if self.monitor:
                self.monitor.log_metric('ml_search_result_count', len(normalized_results))
            
            return normalized_results, total
            
        except Exception as json_error:
            error_msg = f"Error al procesar la respuesta JSON: {str(json_error)}"
            logger.error(error_msg)
            logger.debug(f"Contenido de la respuesta: {getattr(response, 'text', '')[:1000]}")
            if self.monitor:
                self.monitor.log_error('json_parse_error', error_msg)
            return [], 0
    
    def _extract_results(self, data: Dict) -> List[Dict]:
        """Extrae los resultados de la respuesta de la API."""
        if isinstance(data, list):
            return data
        if 'data' in data and 'results' in data['data']:
            return data['data']['results']
        if 'results' in data:
            return data['results']
        return []
    
    def _extract_total_results(self, data: Dict, default: int = 0) -> int:
        """Extrae el total de resultados de la respuesta de la API."""
        if 'paging' in data and 'total' in data['paging']:
            return int(data['paging']['total'])
        if 'data' in data and 'paging' in data['data'] and 'total' in data['data']['paging']:
            return int(data['data']['paging']['total'])
        return default
    
    def get_product_details(self, product_id: str, site_id: str = "MLA") -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de un producto específico.
        
        Args:
            product_id: ID del producto en MercadoLibre
            site_id: ID del sitio (ej: 'MLA' para Argentina)
            
        Returns:
            Diccionario con los detalles del producto o None si hay un error
        """
        if not product_id:
            return None
            
        # Obtener configuración
        hosts = self.config.get('mercadolibre.hosts', [])
        if not hosts:
            return None
            
        base_url = f"https://{hosts[0]}"
        url = f"{base_url}/items/{product_id}"
        
        try:
            response = self.api_client.get(
                url,
                params={"site_id": site_id},
                timeout=self.config.get('api.timeout', 30)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error al obtener detalles del producto {product_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción al obtener detalles del producto {product_id}: {str(e)}", exc_info=True)
            if self.monitor:
                self.monitor.track_exception(e, {"context": "get_product_details", "product_id": product_id})
            return None
    
    def get_seller_info(self, seller_id: int, site_id: str = "MLA") -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un vendedor.
        
        Args:
            seller_id: ID del vendedor en MercadoLibre
            site_id: ID del sitio (ej: 'MLA' para Argentina)
            
        Returns:
            Diccionario con la información del vendedor o None si hay un error
        """
        if not seller_id:
            return None
            
        # Obtener configuración
        hosts = self.config.get('mercadolibre.hosts', [])
        if not hosts:
            return None
            
        base_url = f"https://{hosts[0]}"
        url = f"{base_url}/sellers/{seller_id}"
        
        try:
            response = self.api_client.get(
                url,
                params={"site_id": site_id},
                timeout=self.config.get('api.timeout', 30)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error al obtener información del vendedor {seller_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción al obtener información del vendedor {seller_id}: {str(e)}", exc_info=True)
            if self.monitor:
                self.monitor.track_exception(e, {"context": "get_seller_info", "seller_id": seller_id})
            return None
    
    def get_category_info(self, category_id: str, site_id: str = "MLA") -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una categoría.
        
        Args:
            category_id: ID de la categoría en MercadoLibre
            site_id: ID del sitio (ej: 'MLA' para Argentina)
            
        Returns:
            Diccionario con la información de la categoría o None si hay un error
        """
        if not category_id:
            return None
            
        # Obtener configuración
        hosts = self.config.get('mercadolibre.hosts', [])
        if not hosts:
            return None
            
        base_url = f"https://{hosts[0]}"
        url = f"{base_url}/categories/{category_id}"
        
        try:
            response = self.api_client.get(
                url,
                params={"site_id": site_id},
                timeout=self.config.get('api.timeout', 30)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error al obtener información de la categoría {category_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Excepción al obtener información de la categoría {category_id}: {str(e)}", exc_info=True)
            if self.monitor:
                self.monitor.track_exception(e, {"context": "get_category_info", "category_id": category_id})
            return None
        
    def _normalize_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza un resultado de búsqueda a un formato estándar.
        
        Args:
            item: Item de resultado de búsqueda
            
        Returns:
            Diccionario con el resultado normalizado
        """
        if not item:
            return {}
            
        # Extraer información del vendedor
        seller_info = self._extract_seller_info(item)
        
        # Extraer información de envío
        shipping_info = self._extract_shipping_info(item)
        
        # Extraer información de ubicación
        location_info = self._extract_location_info(item)
        
        # Construir el resultado normalizado
        normalized = {
            'id': item.get('id', ''),
            'title': item.get('title', ''),
            'price': self._parse_price(item.get('price')),
            'original_price': self._parse_price(item.get('original_price')),
            'currency_id': item.get('currency_id', 'ARS'),
            'available_quantity': int(item.get('available_quantity', 0)),
            'sold_quantity': int(item.get('sold_quantity', 0)),
            'condition': item.get('condition', 'not_specified'),
            'permalink': item.get('url') or item.get('permalink', ''),
            'thumbnail': item.get('thumbnail') or item.get('thumbnail_url', ''),
            'accepts_mercadopago': item.get('accepts_mercadopago', False),
            'shipping': shipping_info,
            'seller': seller_info,
            'location': location_info,
            'attributes': item.get('attributes', []),
            'tags': item.get('tags', []),
            'original_data': item  # Mantener los datos originales para referencia
        }
        
        # Asegurar que los campos opcionales tengan valores por defecto
        if 'warranty' not in normalized:
            normalized['warranty'] = item.get('warranty', '')
            
        if 'official_store_name' not in normalized:
            normalized['official_store_name'] = item.get('official_store_name')
        
        return normalized
    
    def _extract_seller_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae y normaliza la información del vendedor."""
        seller = item.get('seller', {})
        
        # Manejar diferentes formatos de vendedor
        if isinstance(seller, str):
            # Si el vendedor es solo un string (nombre)
            seller_name = seller.replace('Por ', '').strip()
            return {
                'id': None,
                'nickname': seller_name,
                'power_seller_status': None
            }
        
        # Si el vendedor es un diccionario
        return {
            'id': seller.get('id'),
            'nickname': seller.get('nickname', '').replace('Por ', '').strip(),
            'power_seller_status': seller.get('power_seller_status'),
            'seller_reputation': seller.get('seller_reputation', {})
        }
    
    def _extract_shipping_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae y normaliza la información de envío."""
        shipping = item.get('shipping', {})
        
        # Manejar diferentes formatos de envío
        if isinstance(shipping, bool):
            return {
                'free_shipping': shipping,
                'store_pick_up': False,
                'logistic_type': 'not_specified'
            }
            
        if isinstance(shipping, dict):
            return {
                'free_shipping': shipping.get('free_shipping', False),
                'store_pick_up': shipping.get('store_pick_up', False),
                'logistic_type': shipping.get('logistic_type', 'not_specified'),
                'mode': shipping.get('mode', 'not_specified')
            }
            
        return {
            'free_shipping': False,
            'store_pick_up': False,
            'logistic_type': 'not_specified'
        }
    
    def _extract_location_info(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Extrae y normaliza la información de ubicación."""
        location = item.get('location', {})
        address = item.get('address', {})
        
        # Extraer ciudad y estado de diferentes ubicaciones posibles
        city = location.get('city') or address.get('city_name', '')
        state = location.get('state') or address.get('state_name', '')
        country = location.get('country') or address.get('country_name', '')
        
        return {
            'city': city,
            'state': state,
            'country': country,
            'latitude': location.get('latitude'),
            'longitude': location.get('longitude')
        }
    
    def _parse_price(self, price: Any) -> float:
        """Convierte el precio a float, manejando diferentes formatos."""
        if price is None:
            return 0.0
            
        if isinstance(price, (int, float)):
            return float(price)
            
        if isinstance(price, str):
            # Eliminar símbolos de moneda y espacios
            price_str = price.replace('$', '').replace(' ', '').replace(',', '.').strip()
            try:
                return float(price_str)
            except (ValueError, TypeError):
                return 0.0
                
        return 0.0
