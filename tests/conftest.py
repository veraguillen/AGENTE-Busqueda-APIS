import os
import pytest
from typing import Dict, Any

@pytest.fixture
def rapidapi_key() -> str:
    """Fixture para obtener la clave de RapidAPI desde variables de entorno."""
    key = os.environ.get('RAPIDAPI_KEY')
    if not key:
        pytest.fail("La variable de entorno RAPIDAPI_KEY no está configurada")
    return key

@pytest.fixture
def google_api_key() -> str:
    """Fixture para obtener la clave de Google API desde variables de entorno."""
    key = os.environ.get('GOOGLE_API_KEY')
    if not key:
        pytest.fail("La variable de entorno GOOGLE_API_KEY no está configurada")
    return key

@pytest.fixture
def api_key(google_api_key: str) -> str:
    """Fixture que devuelve la clave de Google API."""
    return google_api_key

@pytest.fixture
def seller_name() -> str:
    """Proporciona un nombre de vendedor de prueba genérico."""
    return "Vendedor Confiable"
