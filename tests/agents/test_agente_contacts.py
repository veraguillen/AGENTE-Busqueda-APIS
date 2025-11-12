"""
Pruebas unitarias para el AgenteContacts.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from agents.agente_contacts import AgenteContacts
from agents.agente_gmaps import AgenteGMaps
from agents.agente_google import AgenteGoogle

class MockAgenteGMaps:
    def __init__(self, *args, **kwargs):
        self.search_business = Mock()

class MockAgenteGoogle:
    def __init__(self, *args, **kwargs):
        self.search_seller_contacts = Mock()

class TestAgenteContacts(unittest.TestCase):
    """Caso de prueba para el AgenteContacts."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear mocks para las dependencias
        self.gmaps_mock = MockAgenteGMaps()
        self.google_mock = MockAgenteGoogle()
        
        # Crear instancia del agente con los mocks inyectados
        self.agente = AgenteContacts(
            google_api_key="test_key",
            agente_gmaps=self.gmaps_mock,
            agente_google=self.google_mock
        )
    
    def test_get_contact_info_web_search(self):
        """Prueba la búsqueda de contactos a través de búsqueda web."""
        # Configurar el mock para search_seller_contacts
        mock_web_result = {
            "status": "success",
            "data": {
                "name": "Tienda de Juan",
                "phone": "+541112345678",
                "email": "contacto@tiendadejuan.com",
                "website": "https://tiendadejuan.com"
            }
        }
        self.google_mock.search_seller_contacts.return_value = mock_web_result
        
        # Ejecutar la búsqueda
        resultados = self.agente.get_contact_info("Tienda de Juan", search_strategy="web")
        
        # Verificar que se llamó al método correcto
        self.google_mock.search_seller_contacts.assert_called_once_with("Tienda de Juan")
        
        # Verificar los resultados
        self.assertEqual(resultados["status"], "success")
        self.assertEqual(resultados["data"]["name"], "Tienda de Juan")
        self.assertEqual(resultados["data"]["phone"], "+541112345678")
    
    def test_get_contact_info_location_search(self):
        """Prueba la búsqueda de contactos a través de ubicaciones."""
        # Configurar el mock para search_business
        mock_location_result = {
            "status": "OK",
            "results": [{
                "name": "Tienda de Juan",
                "formatted_address": "Calle Falsa 123, Buenos Aires",
                "formatted_phone_number": "+541112345678",
                "website": "https://tiendadejuan.com",
                "rating": 4.5,
                "user_ratings_total": 120
            }]
        }
        self.gmaps_mock.search_business.return_value = mock_location_result
        
        # Ejecutar la búsqueda
        resultados = self.agente.get_contact_info("Tienda de Juan", search_strategy="location")
        
        # Verificar que se llamó al método correcto
        self.gmaps_mock.search_business.assert_called_once_with("Tienda de Juan", use_fallback=True)
        
        # Verificar los resultados
        self.assertEqual(resultados["status"], "OK")
        self.assertIn("results", resultados)
        self.assertEqual(len(resultados["results"]), 1)
        self.assertEqual(resultados["results"][0]["name"], "Tienda de Juan")
    
    def test_get_contact_info_all_strategies(self):
        """Prueba la búsqueda de contactos con todas las estrategias."""
        # Configurar mocks para ambas estrategias
        mock_web_result = {
            "status": "success",
            "data": {"name": "Tienda de Juan", "phone": "+541112345678"}
        }
        mock_location_result = {
            "status": "OK",
            "results": [{"name": "Tienda de Juan", "formatted_phone_number": "+541112345678"}]
        }
        self.google_mock.search_seller_contacts.return_value = mock_web_result
        self.gmaps_mock.search_business.return_value = mock_location_result
        
        # Ejecutar la búsqueda
        resultados = self.agente.get_contact_info("Tienda de Juan", search_strategy="all")
        
        # Verificar que se llamaron ambos métodos
        self.google_mock.search_seller_contacts.assert_called_once_with("Tienda de Juan")
        self.gmaps_mock.search_business.assert_called_once_with("Tienda de Juan", use_fallback=True)
        
        # Verificar que se combinaron los resultados
        self.assertIn("web", resultados)
        self.assertIn("location", resultados)
        self.assertEqual(resultados["web"]["data"]["name"], "Tienda de Juan")
        self.assertEqual(resultados["location"]["results"][0]["name"], "Tienda de Juan")

if __name__ == "__main__":
    unittest.main()
