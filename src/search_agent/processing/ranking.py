"""
Agente para rankear y seleccionar los mejores productos.
Este agente se encarga de calcular puntajes y ordenar productos.
"""
import logging
import math
from typing import Dict, List, Any, Optional
from app.config_manager import ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class AgenteRanking:
    """Agente especializado en rankear productos según múltiples criterios."""
    
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
        
        # Obtener pesos de la configuración
        self.weights = self.config.get('ranking.weights', {
            'price': 0.4,      # Precio (inverso: más bajo es mejor)
            'sales': 0.4,      # Cantidad de ventas
            'condition': 0.2   # Condición del producto (nuevo, usado, etc.)
        })
        
        logger.info("AgenteRanking inicializado con pesos: %s", self.weights)
    
    def calculate_score(self, product: Dict[str, Any]) -> float:
        """
        Calcula un puntaje para un producto basado en múltiples criterios.
        
        Args:
            product: Diccionario con la información del producto
            
        Returns:
            Puntaje normalizado entre 0 y 1
        """
        if not product:
            return 0.0
            
        try:
            # Obtener configuraciones
            price_config = self.config.get('ranking.price', {})
            sales_config = self.config.get('ranking.sales', {})
            condition_config = self.config.get('ranking.condition', {})
            seller_config = self.config.get('ranking.seller', {})
            shipping_config = self.config.get('ranking.shipping', {})
            
            # Calcular puntaje de precio (inverso, ya que precios más bajos son mejores)
            price_score = self._calculate_price_score(
                product.get('price'), 
                price_config.get('max_price', 1000000),
                price_config.get('price_floor', 1000),
                price_config.get('price_decay', 100000.0)
            )
            
            # Calcular puntaje de ventas
            sales_score = self._calculate_sales_score(
                product.get('sold_quantity', 0),
                sales_config.get('max_sales', 100),
                sales_config.get('sales_weight', 1.0)
            )
            
            # Calcular puntaje de condición
            condition_score = self._calculate_condition_score(
                product.get('condition', 'not_specified'),
                condition_config
            )
            
            # Calcular puntaje del vendedor
            seller_score = self._calculate_seller_score(
                product.get('seller', {}),
                seller_config
            )
            
            # Calcular puntaje de envío
            shipping_score = self._calculate_shipping_score(
                product.get('shipping', {}),
                shipping_config
            )
            
            # Calcular puntaje final ponderado
            final_score = (
                price_score * self.weights.get('price', 0.4) +
                sales_score * self.weights.get('sales', 0.4) +
                condition_score * self.weights.get('condition', 0.2)
            ) * seller_score * shipping_score
            
            return min(max(final_score, 0.0), 1.0)  # Asegurar que esté entre 0 y 1
            
        except Exception as e:
            logger.error(f"Error al calcular el puntaje del producto: {str(e)}", exc_info=True)
            if self.monitor:
                self.monitor.track_exception(e, {"context": "calculate_score", "product_id": product.get('id')})
            return 0.0
    
    def _calculate_price_score(self, price: float, max_price: float, 
                             price_floor: float, price_decay: float) -> float:
        """
        Calcula el puntaje de precio (inverso: precios más bajos son mejores).
        
        Args:
            price: Precio del producto
            max_price: Precio máximo esperado
            price_floor: Precio mínimo esperado
            price_decay: Tasa de decaimiento del puntaje
            
        Returns:
            Puntaje de precio normalizado entre 0 y 1
        """
        if price is None or price <= 0:
            return 0.0
            
        # Aplicar función sigmoide invertida para el precio
        # Esto da más peso a precios bajos y reduce la importancia de precios muy altos
        normalized_price = (min(float(price), max_price) - price_floor) / price_decay
        score = 1.0 / (1.0 + math.exp(normalized_price))
        
        return max(0.0, min(1.0, score))
    
    def _calculate_sales_score(self, sales: int, max_sales: int, sales_weight: float) -> float:
        """
        Calcula el puntaje basado en la cantidad de ventas.
        
        Args:
            sales: Cantidad de ventas
            max_sales: Máximo número de ventas esperado para normalizar
            sales_weight: Peso de las ventas en el puntaje
            
        Returns:
            Puntaje de ventas normalizado entre 0 y 1
        """
        if sales is None or sales <= 0:
            return 0.0
            
        # Usar una función raíz cuadrada para dar más peso a las primeras ventas
        # y reducir la importancia de ventas adicionales después de cierto punto
        normalized_sales = min(float(sales) / max_sales, 1.0)
        score = math.sqrt(normalized_sales) * sales_weight
        
        return max(0.0, min(1.0, score))
    
    def _calculate_condition_score(self, condition: str, condition_config: dict) -> float:
        """
        Calcula el puntaje basado en la condición del producto.
        
        Args:
            condition: Condición del producto (new, used, etc.)
            condition_config: Configuración de puntuación por condición
            
        Returns:
            Puntaje de condición normalizado entre 0 y 1
        """
        # Obtener puntuaciones de condición desde la configuración o usar valores por defecto
        condition_scores = condition_config.get('scores', {
            'new': 1.0,
            'new_other': 0.9,
            'new_with_defects': 0.8,
            'manufacturer_refurbished': 0.7,
            'seller_refurbished': 0.6,
            'used': 0.5,
            'for_parts': 0.3,
            'not_specified': 0.5
        })
        
        return condition_scores.get(condition.lower(), condition_config.get('default_score', 0.5))
    
    def _calculate_seller_score(self, seller: dict, seller_config: dict) -> float:
        """
        Calcula el puntaje basado en la reputación del vendedor.
        
        Args:
            seller: Datos del vendedor
            seller_config: Configuración para el cálculo del puntaje
            
        Returns:
            Puntaje de vendedor normalizado entre 0 y 1
        """
        if not seller:
            return seller_config.get('default_score', 0.5)
            
        # Obtener métricas del vendedor
        reputation = seller.get('seller_reputation', {})
        transactions = reputation.get('transactions', {})
        
        # Calcular puntaje basado en la reputación
        seller_score = seller_config.get('base_score', 0.5)
        
        # Ajustar según el nivel de reputación
        level_id = reputation.get('level_id')
        if level_id in seller_config.get('level_multipliers', {}):
            seller_score *= seller_config['level_multipliers'][level_id]
            
        # Ajustar según las transacciones completadas
        completed = transactions.get('completed', 0)
        if completed > 0:
            seller_score += min(completed * seller_config.get('completed_transaction_weight', 0.0001), 
                             seller_config.get('max_transaction_bonus', 0.2))
        
        return max(0.0, min(1.0, seller_score))
    
    def _calculate_shipping_score(self, shipping: dict, shipping_config: dict) -> float:
        """
        Calcula el puntaje basado en las opciones de envío.
        
        Args:
            shipping: Datos de envío
            shipping_config: Configuración para el cálculo del puntaje
            
        Returns:
            Puntaje de envío normalizado entre 0 y 1
        """
        if not shipping:
            return shipping_config.get('default_score', 0.5)
            
        # Puntaje base
        shipping_score = shipping_config.get('base_score', 0.5)
        
        # Bonificación por envío gratuito
        if shipping.get('free_shipping', False):
            shipping_score += shipping_config.get('free_shipping_bonus', 0.2)
            
        # Bonificación por envío rápido
        if shipping.get('fast_shipping', False):
            shipping_score += shipping_config.get('fast_shipping_bonus', 0.1)
            
        return max(0.0, min(1.0, shipping_score))
    
    def rank_products(self, products: List[Dict[str, Any]], limit: int = 10, top_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ordena una lista de productos según su puntaje.
        
        Args:
            products: Lista de productos a ordenar
            limit: Número máximo de productos a devolver (0 para todos)
            top_n: Alias para limit (opcional, por compatibilidad)
            
        Returns:
            Lista de productos ordenados por puntaje descendente
        """
        # Usar top_n si se proporciona, de lo contrario usar limit
        result_limit = top_n if top_n is not None else limit
        
        if not products:
            return []
            
        # Calcular puntaje para cada producto
        scored_products = []
        for product in products:
            score = self.calculate_score(product)
            product_with_score = product.copy()
            product_with_score['_ranking_score'] = score
            scored_products.append(product_with_score)
        
        # Ordenar por puntaje descendente
        scored_products.sort(key=lambda x: x.get('_ranking_score', 0), reverse=True)
        
        # Aplicar límite si es necesario
        if result_limit > 0:
            return scored_products[:result_limit]
            
        return scored_products
