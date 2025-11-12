"""
Módulo que implementa el orquestador principal siguiendo el patrón Fachada de Servicio.
Coordina el flujo de búsqueda de productos, filtrado, ranking y enriquecimiento con contactos.
"""
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importar agentes
from search_agent.clients.mercado_libre import MercadoLibreClient
from search_agent.processing.filtering import FilteringProcessor
from search_agent.processing.ranking import RankingProcessor
from search_agent.core.contacts import ContactManager

# Servicios
from search_agent.services.cache import CacheManager
from search_agent.services.config import ConfigManager, get_config, init_config
from search_agent.utils.monitoring import Monitor, measure_execution_time

# Configurar logging
logger = logging.getLogger(__name__)

class SearchOrchestrator:
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
            from search_agent.services.cache import CacheManager
            # Obtener la URL de Redis desde la configuración o variable de entorno
            redis_url = self.config.get('redis.url') or os.getenv('REDIS_URL')
            self.cache = CacheManager(redis_url=redis_url)
        else:
            self.cache = cache
            
        # Inicializar monitor si no se proporciona
        if monitor is None and self.config.get('monitoring.enabled', True):
            from search_agent.utils.monitoring import Monitor
            self.monitor = Monitor(app_name=self.config.get('app.name', 'SearchAgent'))
        else:
            # Usar el monitor proporcionado o un monitor nulo si está deshabilitado
            self.monitor = monitor or Monitor(app_name='SearchAgent_Disabled')
            
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
        self._initialize_agents()
        
        logger.info("Orquestador inicializado correctamente")
        self.monitor.log_event("orchestrator_initialized", {"status": "success"})
    
    def _initialize_agents(self):
        """Inicializa todos los agentes necesarios."""
        # Inicializar cliente de MercadoLibre
        self.ml_client = MercadoLibreClient(
            api_key=self.secrets.get('RAPIDAPI-KEY'),
            cache=self.cache,
            config=self.config
        )
        
        # Inicializar procesador de filtrado
        self.filter_processor = FilteringProcessor(
            config=self.config
        )
        
        # Inicializar procesador de ranking
        self.ranking_processor = RankingProcessor(
            config=self.config
        )
        
        # Inicializar gestor de contactos
        self.contact_manager = ContactManager(
            api_key=self.secrets.get('RAPIDAPI-KEY'),
            cache=self.cache,
            config=self.config
        )
        
        logger.info("Agentes inicializados correctamente")
    
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
        # Validar parámetros
        if not query or not query.strip():
            raise ValueError("El término de búsqueda no puede estar vacío")
        
        if not country_code or not isinstance(country_code, str) or len(country_code) != 2:
            raise ValueError("El código de país debe ser un código de 2 letras")
        
        logger.info(f"Iniciando búsqueda para: '{query}' en {country_code}")
        self.monitor.log_event("search_started", {"query": query, "country": country_code})
        
        try:
            # 1. Búsqueda en MercadoLibre
            products = self.ml_client.search_products(
                query=query,
                country_code=country_code,
                limit=self.config.get('mercadolibre.api.default_limit', 50)
            )
            
            if not products:
                logger.warning("No se encontraron productos")
                return []
            
            # 2. Filtrar productos
            filtered_products = self.filter_processor.apply_filters(products)
            
            if not filtered_products:
                logger.warning("Ningún producto superó los filtros")
                return []
            
            # 3. Ordenar por ranking
            ranked_products = self.ranking_processor.rank_products(filtered_products)
            
            # 4. Enriquecer con información de contacto
            enriched_products = []
            for product in ranked_products:
                try:
                    seller_id = product.get('seller', {}).get('id')
                    if seller_id:
                        contact_info = self.contact_manager.get_seller_contact(
                            seller_id=seller_id,
                            country_code=country_code
                        )
                        product['seller_contact'] = contact_info
                    
                    enriched_products.append(product)
                except Exception as e:
                    logger.error(f"Error al enriquecer producto {product.get('id')}: {str(e)}")
                    # Añadir el producto sin enriquecer
                    product['seller_contact'] = {}
                    enriched_products.append(product)
            
            logger.info(f"Búsqueda completada. Productos encontrados: {len(products)}, "
                       f"filtrados: {len(filtered_products)}, "
                       f"enriquecidos: {len(enriched_products)}")
            
            self.monitor.log_event("search_completed", {
                "query": query,
                "country": country_code,
                "total_products": len(products),
                "filtered_products": len(filtered_products),
                "enriched_products": len(enriched_products)
            })
            
            return enriched_products
            
        except Exception as e:
            error_msg = f"Error en la búsqueda: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.monitor.log_event("search_error", {
                "query": query,
                "country": country_code,
                "error": str(e)
            })
            raise
