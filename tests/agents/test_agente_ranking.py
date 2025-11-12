"""
Pruebas unitarias para el AgenteRanking.
"""
import unittest
from unittest.mock import Mock, patch
from agents.agente_ranking import AgenteRanking

class TestAgenteRanking(unittest.TestCase):
    """Caso de prueba para el AgenteRanking."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Mock de ConfigManager
        self.config_mock = Mock()
        self.config_mock.get.return_value = {
            'price': 0.4,
            'sales': 0.4,
            'condition': 0.2
        }
        
        # Instancia del agente
        self.agente = AgenteRanking(config=self.config_mock)
    
    def test_calculate_score(self):
        """Prueba el cálculo de puntaje para un producto."""
        # Productos de prueba
        producto1 = {
            "price": 1000,
            "sold_quantity": 100,  # Más ventas
            "available_quantity": 10,
            "condition": "new",
            "seller": {
                "reputation_level_id": "5_green"
            },
            "shipping": {
                "free_shipping": True
            }
        }
        
        producto2 = {
            "price": 500,  # Más barato
            "sold_quantity": 50,
            "available_quantity": 5,
            "condition": "new",
            "seller": {
                "reputation_level_id": "5_green"
            },
            "shipping": {
                "free_shipping": True
            }
        }
        
        # Calcular puntuaciones
        puntuacion1 = self.agente.calculate_score(producto1)
        puntuacion2 = self.agente.calculate_score(producto2)
        
        # Verificar que la relación ventas/precio tiene más peso
        # producto2 es más barato y debería tener mejor puntuación
        self.assertGreater(puntuacion2, puntuacion1, 
                         "El producto más barato con buena relación ventas/precio debería tener mejor puntuación")
        
        # Verificar que la puntuación está dentro del rango esperado
        for producto, puntuacion in [(producto1, puntuacion1), (producto2, puntuacion2)]:
            with self.subTest(producto=producto):
                self.assertGreaterEqual(puntuacion, 0, f"La puntuación no puede ser negativa: {puntuacion}")
                self.assertLessEqual(puntuacion, 1, f"La puntuación no puede ser mayor a 1: {puntuacion}")
        
        # Verificar que la relación ventas/precio tiene más peso que otros factores
        producto_caro_muchas_ventas = {
            "price": 2000,  # Más caro
            "sold_quantity": 200,  # Más ventas
            "available_quantity": 20,
            "condition": "used",  # Condición usada
            "seller": {
                "reputation_level_id": "3_yellow"  # Reputación media
            },
            "shipping": {
                "free_shipping": False  # Sin envío gratis
            }
        }
        
        puntuacion3 = self.agente.calculate_score(producto_caro_muchas_ventas)
        self.assertGreater(puntuacion2, puntuacion3, 
                         "La relación ventas/precio debería pesar más que otros factores")
    
    @patch('agents.agente_ranking.logger')
    def test_rank_products(self, mock_logger):
        """Prueba el ranking de múltiples productos con diferentes características."""
        # Lista de productos de prueba con diferentes combinaciones de precios y ventas
        productos = [
            {
                "id": 1, 
                "price": 1000, 
                "sold_quantity": 10, 
                "available_quantity": 5,
                "condition": "new",
                "shipping": {"free_shipping": True},
                "seller": {"seller_reputation": {"level_id": "5_green"}}
            },
            {
                "id": 2, 
                "price": 500, 
                "sold_quantity": 20, 
                "available_quantity": 10,
                "condition": "used",
                "shipping": {"free_shipping": False},
                "seller": {"seller_reputation": {"level_id": "4_blue"}}
            },
            {
                "id": 3, 
                "price": 2000, 
                "sold_quantity": 5, 
                "available_quantity": 20,
                "condition": "new",
                "shipping": {"free_shipping": True, "fast_shipping": True},
                "seller": {"seller_reputation": {"level_id": "5_green"}}
            }
        ]
        
        # Ejecutar el ranking completo
        resultado = self.agente.rank_products(productos)
        
        # Verificar que se devuelven todos los productos
        self.assertEqual(len(resultado), 3)
        
        # Verificar que los productos están ordenados por puntaje descendente
        scores = [p['_ranking_score'] for p in resultado]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Verificar que el producto con mejor puntaje (precio bajo + más ventas) esté primero
        # El producto 2 debería tener mejor puntaje por tener mejor relación precio/ventas
        self.assertEqual(resultado[0]["id"], 2)
        
        # Verificar que el producto más caro tenga el peor puntaje
        self.assertEqual(resultado[-1]["id"], 3)
        
        # Probar con límite de resultados
        limited_result = self.agente.rank_products(productos, limit=2)
        self.assertEqual(len(limited_result), 2)
        
        # Verificar que el alias top_n funciona igual que limit
        top_n_result = self.agente.rank_products(productos, top_n=1)
        self.assertEqual(len(top_n_result), 1)
        self.assertEqual(top_n_result[0]["id"], 2)

if __name__ == "__main__":
    unittest.main()
