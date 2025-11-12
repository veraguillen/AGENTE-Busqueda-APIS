#!/usr/bin/env python3
"""Script para ejecutar todas las pruebas unitarias de los agentes."""
import unittest
import sys
import os

def run_tests():
    """Ejecuta todas las pruebas unitarias."""
    # Agregar el directorio raíz al path
    sys.path.insert(0, os.path.abspath('.'))
    
    # Configurar entorno de pruebas
    os.environ['TESTING'] = 'True'
    
    # Descubrir y cargar todas las pruebas
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Ejecutar las pruebas
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_loader.suiteClass(test_suite))
    
    # Retornar código de salida apropiado
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
