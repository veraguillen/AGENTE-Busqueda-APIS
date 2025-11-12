"""
Pruebas unitarias para el AgenteGMaps.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from agents.agente_gmaps import AgenteGMaps

class TestAgenteGMaps(unittest.TestCase):
    """Caso de prueba para el AgenteGMaps."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Mock de ConfigManager
        self.config_mock = Mock()
        self.config_mock.get.side_effect = lambda key, default=None: {
            'google.maps.api': {
                'base_url': 'https://maps.googleapis.com/maps/api/place',
                'endpoints': {
                    'textsearch': '/textsearch/json',
                    'details': '/details/json',
                    'findplace': '/findplacefromtext/json'
                },
                'fields': 'formatted_address,geometry,name,place_id,types',
                'locationbias': 'ipbias',
                'max_results': 5
            },
            'cache.ttl': 3600  # 1 hora
        }.get(key, default)
        
        # Mock para la caché
        self.cache_mock = Mock()
        self.cache_mock.get.return_value = None  # Por defecto, no hay caché
        
        # Mock para el monitor
        self.monitor_mock = Mock()
        
        # Instancia del agente
        self.agente = AgenteGMaps(
            google_api_key="test_key",
            config=self.config_mock,
            cache=self.cache_mock,
            monitor=self.monitor_mock
        )
        
        # Mock para la API de Google Maps
        self.api_client_mock = Mock()
        # Inyectar el mock del APIClient en el constructor
        self.agente = AgenteGMaps(
            google_api_key="test_key",
            api_client=self.api_client_mock,
            config=self.config_mock,
            cache=self.cache_mock,
            monitor=self.monitor_mock
        )
    
    @patch('agents.agente_gmaps.logger')
    def test_search_business(self, mock_logger):
        """Prueba la búsqueda de negocios en Google Maps."""
        # Configurar el mock para devolver una respuesta exitosa
        mock_response = {
            "results": [
                {
                    "place_id": "ChIJd8BlQ2BZwokRAFUEcm_qrcA",
                    "name": "Tienda de Electrónica",
                    "formatted_address": "Calle Falsa 123, CABA, Argentina",
                    "geometry": {
                        "location": {
                            "lat": -34.6037,
                            "lng": -58.3816
                        },
                        "viewport": {
                            "northeast": {"lat": -34.6023510197085, "lng": -58.3803509802915},
                            "southwest": {"lat": -34.6050489802915, "lng": -58.3830489397085}
                        }
                    },
                    "types": ["electronics_store", "store", "point_of_interest", "establishment"],
                    "rating": 4.5,
                    "user_ratings_total": 128,
                    "business_status": "OPERATIONAL",
                    "plus_code": {
                        "compound_code": "C123+X2 CABA, Argentina",
                        "global_code": "5883C123+X2"
                    }
                }
            ],
            "status": "OK"
        }
        
        # Configurar el mock para devolver la respuesta
        self.api_client_mock.get.return_value.status_code = 200
        self.api_client_mock.get.return_value.json.return_value = mock_response
        
        # Ejecutar la búsqueda
        query = "tienda de electrónica"
        resultados = self.agente.search_business(query, use_fallback=False)
        
        # Verificar resultados
        self.assertIn('results', resultados, "La respuesta debe contener la clave 'results'")
        self.assertIsInstance(resultados['results'], list, "Los resultados deben ser una lista")
        self.assertGreater(len(resultados['results']), 0, "Debería devolver al menos un resultado")
        
        primer_resultado = resultados['results'][0]
        self.assertEqual(primer_resultado["name"], "Tienda de Electrónica", "El nombre del lugar es incorrecto")
        self.assertEqual(primer_resultado["formatted_address"], "Calle Falsa 123, CABA, Argentina", "La dirección es incorrecta")
        self.assertEqual(primer_resultado["geometry"]["location"]["lat"], -34.6037, "La latitud es incorrecta")
        self.assertEqual(primer_resultado["geometry"]["location"]["lng"], -58.3816, "La longitud es incorrecta")
        
        # Verificar que se llamó a la API con los parámetros correctos
        expected_params = {
            'query': f"{query} {location}",
            'key': 'test_key',
            'language': 'es',
            'region': 'ar',
            'fields': 'formatted_address,geometry,name,place_id,types'
        }
        
        self.api_client_mock.get.assert_called_once()
        args, kwargs = self.api_client_mock.get.call_args
        self.assertEqual(kwargs['params']['query'], expected_params['query'])
        self.assertEqual(kwargs['params']['key'], expected_params['key'])
        
        # Verificar que se registró la métrica
        self.monitor_mock.registrar_metrica.assert_called_once()
        metric_name, metric_value = self.monitor_mock.registrar_metrica.call_args[0]
        self.assertEqual(metric_name, 'tiempo_respuesta_gmaps')
        self.assertIsInstance(metric_value, (int, float))
        self.api_client_mock.get.assert_called()

if __name__ == "__main__":
    unittest.main()
