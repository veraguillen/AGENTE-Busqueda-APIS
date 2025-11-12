"""
Agente para búsqueda en MercadoLibre.
Este agente se encarga de buscar productos en MercadoLibre con paginación completa.
"""
import requests
import logging
import time
import json
from typing import Dict, List, Any, Optional

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

# Constantes
# Configuración de RapidAPI - Múltiples hosts a probar
RAPIDAPI_HOSTS = [
    "mercado-libre7.p.rapidapi.com",
    "mercadolibre1.p.rapidapi.com",
    "mercadolibre.p.rapidapi.com"
]
REQUEST_TIMEOUT = 15  # segundos

class AgenteML:
    """Agente especializado en búsquedas en MercadoLibre."""
    
    def __init__(self, rapidapi_key: str):
        """
        Inicializa el agente con la clave de RapidAPI.
        
        Args:
            rapidapi_key: Clave de API para RapidAPI
        """
        self.rapidapi_key = rapidapi_key
        self.current_host = RAPIDAPI_HOSTS[0]  # Empezar con el primer host
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": self.current_host
        }
    
    def search(self, query: str, country: str, max_pages: int = 30, sort: str = "relevance") -> List[Dict[str, Any]]:
        """
        Busca productos en MercadoLibre probando múltiples endpoints y configuraciones.
        
        Args:
            query: Texto de búsqueda
            country: Código de país en minúsculas (ej: ar, mx, br)
            max_pages: Número máximo de páginas a consultar
            sort: Criterio de ordenamiento (relevance, price_asc, price_desc)
            
        Returns:
            Lista de productos encontrados
        """
        # Inicializar variables
        all_results = []
        total_pages_processed = 0
        consecutive_empty_pages = 0
        
        # Log información inicial
        logger.info(f"Buscando en Mercado Libre: query='{query}', country='{country}', páginas máximas={max_pages}")
        
        # Lista de endpoints a probar (basados en distintas versiones de la API)
        endpoints = [
            "/api/search",
            "/search", 
            "/items/search",
            "/products/search",
            "/sites/MLA/search"
        ]
        
        # Para cada host en la lista de hosts disponibles
        for endpoint_index, endpoint in enumerate(endpoints):
            # Resetear contador de páginas vacías para cada endpoint
            consecutive_empty_pages = 0
            
            # Probar cada host disponible
            for host_index, host in enumerate(RAPIDAPI_HOSTS):
                # Actualizar headers con el host actual
                self.headers = {
                    "X-RapidAPI-Key": self.rapidapi_key,
                    "X-RapidAPI-Host": host
                }
                
                # URL completa con el endpoint actual
                url = f"https://{host}{endpoint}"
                logger.info(f"Probando endpoint #{endpoint_index+1}: {url}")
                
                # Diferentes parámetros para diferentes formatos de API
                param_options = [
                    {'q': query, 'site_id': country.upper(), 'limit': '50', 'offset': '0'},
                    {'query': query, 'country': country.lower(), 'page': '1'},
                    {'search_str': query, 'country': country.lower(), 'page_num': '1'},
                    {'keyword': query, 'site': country.lower(), 'page': '1'}
                ]
                
                # Probar cada formato de parámetros
                for param_index, params in enumerate(param_options):
                    logger.info(f"Probando formato de parámetros #{param_index+1}: {params}")
                    
                    # Iterar por páginas
                    for page in range(max_pages):
                        # Salir después de 3 páginas vacías consecutivas
                        if consecutive_empty_pages >= 3:
                            logger.info("3 páginas vacías consecutivas. Pasando al siguiente formato.")
                            break
                        
                        # Las páginas empiezan en 1 o 0 según el formato
                        if 'page' in params:
                            params['page'] = str(page + 1)
                        elif 'page_num' in params:
                            params['page_num'] = str(page + 1)
                        elif 'offset' in params:
                            params['offset'] = str(page * 50)  # Asumiendo 50 resultados por página
                            
                        current_page = page + 1
                        logger.info(f"Procesando página {current_page} con {url}")
                        
                        try:
                            # Añadir delay entre páginas para evitar limitaciones de la API
                            if page > 0:
                                time.sleep(0.5)
                            
                            # Log detallado para diagnóstico
                            logger.info(f"Enviando solicitud a: {url} con params: {params}")
                            logger.info(f"Headers: X-RapidAPI-Key=****** X-RapidAPI-Host={host}")
                            
                            # Realizar solicitud HTTP
                            response = requests.get(url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT)
                            
                            # Log de la respuesta para diagnóstico
                            logger.info(f"Respuesta: Status={response.status_code}, Content-Type={response.headers.get('Content-Type')}")
                            
                            if response.status_code != 200:
                                logger.error(f"Error en respuesta: {response.text[:500]}")
                                consecutive_empty_pages += 1
                                continue
                            
                            # Obtener respuesta como JSON
                            response.raise_for_status()
                            
                            # Log de la estructura de respuesta para diagnóstico
                            data = response.json()
                            logger.info(f"Estructura de respuesta: {type(data).__name__}")
                            logger.info(f"Contenido de muestra: {str(response.text)[:200]}...")
                            
                            # Verificar si la respuesta es un string (lo que causaría el error)
                            if isinstance(data, str):
                                logger.warning(f"La respuesta de la API es un string, no un diccionario o lista: {data}")
                                try:
                                    # Intentar convertir el string a JSON si es posible
                                    import json
                                    data = json.loads(data)
                                    logger.info(f"Convertido string a {type(data).__name__}: {data}")
                                except:
                                    logger.error("No se pudo convertir el string a JSON")
                                    # Si no se puede convertir, tratarlo como un resultado vacío
                                    data = []
                            
                            # Extraer resultados
                            results = []
                            
                            # Intentar varios formatos posibles de la API
                            if isinstance(data, dict):
                                if 'results' in data:
                                    results = data['results']
                                elif 'data' in data:
                                    results = data['data']
                                elif 'items' in data:
                                    results = data['items']
                                elif 'products' in data:
                                    results = data['products']
                                elif 'paging' in data and 'results' in data:
                                    results = data['results']
                                # Si no tenemos resultados pero tenemos paginación, puede ser otro formato
                                elif 'paging' in data:
                                    # Buscar en cualquier campo que contenga una lista
                                    for key, value in data.items():
                                        if isinstance(value, list) and len(value) > 0:
                                            results = value
                                            break
                            elif isinstance(data, list):
                                results = data
                            
                            # Normalizar resultados si son objetos simplificados
                            normalized_results = []
                            for item in results:
                                # Si es un diccionario, mantenerlo
                                if isinstance(item, dict):
                                    # Verificar si el producto tiene los campos mínimos
                                    if not any(key in item for key in ['id', 'title', 'price', 'permalink']):
                                        # Intentar mapear campos comunes de otras APIs
                                        normalized_item = {}
                                        
                                        # Mapeo de campos comunes con diferentes nombres
                                        field_mappings = {
                                            'id': ['id', 'item_id', 'product_id', 'itemId', 'ID', 'productId'],
                                            'title': ['title', 'name', 'description', 'item_title', 'product_name', 'product_title', 'Name'],
                                            'price': ['price', 'item_price', 'product_price', 'pricing', 'Price', 'CurrentPrice', 'current_price', 'strikethrough_price'],
                                            'url': ['url', 'permalink', 'link', 'item_url', 'product_url', 'URL', 'Link', 'share_url'],
                                            'thumbnail': ['thumbnail', 'image', 'image_url', 'item_image', 'pictures', 'Image', 'main_image', 'main_picture'],
                                            'condition': ['condition', 'item_condition', 'product_condition', 'Condition', 'state'],
                                            'currency': ['currency', 'currency_id', 'Currency', 'price_currency'],
                                            'location': ['location', 'seller_location', 'item_location', 'Location'],
                                            'rating': ['rating', 'stars', 'review_rating', 'average_rating'],
                                            'votes': ['votes', 'review_count', 'reviews', 'ratings_count', 'rating_count'],
                                            'seller': ['seller', 'vendor', 'store', 'merchant', 'seller_info']
                                        }
                                        
                                        # Aplicar mapeo de campos
                                        for target_field, possible_fields in field_mappings.items():
                                            for field in possible_fields:
                                                if field in item:
                                                    normalized_item[target_field] = item[field]
                                                    break
                                                    
                                        # Si encontramos al menos título y precio, lo consideramos válido
                                        if 'title' in normalized_item and 'price' in normalized_item:
                                            normalized_results.append(normalized_item)
                                        else:
                                            # Guardar el item original
                                            normalized_results.append(item)
                                    else:
                                        # El item ya tiene los campos necesarios
                                        normalized_results.append(item)
                                elif isinstance(item, str) and item.startswith('{') and item.endswith('}'):
                                    # Intentar parsear si es un string JSON
                                    try:
                                        json_item = json.loads(item)
                                        if isinstance(json_item, dict):
                                            normalized_results.append(json_item)
                                    except:
                                        # Si falla, ignorar
                                        pass
                                
                            # Actualizar la lista de resultados con los normalizados
                            if normalized_results:
                                results = normalized_results
                                logger.info(f"Resultados normalizados: {len(results)} elementos")
                                # Mostrar muestra del primer resultado
                                if results:
                                    logger.info(f"Muestra del primer resultado normalizado: {results[0]}")

                            # Verificar si hay resultados
                            if not results:
                                logger.warning("No se encontraron resultados en esta página")
                                consecutive_empty_pages += 1
                                continue
                            
                            # Procesar resultados
                            logger.info(f"Se encontraron {len(results)} resultados")
                            all_results.extend(results)
                            total_pages_processed += 1
                            consecutive_empty_pages = 0  # Resetear contador de páginas vacías
                            
                            # Si encontramos resultados, terminar la búsqueda de endpoints
                            # y seguir con este que funciona
                            if all_results:
                                # Salir de los bucles de parámetros, hosts y endpoints
                                break
                        
                        except requests.RequestException as e:
                            logger.error(f"Error en solicitud HTTP: {e}")
                            consecutive_empty_pages += 1
                            continue
                        
                        except Exception as e:
                            logger.error(f"Error inesperado: {e}")
                            consecutive_empty_pages += 1
                            continue
                    
                    # Si encontramos resultados con este formato de parámetros, no probar más
                    if all_results:
                        break
                
                # Si encontramos resultados con este host, no probar más hosts
                if all_results:
                    break
            
            # Si encontramos resultados con este endpoint, no probar más endpoints
            if all_results:
                break
        
        # Resumen final
        logger.info(f"Búsqueda completada. Total de productos encontrados: {len(all_results)}")
        # Guardar los resultados en un archivo para diagnóstico si es necesario
        try:
            with open('ml_search_results.json', 'w', encoding='utf-8') as f:
                json.dump(all_results[:10], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"No se pudieron guardar los resultados para diagnóstico: {e}")
            
        return all_results

    def extract_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae información relevante de un producto de Mercado Libre.
        
        Args:
            product: Diccionario con los datos del producto
        
        Returns:
            Diccionario con la información relevante del producto
        """
        try:
            # Verificar si product es un diccionario
            if not isinstance(product, dict):
                logger.error(f"El producto no es un diccionario, es {type(product).__name__}: {str(product)[:100]}")
                return {
                    "id": "",
                    "title": "Formato de producto no válido",
                    "price": 0,
                    "url": ""
                }
            
            # Función auxiliar para obtener un valor con manejo de tipos
            def safe_get(d, key, default=None):
                return d.get(key, default) if isinstance(d, dict) else default
            
            # Extraer campos básicos según la estructura proporcionada
            result = {
                "id": safe_get(product, "id", ""),
                "title": safe_get(product, "title", ""),
                "price": safe_get(product, "price", 0),
                "strikethrough_price": safe_get(product, "strikethrough_price", ""),
                "currency": safe_get(product, "currency", ""),
                "url": safe_get(product, "url", ""),
                "rating": safe_get(product, "rating", ""),
                "votes": safe_get(product, "votes", ""),
                "seller_info": safe_get(product, "seller", "")
            }
            
            # Procesar URL para obtener información del vendedor
            if result["url"]:
                # Limpiar la URL - eliminar caracteres de escape HTML
                result["url"] = result["url"].replace("&amp;", "&")
                
                # Marcar que esta URL puede usarse para extraer info del vendedor
                result["url_for_seller_extraction"] = True
            
            # Convertir precio a número si es string
            if isinstance(result["price"], str):
                try:
                    # Eliminar caracteres no numéricos excepto punto decimal
                    clean_price = ''.join(c for c in result["price"] if c.isdigit() or c == '.')
                    result["price"] = float(clean_price) if clean_price else 0
                except ValueError:
                    result["price"] = 0
            
            # Convertir rating a float si es string
            if isinstance(result["rating"], str):
                try:
                    result["rating"] = float(result["rating"])
                except ValueError:
                    result["rating"] = 0.0
            
            # Convertir votes a int si es string
            if isinstance(result["votes"], str):
                try:
                    result["votes"] = int(result["votes"])
                except ValueError:
                    result["votes"] = 0
            
            # Preparar estructura para almacenar información del vendedor que se obtendrá posteriormente
            result["seller"] = {
                "id": "",                    # Se llenará después con web scraping
                "nickname": "",              # Se llenará después con web scraping
                "url": "",                   # Se llenará después con web scraping
                "needs_extraction": True,    # Indica que la información del vendedor debe extraerse
                "product_url": result["url"] # URL del producto para extraer datos del vendedor
            }
            
            # Si ya tenemos información del vendedor, extraerla directamente
            if result["seller_info"] and isinstance(result["seller_info"], dict):
                seller_info = result["seller_info"]
                result["seller"] = {
                    "id": safe_get(seller_info, "id", ""),
                    "nickname": safe_get(seller_info, "nickname", ""),
                    "url": safe_get(seller_info, "url", ""),
                    "needs_extraction": False if safe_get(seller_info, "id", "") else True,
                    "product_url": result["url"]
                }
                
                # Si no tenemos URL del vendedor pero tenemos ID, construirla
                if result["seller"]["id"] and not result["seller"]["url"]:
                    result["seller"]["url"] = f"https://www.mercadolibre.com.ar/perfil/{result['seller']['id']}"
                    
            # Eliminar campo seller_info ya que ahora está en seller
            if "seller_info" in result:
                del result["seller_info"]
            
            return result
        
        except Exception as e:
            logger.error(f"Error al extraer información del producto: {e}")
            # Devolver un objeto vacío si hay error
            return {
                "id": "",
                "title": f"Error al procesar producto: {str(e)[:100]}",
                "price": 0,
                "url": "",
                "seller": {
                    "id": "",
                    "nickname": "",
                    "url": "",
                    "needs_extraction": False,
                    "product_url": ""
                }
            }
