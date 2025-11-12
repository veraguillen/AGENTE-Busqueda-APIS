"""
Agente para filtrado de vendedores por marcas conocidas.
Este agente se encarga de filtrar vendedores que son marcas famosas.
"""
import logging
from typing import Dict, List, Any, Optional
from app.config_manager import ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class AgenteFiltro:
    """Agente especializado en filtrar vendedores que son marcas famosas."""
    
    def __init__(self, config: ConfigManager, cache=None, monitor=None, **kwargs):
        """
        Inicializa el agente con la configuración proporcionada.
        
        Args:
            config: Instancia de ConfigManager para acceder a la configuración
            cache: Instancia de caché (opcional)
            monitor: Objeto para monitoreo y métricas (opcional)
            **kwargs: Argumentos adicionales
        """
        self.config = config
        self.cache = cache
        self.monitor = monitor
        
        # Obtener la lista de marcas excluidas de la configuración
        self.excluded_brands = self.config.get('filters.excluded_brands', [])
        logger.info(f"AgenteFiltro inicializado con {len(self.excluded_brands)} marcas excluidas.")
    
    def filter_listings(self, listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtra los listados por vendedor para excluir marcas conocidas.
        
        Args:
            listings: Lista de productos de MercadoLibre
            
        Returns:
            Lista filtrada de productos
        """
        filtered_listings = []
        logger.info(f"Filtrando {len(listings)} listados, excluyendo vendedores que sean marcas conocidas.")
        
        # Obtener configuración de filtrado
        min_seller_reputation = self.config.get('filters.min_seller_reputation', 0)
        max_price = self.config.get('filters.max_price', float('inf'))
        min_price = self.config.get('filters.min_price', 0)
        allowed_conditions = self.config.get('filters.allowed_conditions', ["new", "used", "not_specified"])
        
        for item in listings:
            # Filtrar por precio
            price = item.get("price", 0)
            if price < min_price or price > max_price:
                continue
                
            # Filtrar por condición
            condition = item.get("condition", "not_specified")
            if condition not in allowed_conditions:
                continue
                
            seller = item.get("seller", {})
            seller_nickname_raw = seller.get("nickname", "")
            
            # Intentar obtener el nickname del eshop si no está en el seller
            if not seller_nickname_raw and seller.get("eshop"):
                seller_nickname_raw = seller.get("eshop", {}).get("nick_name", "")
                
            seller_nickname_lower = seller_nickname_raw.lower()
            
            # Verificar si el vendedor es una marca conocida
            if seller_nickname_lower and any(brand in seller_nickname_lower for brand in self.excluded_brands):
                logger.debug(f"Excluyendo vendedor '{seller_nickname_raw}' por coincidir con marca conocida")
                continue  # Saltar este listado porque es una marca conocida
                
            # Si el vendedor es nulo o vacío, dejarlo pasar pero registrarlo
            if not seller_nickname_lower:
                logger.debug(f"Producto con vendedor vacío: ID={item.get('id', 'unknown')}, Title={item.get('title', 'unknown')}")
                # NO excluimos productos con vendedor vacío, los dejamos pasar
            
            # Si pasa el filtro, incluirlo en la lista de resultados
            filtered_listings.append(item)
        
        logger.info(f"Filtrado completado. Quedan {len(filtered_listings)} de {len(listings)} productos.")
        return filtered_listings
        
    def update_excluded_brands(self, brands: List[str]) -> None:
        """
        Actualiza la lista de marcas excluidas.
        
        Args:
            brands: Nueva lista de marcas a excluir
        """
        self.excluded_brands = brands
        logger.info(f"Lista de marcas excluidas actualizada a: {self.excluded_brands}")
        
        # Opcional: Actualizar la configuración en tiempo de ejecución
        if hasattr(self.config, 'update'):
            self.config.update('filters.excluded_brands', brands)
