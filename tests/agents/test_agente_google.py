"""
Pruebas unitarias para el AgenteGoogle.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from agents.agente_google import AgenteGoogle

class TestAgenteGoogle(unittest.TestCase):
    """Caso de prueba para el AgenteGoogle."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Mock de ConfigManager
        self.config_mock = Mock()
        self.config_mock.get.side_effect = lambda key, default=None: {
            'google.api': {
                'base_url': 'https://www.googleapis.com/customsearch/v1',
                'cse_id': 'test_cse_id',
                'api_key': 'test_key',
                'search_type': 'image',
                'num_results': 10,
                'safe': 'high',
                'fields': 'items(title,link,snippet,pagemap)'
            },
            'cache.ttl': 3600  # 1 hora
        }.get(key, default)
        
        # Mock para la caché
        self.cache_mock = Mock()
        self.cache_mock.get.return_value = None  # Por defecto, no hay caché
        
        # Mock para el monitor
        self.monitor_mock = Mock()
        
        # Instancia del agente
        self.agente = AgenteGoogle(
            google_api_key="test_key",
            google_cse_id="test_cse_id",
            cache=self.cache_mock,
            monitor=self.monitor_mock
        )
        
        # Mock para la API de Google
        self.api_client_mock = Mock()
        self.agente.api_client = self.api_client_mock
    
    @patch('agents.agente_google.logger')
    def test_search_seller_contacts(self, mock_logger):
        """Prueba la búsqueda de contactos de vendedor en Google."""
        # Configurar el mock para devolver una respuesta exitosa
        mock_response = {
            "items": [
                {
                    "title": "Tienda de Electrónica XYZ",
                    "link": "https://tiendaelectronica.com",
                    "snippet": "Venta de productos electrónicos en Buenos Aires",
                    "pagemap": {
                        "metatags": [{
                            "og:site_name": "Tienda de Electrónica XYZ",
                            "og:description": "Los mejores precios en electrónica",
                            "business:contact_data:website": "https://tiendaelectronica.com",
                            "business:contact_data:phone_number": "+541112345678"
                        }],
                        "localbusiness": [{
                            "name": "Tienda de Electrónica XYZ",
                            "address": {
                                "streetAddress": "Av. Corrientes 1234",
                                "addressLocality": "Buenos Aires",
                                "addressRegion": "CABA",
                                "postalCode": "C1043",
                                "addressCountry": "AR"
                            },
                            "telephone": "+541112345678",
                            "openingHours": "Mo-Fr 10:00-20:00",
                            "priceRange": "$$",
                            "image": "https://tiendaelectronica.com/logo.jpg"
                        }]
                    }
                },
                {
                    "title": "Electrónica Moderna SA",
                    "link": "https://electronicamoderna.com.ar",
                    "snippet": "Venta de electrónica y electrodomésticos",
                    "pagemap": {
                        "metatags": [{
                            "og:site_name": "Electrónica Moderna",
                            "og:description": "Especialistas en tecnología",
                            "business:contact_data:website": "https://electronicamoderna.com.ar",
                            "business:contact_data:phone_number": "+541119876543"
                        }]
                    }
                }
            ],
            "searchInformation": {
                "totalResults": "2",
                "searchTime": 0.35
            }
        }
        
        # Configurar el mock para devolver la respuesta
        self.api_client_mock.get.return_value.status_code = 200
        self.api_client_mock.get.return_value.json.return_value = mock_response
        
        # Ejecutar la búsqueda
        seller_nickname = "electronica_xyz"
        resultados = self.agente.search_seller_contacts(seller_nickname)
        
        # Verificar resultados
        self.assertIsInstance(resultados, dict, "El resultado debe ser un diccionario")
        self.assertIn("phone", resultados, "El resultado debe incluir teléfono")
        self.assertIn("email", resultados, "El resultado debe incluir email")
        self.assertIn("facebook_url", resultados, "El resultado debe incluir URL de Facebook")
        # Verificar que el nombre está en el formato correcto (puede estar en diferentes claves)
        self.assertTrue(
            any(key in resultados for key in ["name", "business_name", "company_name"]),
            "El resultado debe incluir el nombre de la empresa"
        )
        # Verificar que la web está en el formato correcto
        self.assertTrue(
            any(key in resultados for key in ["website", "web", "url"]),
            "El resultado debe incluir la URL del sitio web"
        )
        # Verificar que el teléfono está en el formato correcto
        self.assertEqual(resultados["phone"], "+541112345678", "El teléfono es incorrecto")
        
        # Verificar que se llamó a la API con los parámetros correctos
        self.api_client_mock.get.assert_called_once()
        args, kwargs = self.api_client_mock.get.call_args
        
        # Verificar parámetros de la llamada
        self.assertEqual(kwargs['params']['q'], f"{query} {location}")
        self.assertEqual(kwargs['params']['key'], 'test_key')
        self.assertEqual(kwargs['params']['cx'], 'test_cse_id')
        
        # Verificar que se registró la métrica
        self.monitor_mock.registrar_metrica.assert_called_once()
        metric_name, metric_value = self.monitor_mock.registrar_metrica.call_args[0]
        self.assertEqual(metric_name, 'tiempo_respuesta_google')
        self.assertIsInstance(metric_value, (int, float))

if __name__ == "__main__":
    unittest.main()
