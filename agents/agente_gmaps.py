"""Agente para búsqueda de negocios en Google Maps/Places API.
Este agente se encarga de localizar negocios físicos a partir de nombres de vendedores.
Incluye opciones de fallback si la API principal no responde.
"""
import requests
import logging
import os
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Union

# Importar el formateador de contactos
try:
    from app.utils.formatters import format_business_contact_cards
    HAS_FORMATTERS = True
except ImportError:
    HAS_FORMATTERS = False
    logging.warning("No se pudo importar el formateador de contactos. Algunas funciones no estarán disponibles.")

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

# Constantes
RAPIDAPI_MAPS_DATA_URL = "https://maps-data.p.rapidapi.com/searchmaps.php"
GOOGLE_PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
REQUEST_TIMEOUT = 10  # segundos (reducido para mayor responsividad)
MAX_RETRIES = 2       # intentos máximos para conectar con la API

class AgenteGMaps:
    """Agente especializado en búsquedas de negocios usando Google Places API."""
    
    def __init__(self, google_api_key: str, cache=None, config=None, monitor=None):
        """
        Inicializa el agente con la clave de API de Google Maps.
        
        Args:
            google_api_key: Clave API de Google Maps
            cache: Instancia de CacheManager (opcional)
            config: Instancia de ConfigManager (opcional)
            monitor: Instancia de Monitor para métricas (opcional)
        """
        self.api_key = google_api_key
        self.cache = cache
        self.config = config
        self.monitor = monitor
        
        # Configurar timeout desde config si está disponible
        self.timeout = REQUEST_TIMEOUT
        if config:
            self.timeout = config.get("request_timeout", REQUEST_TIMEOUT)
        
        logger.info("AgenteGMaps inicializado correctamente.")
    
    def _clean_seller_name(self, seller_name: str) -> str:
        """
        Limpia el nombre del vendedor para optimizar la búsqueda.
        
        Args:
            seller_name: Nombre original del vendedor
            
        Returns:
            Nombre limpio para usar en búsqueda
        """
        if not seller_name:
            return ""
        
        # Convertir a string por seguridad
        seller_name = str(seller_name)
        
        # Eliminar sufijos comunes de tiendas en línea
        suffixes_to_remove = [
            "_TiendaOficial", "_Tienda_Oficial", "_Oficial", "_Official",
            "_Store", "_Tienda", "_ML", "_Shop", "_Argentina"
        ]
        
        cleaned_name = seller_name
        for suffix in suffixes_to_remove:
            cleaned_name = cleaned_name.replace(suffix, "")
        
        # Eliminar caracteres especiales y espacios extra
        cleaned_name = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]', ' ', cleaned_name)
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        logger.debug(f"Nombre de vendedor limpiado: '{seller_name}' -> '{cleaned_name}'")
        return cleaned_name
    
    def _format_search_query(self, seller_name: str) -> str:
        """
        Formatea el nombre del vendedor para búsqueda.
        
        Args:
            seller_name: Nombre del vendedor (ya limpiado)
            
        Returns:
            Consulta optimizada para búsqueda
        """
        # Usar solo el nombre del vendedor, sin añadir contexto geográfico
        query = seller_name.strip()
        logger.debug(f"Nombre de vendedor para búsqueda: '{query}'")
        return query
    
    def find_business(self, seller_name: str, google_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Busca información del negocio usando primero RapidAPI Maps Data y, si falla, con Google Places API directa.
        
        Args:
            seller_name: Nombre del vendedor a buscar
            google_api_key: Clave API de Google Maps para fallback (opcional)
            
        Returns:
            Resultados en formato JSON con la información del negocio
        """
        if not seller_name:
            logger.error("Se requiere un nombre de vendedor válido")
            return {"status": "error", "message": "Nombre de vendedor no proporcionado"}
        
        # Verificar caché si está disponible
        cache_key = f"gmaps_business_{seller_name}"
        if self.cache:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Resultados recuperados de caché para {seller_name}")
                return json.loads(cached_result)
        
        # Preparar la consulta
        cleaned_name = self._clean_seller_name(seller_name)
        query = self._format_search_query(cleaned_name)
        
        # 1. Intentar con RapidAPI Maps Data primero
        logger.info(f"Buscando negocio para '{seller_name}' (limpiado: '{query}')")
        
        try:
            # Intentar con RapidAPI Maps Data con timeout reducido
            result = self._try_rapidapi_maps_data(query)
            
            # Si tenemos resultados válidos, guardar en caché y devolver
            if result.get("status") == "ok" and result.get("data"):
                if self.cache:
                    self.cache.set(cache_key, json.dumps(result), ttl=86400)  # 24 horas
                return result
                
            # Si RapidAPI falló y tenemos una clave de Google Maps, intentar fallback
            if google_api_key or (self.api_key != "maps-data.p.rapidapi.com"):
                fallback_key = google_api_key or self.api_key
                logger.info(f"Intentando fallback con Google Maps API directa para '{query}'")
                fallback_result = self._try_google_places_direct(query, fallback_key)
                
                # Guardar resultado del fallback en caché
                if fallback_result.get("status") == "ok" and self.cache:
                    self.cache.set(cache_key, json.dumps(fallback_result), ttl=86400)
                    
                return fallback_result
            
            # Si llegamos aquí, devolver el resultado original de RapidAPI
            return result
            
        except Exception as e:
            error_msg = f"Error buscando negocio: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
            
    def _try_rapidapi_maps_data(self, query: str) -> Dict[str, Any]:
        """
        Intenta buscar usando RapidAPI Maps Data con reintentos en caso de error.
        
        Args:
            query: Término de búsqueda
            
        Returns:
            Resultados formateados o mensaje de error
        """
        # Preparar parámetros y cabeceras para RapidAPI
        params = {
            'query': query,
            'country': 'ar'  # Argentina
        }
        
        headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': "maps-data.p.rapidapi.com"
        }
        
        # Intentar con reintentos en caso de error de conexión
        for attempt in range(MAX_RETRIES):
            try:
                # Usar un timeout menor en cada reintento
                current_timeout = REQUEST_TIMEOUT / (attempt + 1)
                logger.debug(f"Intento {attempt+1}/{MAX_RETRIES} con RapidAPI, timeout={current_timeout}s")
                
                response = requests.get(
                    RAPIDAPI_MAPS_DATA_URL, 
                    params=params, 
                    headers=headers,
                    timeout=current_timeout
                )
                
                # Verificar código de respuesta HTTP
                response.raise_for_status()
                
                # Intentar parsear la respuesta JSON
                try:
                    data = response.json()
                    return self._format_response(data)
                except json.JSONDecodeError as je:
                    logger.warning(f"Error al decodificar JSON de RapidAPI: {str(je)}")
                    # Continuar con el siguiente intento
                    continue
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout en intento {attempt+1} con RapidAPI")
                # Continuar con el siguiente intento
                
            except requests.RequestException as e:
                logger.warning(f"Error de conexión en RapidAPI: {str(e)}")
                # Esperar un poco antes del siguiente intento
                time.sleep(1)
        
        # Si llegamos aquí, todos los intentos fallaron
        logger.error(f"Todos los intentos con RapidAPI fallaron para '{query}'")
        return {"status": "error", "message": "No se pudo conectar con RapidAPI Maps Data"}
    
    def _try_google_places_direct(self, query: str, api_key: str) -> Dict[str, Any]:
        """
        Intenta buscar directamente en la API de Google Places como fallback.
        
        Args:
            query: Término de búsqueda
            api_key: Clave API de Google Maps
            
        Returns:
            Resultados formateados o mensaje de error
        """
        params = {
            'query': query,
            'key': api_key,
            'language': 'es',
            'region': 'ar'
        }
        
        try:
            logger.info(f"Realizando búsqueda directa en Google Places API: '{query}'")
            response = requests.get(GOOGLE_PLACES_API_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Convertir formato de Google Places al formato estándar del agente
            return self._format_google_places_response(data)
            
        except Exception as e:
            logger.error(f"Error en fallback con Google Places API: {str(e)}")
            return {"status": "error", "message": f"Error en fallback: {str(e)}"}
    
    def get_formatted_contacts(self, seller_name: str, google_api_key: Optional[str] = None) -> str:
        """
        Busca información de negocio y devuelve tarjetas de contacto formateadas.
        
        Args:
            seller_name: Nombre del vendedor a buscar
            google_api_key: Clave API de Google opcional para fallback
        
        Returns:
            Tarjetas de contacto en formato Markdown
        """
        result = self.find_business(seller_name, google_api_key)
        
        if HAS_FORMATTERS:
            return format_business_contact_cards(result)
        else:
            # Fallback si el formateador no está disponible
            if result.get("status") != "ok":
                return f"No se encontraron resultados para {seller_name}"
                
            data = result.get("data", [])
            if not data:
                return f"No se encontraron resultados para {seller_name}"
                
            output = f"Resultados para {seller_name}:\n\n"
            
            for item in data:
                output += f"- {item.get('name', 'Desconocido')}\n"
                output += f"  Teléfono: {item.get('phone_number', 'No disponible')}\n"
                output += f"  Dirección: {item.get('full_address', 'No disponible')}\n\n"
                
            return output
    
    def _format_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea la respuesta de RapidAPI Maps Data al formato estándar del agente.
        
        Args:
            api_response: Respuesta original de la API
            
        Returns:
            Respuesta formateada según el formato estándar
        """
        # Verificar si la respuesta contiene resultados
        results = api_response.get("results", [])
        
        if not results or not isinstance(results, list):
            logger.warning("RapidAPI Maps Data no devolvió resultados válidos")
            return {"status": "no_results", "message": "No se encontraron resultados."}
        
        formatted_data = []
        
        for place in results[:3]:  # Limitar a los 3 mejores resultados
            try:
                # Los campos pueden variar según la API de RapidAPI Maps Data
                place_data = {
                    "business_id": place.get("id", ""),
                    "phone_number": place.get("phone", ""),
                    "name": place.get("name", ""),
                    "full_address": place.get("address", ""),
                    "review_count": place.get("reviews", 0),
                    "rating": place.get("rating", 0.0),
                    "website": place.get("website", ""),
                    "place_link": place.get("link", "")
                }
                formatted_data.append(place_data)
            except Exception as e:
                logger.error(f"Error formateando datos de RapidAPI Maps Data: {str(e)}")
        
        return {
            "status": "ok" if formatted_data else "no_results",
            "data": formatted_data
        }
        
    def _format_google_places_response(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatea la respuesta de la API directa de Google Places al formato estándar del agente.
        
        Args:
            api_response: Respuesta original de Google Places API
            
        Returns:
            Respuesta formateada según el formato estándar
        """
        # Verificar estado de la respuesta
        status = api_response.get("status", "")
        if status != "OK":
            logger.warning(f"Google Places API devolvió estado no OK: {status}")
            return {"status": "no_results", "message": f"No se encontraron resultados. Status: {status}"}
        
        # Obtener resultados
        results = api_response.get("results", [])
        if not results:
            return {"status": "no_results", "message": "No se encontraron resultados."}
        
        formatted_data = []
        
        # Procesar los primeros 3 resultados
        for place in results[:3]:
            try:
                # Extraer ID del place
                place_id = place.get("place_id", "")
                
                # Manejar el formato de Google Places API
                place_data = {
                    "business_id": place_id,
                    "phone_number": "",  # Google Places API textsearch no incluye teléfono
                    "name": place.get("name", ""),
                    "full_address": place.get("formatted_address", ""),
                    "review_count": place.get("user_ratings_total", 0),
                    "rating": place.get("rating", 0.0),
                    "website": "",  # No incluido en textsearch
                    "place_link": f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ""
                }
                formatted_data.append(place_data)
            except Exception as e:
                logger.error(f"Error formateando datos de Google Places API: {str(e)}")
        

    def search_business(self, query: str, use_fallback: bool = True) -> Dict[str, Any]:
        """
        Busca un negocio usando varias APIs disponibles, con mecanismo de fallback.
        
        Esta función intentará usar primero RapidAPI Maps Data y, si falla y se solicita, 
        usará la API directa de Google Maps como fallback.
        
        Args:
            query: Consulta de búsqueda (nombre del vendedor)
            use_fallback: Si es True, usar fallback con Google Maps API cuando RapidAPI falla
            
        Returns:
            Resultados formateados o mensaje de error
        """
        try:
            # Verificar si hay caché
            cache_key = f"business_search:{query.lower().strip()}"
            if self.cache:
                cached = self.cache.get(cache_key)
                if cached:
                    if self.monitor:
                        self.monitor.log_metric('gmap_cache_hit', 1)
                    return cached
            
            # Intentar con RapidAPI primero
            resultados = self.find_business(query)
            
            # Si no hay resultados y está habilitado el fallback, intentar con Google Places
            if (not resultados or 'error' in resultados) and use_fallback:
                logger.info("RapidAPI no devolvió resultados, intentando con Google Places API...")
                if self.monitor:
                    self.monitor.log_metric('gmap_api_fallback', 1)
                resultados = self._try_google_places_direct(query, self.api_key)
            
            # Guardar en caché si hay resultados
            if resultados and 'error' not in resultados and self.cache:
                self.cache.set(cache_key, resultados, ttl=86400)  # Cachear por 24 horas
                
            return resultados
            
        except Exception as e:
            logger.error(f"Error en búsqueda de negocio: {str(e)}")
            if self.monitor:
                self.monitor.log_error('gmap_search_error', str(e))
            return {
                'error': True,
                'message': f'Error al buscar el negocio: {str(e)}',
                'source': 'AgenteGMaps',
                'results': []
            }

def search_business(query: str, api_key: str, use_fallback: bool = True) -> Dict[str, Any]:
    """
    Función de conveniencia para buscar un negocio sin instanciar la clase.
    
    Args:
        query: Consulta de búsqueda (nombre del vendedor)
        api_key: Clave API (funciona con RapidAPI o Google Maps API keys)
        use_fallback: Si es True, usar fallback con Google Maps API cuando RapidAPI falla
        
    Returns:
        Resultados formateados o mensaje de error
    """
    agent = AgenteGMaps(google_api_key=api_key)
    return agent.search_business(query, use_fallback)

# Ejemplo de uso independiente del agente
if __name__ == "__main__":
    # Configurar logging para ejecución directa
    logging.basicConfig(level=logging.INFO)
    
    # Cargar variables de entorno
    from dotenv import load_dotenv
    load_dotenv()
    
    # Claves API
    rapidapi_key = os.environ.get("RAPIDAPI_KEY") or os.environ.get("GOOGLE_MAPS_DATA_API_KEY")
    
    if not rapidapi_key:
        print("❌ ERROR: No se encontró clave API en las variables de entorno")
    else:
        # Inicializar el agente
        agente = AgenteGMaps(google_api_key=rapidapi_key)
        
        # Buscar un negocio de ejemplo
        seller_name = "Al Click"
        resultado = agente.find_business(seller_name)
        
        # Mostrar resultado
        print(f"Resultado para '{seller_name}': ")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        # Mostrar versión formateada
        print("\nInformación de contacto formateada:")
        print("-" * 50)
        print(agente.get_formatted_contacts(seller_name))
        print("-" * 50)
