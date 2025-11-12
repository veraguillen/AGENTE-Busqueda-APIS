"""
Pruebas unitarias para el AgenteFiltro.
"""
import unittest
from unittest.mock import Mock
from agents.agente_filtro import AgenteFiltro

class TestAgenteFiltro(unittest.TestCase):
    """Caso de prueba para el AgenteFiltro."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Mock de ConfigManager
        self.config_mock = Mock()
        # Configurar valores de retorno para diferentes llamadas a config.get
        self.config_mock.get.side_effect = lambda key, default=None: {
            'filters.excluded_brands': ["sony", "samsung", "lg"],
            'filters.min_price': 1000,  # Precio mínimo para pruebas
            'filters.max_price': 50000,  # Precio máximo para pruebas
            'filters.condition': 'any',   # Condición del producto
            'filters.shipping.free': False,  # Envío gratis
            'filters.shipping.logistic_type': 'cross_docking',  # Tipo de logística
            'filters.attributes': [],  # Atributos adicionales
            'filters.currency': 'ARS'  # Moneda
        }.get(key, default)
        
        # Instancia del agente
        self.agente = AgenteFiltro(config=self.config_mock)
    
    def test_filtrar_listados_marcas_excluidas(self):
        """Prueba que se filtren correctamente las marcas excluidas."""
        # Datos de prueba con más campos para pruebas realistas
        listados = [
            {
                "id": "1",
                "title": "TV Sony 50 pulgadas 4K",
                "price": 25000,
                "condition": "new",
                "shipping": {"free_shipping": True, "logistic_type": "cross_docking"},
                "currency_id": "ARS",
                "seller": {"id": 1, "nickname": "sony_official"},
                "attributes": [{"id": "BRAND", "value_name": "Sony"}]
            },
            {
                "id": "2",
                "title": "Samsung Galaxy S20",
                "price": 30000,
                "condition": "used",
                "shipping": {"free_shipping": False, "logistic_type": "drop_off"},
                "currency_id": "ARS",
                "seller": {"id": 2, "nickname": "samsung_store"},
                "attributes": [{"id": "BRAND", "value_name": "Samsung"}]
            },
            {
                "id": "3",
                "title": "iPhone 12 128GB",
                "price": 45000,
                "condition": "new",
                "shipping": {"free_shipping": True, "logistic_type": "cross_docking"},
                "currency_id": "ARS",
                "seller": {"id": 3, "nickname": "apple_store"},
                "attributes": [{"id": "BRAND", "value_name": "Apple"}]
            },
            {
                "id": "4",
                "title": "LG Smart TV 55",
                "price": 18000,
                "condition": "new",
                "shipping": {"free_shipping": True, "logistic_type": "cross_docking"},
                "currency_id": "ARS",
                "seller": {"id": 4, "nickname": "lg_shop"},
                "attributes": [{"id": "BRAND", "value_name": "LG"}]
            },
            {
                "id": "5",
                "title": "Xiaomi Mi 11 Lite",
                "price": 12000,
                "condition": "new",
                "shipping": {"free_shipping": True, "logistic_type": "cross_docking"},
                "currency_id": "ARS",
                "seller": {"id": 5, "nickname": "xiaomi_store"},
                "attributes": [{"id": "BRAND", "value_name": "Xiaomi"}]
            }
        ]
        
        # Ejecutar el filtrado
        resultado = self.agente.filter_listings(listados)
        
        # Verificar resultados - solo deberían quedar iPhone y Xiaomi
        self.assertEqual(len(resultado), 2, "Deberían quedar 2 productos después del filtrado")
        remaining_ids = {item["id"] for item in resultado}
        self.assertIn("3", remaining_ids, "El iPhone 12 debería estar en los resultados")
        self.assertIn("5", remaining_ids, "El Xiaomi Mi 11 debería estar en los resultados")

if __name__ == "__main__":
    unittest.main()
