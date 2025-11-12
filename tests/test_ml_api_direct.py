"""
Script de prueba directa para la API de MercadoLibre.
"""
import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_ml_api_direct.log')
    ]
)
logger = logging.getLogger(__name__)

def test_api_connection():
    """Prueba la conexión directa con la API de MercadoLibre."""
    # Cargar variables de entorno
    load_dotenv()
    
    # Obtener la clave de la API
    rapidapi_key = os.getenv('RAPIDAPI_KEY')
    if not rapidapi_key:
        logger.error("No se encontró la variable de entorno RAPIDAPI_KEY")
        print("ERROR: Debes configurar la variable de entorno RAPIDAPI_KEY")
        return False
    
    # Configurar parámetros de la petición
    url = "https://mercado-libre7.p.rapidapi.com/listings_for_search"
    
    # Usar parámetros de línea de comandos o valores por defecto
    query = sys.argv[1] if len(sys.argv) > 1 else "televisor"
    country = (sys.argv[2] if len(sys.argv) > 2 else "AR").upper()
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    querystring = {
        "search_str": query,
        "country": country.lower(),
        "page_num": "1",
        "sort_by": "relevance"
    }
    
    if limit != 10:  # 10 es el valor por defecto
        querystring["limit"] = str(limit)
    
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "mercado-libre7.p.rapidapi.com"
    }
    
    logger.info(f"Iniciando prueba de conexión con la API de MercadoLibre")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {json.dumps(headers, indent=2)}")
    logger.info(f"Parámetros: {json.dumps(querystring, indent=2)}")
    
    try:
        # Realizar la petición
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        
        # Mostrar información de la respuesta
        logger.info(f"Respuesta recibida - Status Code: {response.status_code}")
        logger.info(f"URL de respuesta: {response.url}")
        
        # Intentar decodificar la respuesta JSON
        try:
            data = response.json()
            logger.info("Respuesta JSON recibida correctamente")
            
            # Guardar la respuesta completa en un archivo
            with open('ml_api_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Respuesta guardada en 'ml_api_response.json'")
            
            # Mostrar información resumida
            if isinstance(data, dict):
                if 'results' in data:
                    print(f"\n=== RESULTADOS DE BÚSQUEDA ===")
                    print(f"Término: {query}")
                    print(f"País: {country}")
                    print(f"Total de resultados: {data.get('paging', {}).get('total', 'Desconocido')}")
                    print(f"Resultados obtenidos: {len(data.get('results', []))}")
                    
                    # Mostrar los primeros 3 resultados
                    for i, item in enumerate(data.get('results', [])[:3], 1):
                        print(f"\n--- Resultado {i} ---")
                        print(f"ID: {item.get('id')}")
                        print(f"Título: {item.get('title')}")
                        print(f"Precio: {item.get('price')} {item.get('currency_id')}")
                        print(f"Condición: {item.get('condition')}")
                        print(f"Vendedor: {item.get('seller', {}).get('nickname')}")
                else:
                    print("\nLa respuesta no contiene resultados. Estructura recibida:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print("\nLa respuesta no es un diccionario. Tipo recibido:", type(data))
                print("Contenido:", data)
            
            return True
            
        except Exception as json_error:
            logger.error(f"Error al decodificar la respuesta JSON: {str(json_error)}")
            logger.error(f"Contenido de la respuesta: {response.text[:1000]}")
            print(f"\nERROR al procesar la respuesta JSON: {str(json_error)}")
            print(f"Contenido de la respuesta: {response.text[:500]}...")
            
    except Exception as e:
        logger.error(f"Error en la petición: {str(e)}", exc_info=True)
        print(f"\nERROR en la petición: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("=== PRUEBA DIRECTA DE LA API DE MERCADO LIBRE ===\n")
    
    if test_api_connection():
        print("\nPrueba completada con éxito. Revisa el archivo 'ml_api_response.json' para ver los detalles completos.")
    else:
        print("\nLa prueba ha fallado. Revisa los logs para más detalles.")
