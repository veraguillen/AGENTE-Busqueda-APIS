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
RAPIDAPI_HOST = "mercado-libre7.p.rapidapi.com"
REQUEST_TIMEOUT = 15  # segundos

class AgenteML:
    """Agente especializado en búsquedas en MercadoLibre."""
    
    def __init__(self, rapidapi_key: str, cache=None, config=None, monitor=None):
        """
        Inicializa el agente con la clave de RapidAPI.
        
        Args:
            rapidapi_key: Clave de API para RapidAPI
            cache: Instancia de CacheManager (opcional)
            config: Instancia de ConfigManager (opcional)
            monitor: Instancia de Monitor para métricas (opcional)
        """
        self.rapidapi_key = rapidapi_key
        self.headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": RAPIDAPI_HOST
        }
        self.cache = cache
        self.config = config
        self.monitor = monitor
        
        # Configurar timeout desde config si está disponible
        self.timeout = REQUEST_TIMEOUT
        if config:
            self.timeout = config.get("request_timeout", REQUEST_TIMEOUT)
    
    def search(self, query: str, country: str, max_pages: int = 100, sort: str = "relevance", min_results: int = 1) -> List[Dict[str, Any]]:
        """
        Busca productos en MercadoLibre probando múltiples endpoints y configuraciones.
        
        Args:
            query: Texto de búsqueda
            country: Código de país en minúsculas (ej: ar, mx, br)
            max_pages: Número máximo de páginas a consultar (por defecto 100)
            sort: Criterio de ordenamiento (relevance, price_asc, price_desc)
            min_results: Número mínimo de resultados con vendedor a devolver
            
        Returns:
            Lista de productos encontrados con vendedores reales
        """
        # Inicializar variables para la búsqueda
        all_results = []
        total_pages_processed = 0
        consecutive_empty_pages = 0
        results_with_seller = 0
        current_page = 1
        
        # Configuración de límites
        max_attempts = max_pages  # Número máximo de páginas a consultar
        min_seller_results = min_results  # Mínimo de resultados con vendedor a devolver
        max_consecutive_empty = 5  # Máximo de páginas vacías consecutivas permitidas
        
        logger.info(f"Iniciando búsqueda en MercadoLibre: '{query}' en {country}")
        logger.info(f"Objetivo: mínimo {min_seller_results} resultados con vendedor (máx. {max_attempts} páginas)")
        
        # Endpoint principal de búsqueda
        url = f"https://{RAPIDAPI_HOST}/listings_for_search"
        
        # Bucle principal de paginación
        while current_page <= max_attempts:
            # Verificar condiciones de salida
            if results_with_seller >= min_seller_results:
                logger.info(f"Se encontraron suficientes resultados con vendedor: {results_with_seller}/{min_seller_results}")
                break
                
            if consecutive_empty_pages >= max_consecutive_empty:
                logger.info(f"Se alcanzó el límite de {max_consecutive_empty} páginas vacías consecutivas")
                break
                
            # Mostrar progreso actual
            logger.info(f"Página {current_page}: {results_with_seller} resultados con vendedor (mínimo {min_seller_results} deseados)")
            
            # Configurar parámetros según documentación
            params = {
                'search_str': query,
                'country': country.lower(),
                'sort_by': sort,
                'page_num': current_page
            }
            
            try:
                # Añadir delay entre páginas para evitar limitaciones de la API
                if current_page > 1:
                    time.sleep(0.5)
                
                # Log detallado para diagnóstico
                logger.info(f"Enviando solicitud a: {url} con params: {params}")
                
                # Realizar solicitud HTTP con manejo explícito de errores
                try:
                    response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
                    
                    # Log de la respuesta para diagnóstico
                    logger.info(f"Respuesta: Status={response.status_code}, Content-Type={response.headers.get('Content-Type')}")
                    
                    # Verificar código de estado HTTP
                    if response.status_code != 200:
                        error_message = response.text[:500] if response.text else "No hay detalle de error"
                        logger.error(f"Error en respuesta HTTP {response.status_code}: {error_message}")
                        
                        # Verificar si hay problemas específicos conocidos
                        if "sort_by must be a string" in error_message:
                            logger.error("ERROR CRÍTICO: El parámetro sort_by no se está enviando correctamente")
                            
                        # Guardar el error para diagnóstico
                        with open(f"error_ml_api_{query[:10]}_{current_page}.log", "w") as f:
                            f.write(f"Status: {response.status_code}\n")
                            f.write(f"Headers: {dict(response.headers)}\n")
                            f.write(f"Params: {params}\n")
                            f.write(f"Response: {response.text[:2000]}\n")
                        
                        consecutive_empty_pages += 1
                        current_page += 1
                        continue
                    
                    # Obtener respuesta como JSON
                    data = response.json()
                    
                except requests.RequestException as e:
                    logger.error(f"Error de red al conectar con API: {e}")
                    consecutive_empty_pages += 1
                    current_page += 1
                    continue
                except ValueError as e:
                    logger.error(f"Error al decodificar JSON de respuesta: {e}")
                    logger.error(f"Contenido de respuesta: {response.text[:200]}...")
                    consecutive_empty_pages += 1
                    current_page += 1
                    continue
                
                # Extraer resultados
                results = []
                
                # Intentar varios formatos posibles de la API
                if isinstance(data, list):
                    # La API devuelve directamente una lista de productos
                    results = data
                    logger.info(f"API devolvió lista directa con {len(results)} elementos")
                elif isinstance(data, dict):
                    # Intentar extraer resultados de diferentes claves posibles
                    for key in ["results", "listings", "items", "data", "products"]:
                        if key in data and isinstance(data[key], list):
                            results = data[key]
                            logger.info(f"Encontrados resultados en clave '{key}': {len(results)} elementos")
                            break
                
                # Manejar resultados
                if results:
                    logger.info(f"Encontrados {len(results)} productos en página {current_page}")
                    
                    # Procesar cada resultado para asegurar el formato correcto
                    page_has_sellers = False
                    
                    for item in results:
                        try:
                            # Asegurarse de que el item tenga los campos mínimos requeridos
                            if not isinstance(item, dict):
                                logger.warning(f"Resultado no es un diccionario: {item}")
                                continue
                                
                            # Asegurar que los campos requeridos estén presentes
                            if not item.get("id") or not item.get("title"):
                                logger.warning(f"Faltan campos requeridos en el resultado: {item}")
                                continue
                            
                            # Extraer información del vendedor
                            seller_id = item.get("seller_id")
                            seller_name = None
                            
                            # Buscar información del vendedor en todas las estructuras posibles
                            if isinstance(item.get("seller"), dict):
                                # Formato: {"seller": {"nickname": "..."}}  
                                seller_name = item["seller"].get("nickname")
                                # Si no hay nickname, intentar con otros campos
                                if not seller_name:
                                    seller_name = item["seller"].get("id") or item["seller"].get("name")
                            elif isinstance(item.get("seller"), str):
                                # Formato: {"seller": "Por NOMBRE_VENDEDOR"}
                                seller_name = item["seller"]
                                # Quitar prefijo "Por " si existe
                                if seller_name.startswith("Por "):
                                    seller_name = seller_name[4:].strip()
                            
                            # Si hay un campo store_name, usarlo como fallback
                            if not seller_name and item.get("store_name"):
                                seller_name = item["store_name"]
                                            
                            # Si no hay información del vendedor, intentar extraerla de la URL
                            if not seller_id and not seller_name:
                                listing_url = item.get("url", "") or item.get("permalink", "")
                                if listing_url:
                                    try:
                                        import re
                                        # Extraer ID del vendedor de la URL en varios formatos posibles
                                        patterns = [
                                            r'/MLA-\d+-[^-]+-([^-]+)-',  # MLA-12345-Product-SELLER-
                                            r'seller_id=(\d+)',          # seller_id=12345
                                            r'/_Desde_([^_]+)',           # _Desde_SELLERNAME
                                            r'/seller/(\w+)'             # /seller/SELLERID
                                        ]
                                        
                                        for pattern in patterns:
                                            match = re.search(pattern, listing_url)
                                            if match:
                                                extracted_seller = match.group(1)
                                                seller_id = extracted_seller
                                                seller_name = extracted_seller
                                                logger.debug(f"Seller extraído de la URL: {seller_name}")
                                                break
                                    except Exception as e:
                                        logger.debug(f"Error extrayendo vendedor de la URL: {str(e)}")
                                        
                            # Si aún no hay vendedor pero hay título, asignar un nombre genérico 
                            if not seller_name and item.get("title"):
                                seller_name = f"Vendedor-{item['id']}"
                                logger.debug(f"Asignando nombre genérico al vendedor: {seller_name}")
                                
                            # Actualizar el campo seller en formato estándar
                            if seller_name:
                                item["seller"] = {"nickname": seller_name, "id": seller_id or "unknown"}
                            elif seller_id:
                                item["seller"] = {"nickname": seller_id, "id": seller_id}
                            
                            # Solo procesar si tiene un ID de vendedor
                            if seller_id:
                                # Si no hay nombre de vendedor, usar el ID directamente
                                if not seller_name or seller_name.startswith("Vendedor-"):
                                    seller_name = seller_id
                                
                                # Asegurar que el precio sea un número
                                if "price" in item and isinstance(item["price"], str):
                                    try:
                                        item["price"] = float(item["price"].replace("$", "").replace(".", "").replace(",", "."))
                                    except (ValueError, AttributeError):
                                        item["price"] = 0.0
                                
                                all_results.append(item)
                                results_with_seller += 1
                                page_has_sellers = True
                                
                                # Si ya tenemos suficientes resultados, salir
                                if results_with_seller >= min_seller_results:
                                    break
                                
                        except Exception as e:
                            logger.error(f"Error al procesar resultado: {str(e)}")
                            logger.debug(f"Resultado con error: {json.dumps(item, indent=2, ensure_ascii=False)[:500]}...")
                    
                    # Actualizar contadores de páginas
                    if page_has_sellers:
                        total_pages_processed += 1
                        consecutive_empty_pages = 0
                        logger.info(f"Página {current_page}: {results_with_seller} resultados con vendedor hasta ahora")
                    else:
                        consecutive_empty_pages += 1
                        logger.info(f"Página {current_page} sin vendedores válidos")
                        
                    # Pasar a la siguiente página
                    current_page += 1
                    
                    # Si ya tenemos suficientes resultados, salir
                    if results_with_seller >= min_results:
                        logger.info(f"Se encontraron suficientes resultados con vendedor ({results_with_seller})")
                        break
                        
                    # Si llegamos al final de los resultados, salir
                    if len(results) < 50:
                        logger.info(f"Menos de 50 resultados en la página. Llegamos al final de la paginación.")
                        break
                else:
                    logger.info(f"No se encontraron resultados en página {current_page}")
                    consecutive_empty_pages += 1
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Error en solicitud de página {current_page}: {e}")
                consecutive_empty_pages += 1
                continue
            
            except Exception as e:
                logger.error(f"Error inesperado en página {current_page}: {e}")
                consecutive_empty_pages += 1
                continue
        
        # Log de resultados
        logger.info(f"Búsqueda completa. Procesadas {total_pages_processed} páginas. Total de productos: {len(all_results)}")
        
        # Formatear resultados según lo esperado por el orquestador
        logger.info(f"Formateando {len(all_results)} resultados...")
        formatted_results = []
        
        if not all_results:
            logger.warning("No hay resultados para formatear")
            return []
            
        # Mostrar el primer elemento para depuración
        logger.debug(f"Primer elemento crudo: {json.dumps(all_results[0], indent=2, ensure_ascii=False)[:500]}...")
        
        for item in all_results:
            try:
                # Inicializar seller_info como None por defecto
                seller_info = None
                
                # Extraer información del vendedor de diferentes fuentes
                seller_name = item.get("seller")
                seller_id = item.get("seller_id")
                listing_url = item.get("url", "")
                
                # Si no hay ID de vendedor, intentar extraerlo de la URL
                if not seller_id and listing_url:
                    try:
                        import re
                        # Extraer el ID del vendedor de la URL (ejemplo: /MLA-1234567890-...)
                        match = re.search(r'/MLA-\d+-[^-]+-([^-]+)-', listing_url)
                        if match:
                            seller_id = match.group(1)
                            logger.debug(f"ID de vendedor extraído de la URL: {seller_id}")
                    except Exception as e:
                        logger.debug(f"No se pudo extraer ID de vendedor de la URL: {str(e)}")
                
                # Solo procesar si tenemos un ID de vendedor
                if seller_id:
                    # Si no hay nombre de vendedor, usar el ID directamente sin prefijo
                    if not seller_name or seller_name.startswith("Vendedor-"):
                        seller_name = seller_id
                    
                    # Crear el diccionario del vendedor
                    seller_info = {
                        "id": seller_id,
                        "nickname": str(seller_name).strip(),
                        "reputation": item.get("seller_reputation", {})
                    }
                    logger.debug(f"Vendedor encontrado: {seller_info['nickname']} (ID: {seller_info['id']})")
                else:
                    logger.debug("No se encontró información del vendedor en el ítem")
            
                # Solo agregar el producto si tiene información de vendedor
                if seller_info and seller_info.get("id"):
                    # Crear el objeto de producto formateado
                    product = {
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "price": item.get("price", 0),
                        "currency": item.get("currency", ""),
                        "condition": item.get("condition", ""),
                        "thumbnail": item.get("thumbnail", ""),
                        "listing_url": item.get("url", ""),
                        "seller": seller_info,  # Ya aseguramos que existe
                        "shipping": {
                            "free_shipping": item.get("free_shipping", False)
                        },
                        "address": {
                            "city": item.get("location", "")
                        }
                    }
                    
                    # Añadir campos adicionales si están disponibles
                    if "available_quantity" in item:
                        product["available_quantity"] = item["available_quantity"]
                    if "sold_quantity" in item:
                        product["sold_quantity"] = item["sold_quantity"]
                    
                    formatted_results.append(product)
                    logger.debug(f"Producto agregado: {product['id']} - {product['title'][:50]}...")
                else:
                    logger.debug(f"Producto sin información de vendedor, omitiendo: {item.get('id')}")
                
            except Exception as e:
                logger.error(f"Error al formatear el producto {item.get('id', 'desconocido')}: {str(e)}")
                logger.debug(f"Producto con error: {json.dumps(item, indent=2, ensure_ascii=False)[:500]}...")
        
        return formatted_results

    def extract_product_info(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae la información relevante de un producto.
        
        Args:
            product: Diccionario con la información del producto
            
        Returns:
            Diccionario con la información relevante del producto
        """
        try:
            # Adaptarse a diferentes estructuras posibles
            # Intentar extraer los campos más comunes
            result = {
                "id": product.get("id", ""),
                "title": product.get("title", ""),
                "price": product.get("price", 0),
                "currency": product.get("currency_id", ""),
                "link": product.get("permalink", ""),
                "condition": product.get("condition", ""),
                "thumbnail": product.get("thumbnail", ""),
                "available_quantity": product.get("available_quantity", 0),
                "sold_quantity": product.get("sold_quantity", 0)
            }
            
            # Intentar extraer campos adicionales que pueden estar en diferentes ubicaciones
            if "shipping" in product:
                result["free_shipping"] = product["shipping"].get("free_shipping", False)
            
            if "seller" in product:
                result["seller_id"] = product["seller"].get("id", "")
            
            if "location" in product:
                result["location"] = product["location"].get("city", {}).get("name", "")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extrayendo información del producto: {e}")
            return {
                "id": product.get("id", ""),
                "title": product.get("title", "Error al extraer información"),
                "price": 0,
                "link": ""
            }
