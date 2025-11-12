"""
Orquestador para coordinar los agentes de búsqueda.
Este componente coordina el flujo de trabajo entre los diferentes agentes especializados.
"""
import logging
import time
from typing import Dict, List, Any, Optional, Union
import json

# Importar los agentes
from agents import AgenteML, AgenteFiltro, AgenteGoogle, AgenteRanking
from agents.common import get_secrets
from agents.agente_contacts import AgenteContacts  # Nuevo agente unificado

# Importar nuevos módulos de mejoras
from services.cache_manager import CacheManager, cache_result
from services.config_manager import ConfigManager
from app.utils.monitoring import Monitor, measure_execution_time

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

class Orquestador:
    """Orquestador principal que coordina el flujo de trabajo entre agentes."""
    
    def __init__(self):
        """Inicializa el orquestador y carga las credenciales."""
        try:
            # Inicializar sistemas centrales
            self.config = ConfigManager()
            self.cache = CacheManager()
            self.monitor = Monitor(app_name="AgenteBusqueda")
            
            # Cargar los secretos
            self.secrets = get_secrets()
            
            # Inicializar los agentes con las mejoras
            self.agente_ml = AgenteML(
                rapidapi_key=self.secrets["RAPIDAPI-KEY"],
                # Inyectar dependencias para mejoras
                cache=self.cache,
                config=self.config,
                monitor=self.monitor
            )
            
            self.agente_filtro = AgenteFiltro(
                excluded_brands=self.config.get("excluded_brands"),
                monitor=self.monitor
            )
            
            # Inicializar el agente Google tradicional para compatibilidad
            self.agente_google = AgenteGoogle(
                google_api_key=self.secrets["GOOGLE-API-KEY"],
                google_cse_id=self.secrets["GOOGLE-CSE-ID"],
                cache=self.cache,
                config=self.config,
                monitor=self.monitor
            )
            
            # Nuevo agente unificado para información de contacto
            self.agente_contacts = AgenteContacts(
                google_api_key=self.secrets["GOOGLE-API-KEY"],
                google_cse_id=self.secrets["GOOGLE-CSE-ID"],
                rapidapi_key=self.secrets.get("RAPIDAPI-KEY"),
                cache=self.cache,
                config=self.config,
                monitor=self.monitor
            )
            
            self.agente_ranking = AgenteRanking(
                monitor=self.monitor
            )
            
            logger.info("Orquestador inicializado correctamente con todos los agentes y mejoras.")
            self.monitor.log_event("orquestador_initialized", {"status": "success"})
        except Exception as e:
            logger.error(f"Error al inicializar el orquestador: {e}", exc_info=True)
            self.monitor.track_exception(e, {"context": "orquestador_init"})
            raise
    
    @measure_execution_time(monitor_attr='monitor')
    def buscar_productos(self, query: str, country_code: str = "AR",
                        max_listings: int = 50) -> Dict[str, Any]:
        """
        Realiza una búsqueda completa utilizando todos los agentes coordinados.
        
        Args:
            query: Término de búsqueda para MercadoLibre
            country_code: Código de país para MercadoLibre (por defecto AR)
            max_listings: Número máximo de listados para procesar
            
        Returns:
            Dict con resultados procesados
        """
        try:
            # Generar una clave única para caché
            cache_key = f"search:{query}:{country_code}:{max_listings}"
            
            # Intentar recuperar de caché
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"Usando resultados en caché para query: '{query}'")
                return cached_result
            
            search_trace = self.monitor.begin_trace("search_execution", {"query": query})
            
            # Paso 1: Buscar en MercadoLibre usando el agente ML
            ml_trace = self.monitor.begin_trace("busqueda_ml", {"query": query})
            listings = self.agente_ml.search_products(
                query=query,
                country_code=country_code,
                max_results=max_listings
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
            filtered_listings = self.agente_filtro.filter_products(listings)
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
            top_ranked_products = self.agente_ranking.rank_products(filtered_listings)
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
