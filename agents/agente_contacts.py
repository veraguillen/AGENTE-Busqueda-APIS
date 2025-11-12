
"""
Agente unificado para la obtención de información de contacto.
Implementa el patrón Fachada (Facade) para unificar la búsqueda de contactos
a través de diferentes fuentes (Google Search y Google Maps).
"""

import logging
from typing import Dict, Any, Optional, Union

# Importar agentes especializados
from agents.agente_google import AgenteGoogle  # Versión con APIClient
from agents.agente_gmaps import AgenteGMaps

# Importar APIClient centralizado
from utils.api_client import APIClient

# Configurar logging
logger = logging.getLogger(__name__)

class AgenteContacts:
    """
    Agente unificado para obtener información de contacto de vendedores,
    combinando búsqueda web y datos de ubicaciones físicas.
    
    Implementa el patrón Fachada (Facade) para proporcionar una interfaz
    simplificada sobre los diferentes sistemas de búsqueda de contactos.
    """
    
    def __init__(self, google_api_key: str, google_cse_id: str = None, 
                 rapidapi_key: str = None, cache=None, config=None, monitor=None,
                 api_client: Optional[APIClient] = None):
        """
        Inicializa el agente unificado de contactos.
        
        Args:
            google_api_key: Clave API de Google (obligatorio)
            google_cse_id: ID del motor de búsqueda personalizado (para AgenteGoogle)
            rapidapi_key: Clave para RapidAPI (opcional para AgenteGMaps)
            cache: Sistema de caché compartido (opcional)
            config: Sistema de configuración (opcional)
            monitor: Sistema de monitoreo (opcional)
            api_client: Instancia de APIClient (opcional, se crea una por defecto)
        """
        self.cache = cache
        self.monitor = monitor
        self.config = config
        
        # Usar el APIClient proporcionado o crear uno nuevo
        self.api_client = api_client or APIClient(
            default_timeout=30,
            max_retries=3
        )
        
        # Configurar headers comunes para todas las peticiones
        self.api_client.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Inicializar el agente de búsqueda web si se proporciona CSE ID
        self.agente_web = None
        if google_cse_id:
            self.agente_web = AgenteGoogle(
                google_api_key=google_api_key, 
                google_cse_id=google_cse_id,
                api_client=self.api_client,  # Compartir la misma instancia de APIClient
                cache=cache,
                monitor=monitor
            )
            logger.info("Componente de búsqueda web inicializado con APIClient")
        
        # La clave para AgenteGMaps puede ser la de Google o una específica de RapidAPI
        maps_api_key = rapidapi_key or google_api_key
        
        # Inicializar el agente de ubicaciones físicas
        self.agente_locations = AgenteGMaps(
            google_api_key=maps_api_key,
            cache=cache,
            monitor=monitor
        )
        logger.info("Componente de búsqueda de ubicaciones físicas inicializado")
        
        # Importar formateador de contactos
        try:
            from app.utils.formatters import format_business_contact_cards
            self.formatter = format_business_contact_cards
            self.has_formatter = True
            logger.info("Formateador de contactos disponible")
        except ImportError:
            self.has_formatter = False
            logger.warning("Formateador de contactos no disponible")
        
        logger.info("AgenteContacts inicializado correctamente")
    
    def get_contact_info(self, seller_name: str, search_strategy: str = "all", 
                         format_results: bool = True) -> Dict[str, Any]:
        """
        Obtiene información de contacto completa usando la estrategia especificada.
        
        Args:
            seller_name: Nombre del vendedor a buscar
            search_strategy: Estrategia de búsqueda: "all", "web", "location"
            format_results: Si se deben formatear los resultados
            
        Returns:
            dict: Resultados combinados o formateados según format_results
        """
        results = {
            "status": "error", 
            "message": "No search performed",
            "source": "AgenteContacts",
            "data": {}
        }
        
        trace_id = None
        if self.monitor:
            trace_id = self.monitor.begin_trace(
                "contacto_busqueda", 
                {"seller": seller_name, "strategy": search_strategy}
            )
        
        try:
            # Verificar validez del parámetro de estrategia
            if search_strategy not in ["all", "web", "location"]:
                raise ValueError(f"Estrategia de búsqueda no válida: {search_strategy}")
                
            # Realizar búsqueda según la estrategia
            web_results = {}
            location_results = {}
            
            # Búsqueda web (si está habilitada y la estrategia lo requiere)
            if search_strategy in ["all", "web"] and self.agente_web:
                try:
                    web_results = self.agente_web.search_seller_contacts(seller_name)
                    results["data"]["web"] = web_results
                    results["status"] = "partial_success"
                except Exception as e:
                    logger.error(f"Error en búsqueda web: {str(e)}", exc_info=True)
                    if self.monitor:
                        self.monitor.track_exception(e, {"context": "web_search", "seller": seller_name})
            
            # Búsqueda de ubicaciones (si la estrategia lo requiere)
            if search_strategy in ["all", "location"] and hasattr(self, 'agente_locations'):
                try:
                    location_results = self.agente_locations.search_business(seller_name, use_fallback=True)
                    results["data"]["locations"] = location_results
                    results["status"] = "success" if results["status"] != "partial_success" else "partial_success"
                except Exception as e:
                    logger.error(f"Error en búsqueda de ubicaciones: {str(e)}", exc_info=True)
                    if self.monitor:
                        self.monitor.track_exception(e, {"context": "location_search", "seller": seller_name})
            
            # Si no se encontraron resultados
            if not results["data"]:
                results["message"] = "No se encontraron resultados"
            else:
                results["message"] = "Búsqueda completada"
                
                # Formatear resultados si es necesario y está disponible el formateador
                if format_results and self.has_formatter:
                    try:
                        results["formatted"] = self.formatter(results["data"])
                    except Exception as e:
                        logger.error(f"Error al formatear resultados: {str(e)}", exc_info=True)
                        if self.monitor:
                            self.monitor.track_exception(e, {"context": "format_results", "seller": seller_name})
            
            return results
            
        except Exception as e:
            error_msg = f"Error en get_contact_info: {str(e)}"
            logger.error(error_msg, exc_info=True)
            results["message"] = error_msg
            
            if self.monitor:
                self.monitor.track_exception(e, {
                    "context": "get_contact_info", 
                    "seller": seller_name,
                    "strategy": search_strategy
                })
            
            return results
            
        finally:
            if self.monitor and trace_id:
                self.monitor.end_trace(trace_id, results)
    
    def close(self):
        """
        Cierra los recursos utilizados por el agente.
        """
        if hasattr(self, 'api_client'):
            self.api_client.close()
            
        if hasattr(self, 'agente_web') and hasattr(self.agente_web, 'close'):
            self.agente_web.close()
            
        if hasattr(self, 'agente_locations') and hasattr(self.agente_locations, 'close'):
            self.agente_locations.close()
        
        logger.info("Recursos de AgenteContacts liberados")
