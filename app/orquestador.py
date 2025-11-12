"""
Módulo que implementa el orquestador principal siguiendo el patrón Fachada de Servicio.
Coordina el flujo de búsqueda de productos, filtrado, ranking y enriquecimiento con contactos.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importar agentes
from agents.agente_ml import AgenteML
from agents.agente_filtro import AgenteFiltro
from agents.agente_ranking import AgenteRanking
# Usar agente_contacts.py en lugar de agente_contacts_v2.py
from agents.agente_contacts import AgenteContacts

# Servicios
from services.cache_manager import CacheManager
from app.config_manager import ConfigManager, get_config, init_config
from app.utils.monitoring import Monitor, measure_execution_time
from utils.api_client import APIClient

# Inicializar configuración
CONFIG_FILE = os.path.join(Path(__file__).parent.parent, 'config.json')
init_config(CONFIG_FILE)
config = get_config()

# Configuración de logging
logging.basicConfig(
    level=config.get('logging.level', 'INFO'),
    format=config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger = logging.getLogger(__name__)

class Orquestador:
    """
    Fachada de servicio que coordina el flujo de búsqueda de productos.
    
    Responsabilidades:
    - Inicializar y gestionar los agentes necesarios
    - Orquestar el flujo de búsqueda, filtrado y enriquecimiento
    - Manejar errores y métricas
    """
    
    def __init__(self, secrets: Dict[str, str] = None, cache: CacheManager = None, 
                 custom_config: ConfigManager = None, monitor: Monitor = None):
        """
        Inicializa el orquestador con sus dependencias.
        
        Args:
            secrets: Diccionario con secretos (API keys, etc.)
            cache: Manejador de caché (opcional)
            custom_config: Manejador de configuración personalizado (opcional)
            monitor: Sistema de monitoreo (opcional)
        """
        # Usar configuración global por defecto o la personalizada
        self.config = custom_config or get_config()
        
        # Inicializar caché si no se proporciona
        if cache is None:
            from services.cache_manager import CacheManager
            # Obtener la URL de Redis desde la configuración o variable de entorno
            redis_url = self.config.get('redis.url') or os.getenv('REDIS_URL')
            self.cache = CacheManager(redis_url=redis_url)
        else:
            self.cache = cache
            
        # Inicializar monitor si no se proporciona
        if monitor is None and self.config.get('monitoring.enabled', True):
            from app.utils.monitoring import Monitor
            self.monitor = Monitor(app_name=self.config.get('app.name', 'AgenteBusqueda'))
        else:
            # Usar el monitor proporcionado o un monitor nulo si está deshabilitado
            self.monitor = monitor or Monitor(app_name='AgenteBusqueda_Disabled')
            
        # Cargar secretos desde el parámetro o desde la configuración
        self.secrets = secrets or {}
        
        # Cargar secretos requeridos desde variables de entorno si no se proporcionaron
        required_secrets = self.config.get('secrets.required_secrets', [])
        for secret in required_secrets:
            if secret not in self.secrets:
                env_value = os.getenv(secret.replace('-', '_'))  # Convertir RAPIDAPI-KEY a RAPIDAPI_KEY
                if env_value:
                    self.secrets[secret] = env_value
        
        # Verificar que todos los secretos requeridos estén presentes
        missing_secrets = [s for s in required_secrets if s not in self.secrets]
        if missing_secrets:
            logger.warning(f"Faltan secretos requeridos: {', '.join(missing_secrets)}")
        
        # Inicializar agentes
        self._inicializar_agentes()
        
        logger.info("Orquestador inicializado correctamente")
        self.monitor.log_event("orquestador_initialized", {"status": "success"})
    
    def _inicializar_agentes(self) -> None:
        """Inicializa todos los agentes necesarios."""
        try:
            logger.info("Inicializando agentes...")
            
            # Configuración común
            api_timeout = self.config.get('api.timeout', 30)
            max_retries = self.config.get('api.max_retries', 3)
            
            # Inicializar el APIClient centralizado con configuración
            api_client = APIClient(
                default_timeout=api_timeout,
                max_retries=max_retries
            )
            
            # Configurar el retry delay (si es necesario) a través de tenacity
            # Nota: La configuración de retry_delay se maneja internamente en APIClient
            # con valores por defecto razonables
            
            # Configurar headers comunes para todas las peticiones
            headers = {
                'User-Agent': self.config.get('api.user_agent'),
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Añadir API key de RapidAPI si está disponible
            if 'RAPIDAPI-KEY' in self.secrets:
                headers['X-RapidAPI-Key'] = self.secrets["RAPIDAPI-KEY"]
                
            api_client.session.headers.update(headers)
            
            # Inicializar AgenteML
            self.agente_ml = AgenteML(
                rapidapi_key=self.secrets.get("RAPIDAPI-KEY"),
                api_client=api_client,
                config=self.config,
                cache=self.cache,
                monitor=self.monitor
            )
            logger.info("AgenteML inicializado")
            
            # Inicializar AgenteFiltro
            self.agente_filtro = AgenteFiltro(
                cache=self.cache,
                config=self.config,
                monitor=self.monitor
            )
            logger.info("AgenteFiltro inicializado")
            
            # Inicializar AgenteContacts
            self.agente_contacts = AgenteContacts(
                google_api_key=self.secrets.get("GOOGLE-API-KEY"),
                google_cse_id=self.secrets.get("GOOGLE-CSE-ID"),
                rapidapi_key=self.secrets.get("RAPIDAPI-KEY"),
                cache=self.cache,
                config=self.config,
                monitor=self.monitor,
                api_client=api_client  # Compartir la misma instancia de APIClient
            )
            logger.info("AgenteContacts inicializado")
            
            # Inicializar AgenteRanking
            self.agente_ranking = AgenteRanking(
                cache=self.cache,
                config=self.config,
                monitor=self.monitor
            )
            logger.info("AgenteRanking inicializado")
            
            logger.info("Todos los agentes han sido inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error al inicializar los agentes: {str(e)}", exc_info=True)
            raise
    
    @measure_execution_time(monitor_attr='monitor')
    def execute_top_seller_search(self, query: str, country_code: str = "AR") -> List[Dict[str, Any]]:
        """
        Ejecuta una búsqueda completa de productos, filtrando y enriqueciendo los resultados.
        
        Args:
            query: Término de búsqueda
            country_code: Código de país (por defecto: AR)
            
        Returns:
            Lista de productos procesados y enriquecidos
            
        Raises:
            ValueError: Si la consulta está vacía o el código de país no es válido
        """
        # Validaciones
        if not query or not query.strip():
            raise ValueError("La consulta de búsqueda no puede estar vacía")
            
        query = query.strip()
        country_code = country_code.upper()
        
        try:
            self.monitor.log_event("search_started", {"query": query, "country": country_code})
            
            # 1. Búsqueda en MercadoLibre
            # Usar directamente el código de país (ej: 'AR')
            productos, total = self.agente_ml.search(query=query, country=country_code)
            
            if not productos:
                self.monitor.log_event("no_products_found", {"query": query})
                return []
            
            # 1.5. Filtrar productos con vendedor vacío
            productos_filtrados = []
            productos_con_vendedor_vacio = 0
            
            for producto in productos:
                seller = producto.get('seller', {})
                seller_name = seller.get('nickname', '') if isinstance(seller, dict) else str(seller)
                
                # Verificar si el nombre del vendedor está vacío o solo contiene espacios
                if not seller_name or not seller_name.strip():
                    productos_con_vendedor_vacio += 1
                    continue
                    
                productos_filtrados.append(producto)
            
            if productos_con_vendedor_vacio > 0:
                logger.info(f"Se filtraron {productos_con_vendedor_vacio} productos con vendedor vacío")
                self.monitor.log_metric("products_with_empty_seller", productos_con_vendedor_vacio)
            
            # 2. Filtrar productos adicionales (precio, condición, etc.)
            if productos_filtrados:  # Solo filtrar si hay productos después de quitar vendedores vacíos
                productos_filtrados = self.agente_filtro.filter_listings(productos_filtrados)
            
            # 3. Enriquecer con información de contacto
            productos_enriquecidos = []
            for producto in productos_filtrados:
                try:
                    contacto = self.agente_contacts.obtener_contacto_vendedor(
                        producto.get('seller', {}).get('id')
                    )
                    producto['contacto'] = contacto
                    productos_enriquecidos.append(producto)
                except Exception as e:
                    logger.warning(f"Error al obtener contacto para producto {producto.get('id')}: {e}")
                    producto['contacto'] = None
                    productos_enriquecidos.append(producto)
            
            # 4. Ordenar resultados
            productos_ordenados = self.agente_ranking.rank_products(productos_enriquecidos)
            
            self.monitor.log_event("search_completed", {
                "query": query,
                "total_results": len(productos_ordenados)
            })
            
            return productos_ordenados
            
        except Exception as e:
            self.monitor.track_exception(e, {
                "context": "execute_top_seller_search",
                "query": query,
                "country": country_code
            })
            raise
            
            # Intentar recuperar de caché
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Usando resultados en caché para query: '{query}'")
                return cached_result
            
            search_trace = self.monitor.begin_trace("search_execution", {"query": query})
            
            # Paso 1: Buscar en MercadoLibre usando el agente ML
            ml_trace = self.monitor.begin_trace("busqueda_ml", {"query": query})
            listings = self.agente_ml.search(
                query=query,
                country=country_code.lower(),  # El método espera el código en minúsculas
                max_pages=100  # Buscar en todas las 100 páginas disponibles
            )
            self.monitor.end_trace(ml_trace)
            
            if not listings:
                logger.info(f"No se encontraron productos para query: '{query}'")
                result = {
                    "status": "success", 
                    "message": "No se encontraron productos.", 
                    "top_products": []
                }
                self.cache.set(cache_key, result, self.config.get("cache_ttl_search"))
                self.monitor.end_trace(search_trace)
                return result
            
            # Paso 2: Filtrar resultados usando el agente de filtro
            filter_trace = self.monitor.begin_trace("filtrado_productos", {"count": len(listings)})
            filtered_listings = self.agente_filtro.filter_listings(listings)
            self.monitor.end_trace(filter_trace)
            
            if not filtered_listings:
                logger.info(f"No quedaron productos después de filtrar para query: '{query}'")
                result = {
                    "status": "success", 
                    "message": "No se encontraron productos que cumplan los criterios de filtrado.", 
                    "top_products": []
                }
                self.cache.set(cache_key, result, self.config.get("cache_ttl_search"))
                self.monitor.end_trace(search_trace)
                return result
            
            # Paso 3: Rankear productos
            ranking_trace = self.monitor.begin_trace("ranking_productos", {"count": len(filtered_listings)})
            # Asegurar que haya suficientes productos para rankear
            if len(filtered_listings) > 0:
                # Aumentamos el límite para mostrar más productos en los resultados
                top_ranked_products = self.agente_ranking.rank_products(
                    filtered_listings, 
                    limit=min(20, len(filtered_listings))  # Mostrar hasta 20 productos (antes era 5 por defecto)
                )
            else:
                top_ranked_products = []
            self.monitor.end_trace(ranking_trace)
            
            if not top_ranked_products:
                logger.info(f"No quedaron productos después de rankear para query: '{query}'")
                return {
                    "status": "success", 
                    "message": "No se encontraron productos para el ranking.", 
                    "top_products": []
                }
            
            # Paso 4: Buscar información de contacto y generar enlaces de WhatsApp
            results_to_return = []
            for rank_idx, product in enumerate(top_ranked_products):
                seller_contact_info = {}
                
                # Extraer el nombre del vendedor según la estructura recibida
                seller_nickname = None
                
                if isinstance(product.get("seller"), dict) and product["seller"].get("nickname"):
                    # Estructura estándar: {"seller": {"nickname": "..."}}  
                    seller_nickname = product["seller"]["nickname"]
                elif isinstance(product.get("seller"), str):
                    # Estructura alternativa: {"seller": "Por NOMBRE_VENDEDOR"}
                    seller_text = product["seller"]
                    # Quitar prefijo "Por " si existe
                    if seller_text.startswith("Por "):
                        seller_nickname = seller_text[4:].strip()
                    else:
                        seller_nickname = seller_text.strip()
                
                # Si tenemos un nombre de vendedor, buscar sus datos de contacto
                if seller_nickname:
                    logger.info(f"Buscando información de contacto para el vendedor: {seller_nickname}")
                    
                    contact_trace = self.monitor.begin_trace("busqueda_contacto", {"seller": seller_nickname})
                    try:
                        # Buscar contacto usando el nuevo agente unificado
                        contact_result = self.agente_contacts.get_contact_info(
                            seller_name=seller_nickname,
                            search_strategy="all",  # Buscar en todas las fuentes disponibles
                            format_results=True
                        )
                        
                        # Extraer información de contacto del resultado
                        if contact_result.get("status") == "ok":
                            # Guardar la tarjeta de contacto formateada
                            if "formatted_cards" in contact_result:
                                product["formatted_contact_cards"] = contact_result["formatted_cards"]
                            
                            # Obtener el primer resultado para compatibilidad con código existente
                            if contact_result.get("data") and len(contact_result["data"]) > 0:
                                first_contact = contact_result["data"][0]
                                seller_contact_info = {
                                    "phone": first_contact.get("phone_number"),
                                    "address": first_contact.get("full_address"),
                                    "website": first_contact.get("website"),
                                    "email": first_contact.get("email"),
                                    "place_link": first_contact.get("place_link")
                                }
                            else:
                                seller_contact_info = {}
                        else:
                            seller_contact_info = {}
                            
                        logger.debug(f"Información de contacto encontrada: {json.dumps(seller_contact_info, indent=2)}")
                    except Exception as e:
                        logger.error(f"Error al buscar información de contacto: {str(e)}")
                        seller_contact_info = {}
                    finally:
                        self.monitor.end_trace(contact_trace)
                else:
                    logger.info("No hay información de vendedor para buscar contacto")
                    seller_contact_info = {}
                
                # Registrar éxito/fracaso de búsqueda de contacto
                self.monitor.log_event("contacto_encontrado", {
                    "seller": seller_nickname,
                    "found_contact": bool(seller_contact_info),
                    "rank_position": rank_idx
                })
                
                # Añadir la información de contacto al producto
                product["contact_info"] = seller_contact_info
                
                # Generar enlace de WhatsApp si hay número de teléfono
                if seller_contact_info.get("phone"):
                    phone = seller_contact_info["phone"]
                    # Limpiar número de teléfono para WhatsApp (solo dígitos)
                    clean_phone = ''.join(filter(str.isdigit, phone))
                    if clean_phone:
                        product["whatsapp_link"] = f"https://wa.me/{clean_phone}"
                
                # Añadir el producto a la lista final
                results_to_return.append(product)
            
            # Devolver resultados finales
            result = {
                "status": "success",
                "query": query,
                "top_products": results_to_return
            }
            
            # Guardar en caché para futuras consultas
            self.cache.set(cache_key, result, self.config.get("cache_ttl_search"))
            self.monitor.end_trace(search_trace)
            return result
        
        except Exception as e:
            logger.error(f"Error en la búsqueda completa: {e}", exc_info=True)
            self.monitor.track_exception(e, {"context": "busqueda_completa", "query": query})
            return {
                "status": "error",
                "message": f"Error en la búsqueda: {str(e)}",
                "top_products": []
            }
