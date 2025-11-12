"""
Pruebas unitarias para el AgenteML.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from agents.agente_ml import AgenteML

class TestAgenteML(unittest.TestCase):
    """Caso de prueba para el AgenteML."""
    
    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Mock de APIClient
        self.api_client_mock = Mock()
        
        # Configuración simulada
        self.config_mock = Mock()
        self.config_mock.get.side_effect = lambda key, default=None: {
            'mercadolibre.api': {
                'host': 'mercado-libre7.p.rapidapi.com',
                'endpoints': {'search': '/listings_for_search'}
            },
            'rapidapi.key': 'test_key',
            'rapidapi.host': 'mercado-libre7.p.rapidapi.com'
        }.get(key, default)
        
        # Instancia del agente
        self.agente = AgenteML(
            rapidapi_key="test_key",
            api_client=self.api_client_mock,
            config=self.config_mock,
            cache=Mock(),
            monitor=Mock()
        )
    
    @patch('agents.agente_ml.logger')
    def test_search(self, mock_logger):
        """Prueba la búsqueda de productos y su conexión con _process_search_response."""
        # Configurar el mock para devolver una respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "1", "title": "iPhone 12", "price": 1000, "seller": {"id": 123, "nickname": "Vendedor Oficial"}},
                {"id": "2", "title": "Samsung S21", "price": 900, "seller": {"id": 456, "nickname": "Tienda Tech"}}
            ],
            "paging": {"total": 2}
        }
        self.api_client_mock.get.return_value = mock_response
        
        # Guardar la implementación original de _process_search_response
        original_process = self.agente._process_search_response
        self.agente._process_search_response = Mock(wraps=original_process)
        
        # Ejecutar la búsqueda
        resultados, total = self.agente.search("smartphone", "AR")
        
        # Verificar que se llamó a la API con los parámetros correctos
        self.api_client_mock.get.assert_called_once()
        
        # Verificar que se llamó a _process_search_response con la respuesta de la API
        self.agente._process_search_response.assert_called_once_with(mock_response.json.return_value)
        
        # Verificar resultados (deberían ser procesados por _process_search_response)
        self.assertIsInstance(resultados, list)
        self.assertIsInstance(total, int)
        
        # Verificar que los resultados coinciden con lo que devuelve _process_search_response
        expected_resultados, expected_total = original_process(mock_response.json.return_value)
        self.assertEqual(resultados, expected_resultados)
        self.assertEqual(total, expected_total)
        
    @patch('agents.agente_ml.logger')
    def test_search_error_handling(self, mock_logger):
        """Prueba el manejo de errores en la búsqueda."""
        # Configurar el mock para lanzar una excepción
        self.api_client_mock.get.side_effect = Exception("Error de conexión")
        
        # El método search debería manejar la excepción y devolver listas vacías
        resultados, total = self.agente.search("smartphone", "AR")
        
        # Verificar que se devolvieron los valores por defecto
        self.assertEqual(resultados, [])
        self.assertEqual(total, 0)
        
        # Verificar que se registró el error
        mock_logger.error.assert_called()

if __name__ == "__main__":
    unittest.main()
