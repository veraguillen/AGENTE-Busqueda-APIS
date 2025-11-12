"""
Script para verificar los endpoints disponibles en RapidAPI para MercadoLibre
"""
import os
import requests
import json

def main():
    print("Verificando endpoints disponibles en RapidAPI para MercadoLibre...")
    
    # Obtener API key de variable de entorno
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("Error: No se encontró RAPIDAPI_KEY en las variables de entorno")
        return
    
    print(f"API Key disponible: {api_key[:5]}...{api_key[-5:]}")
    
    # Lista de posibles hosts y endpoints base para MercadoLibre en RapidAPI
    hosts_to_test = [
        "mercado-libre7.p.rapidapi.com",
        "mercadolibre1.p.rapidapi.com",
        "mercadolibre.p.rapidapi.com",
        "mercado-libre.p.rapidapi.com"
    ]
    
    endpoints_to_test = [
        "/products/search",
        "/search",
        "/sites/MLA/search",
        "/api/products/search",
        "/api/search",
        "/items/search",
        "/seller/search"
    ]
    
    # Parámetros de prueba
    params = {
        "q": "iphone",
        "query": "iphone",
        "search_str": "iphone",
        "keyword": "iphone",
        "country": "ar",
        "site_id": "MLA",
        "limit": "5"
    }
    
    results = []
    
    # Probar cada combinación de host y endpoint
    for host in hosts_to_test:
        print(f"\nProbando host: {host}")
        
        for endpoint in endpoints_to_test:
            base_url = f"https://{host}{endpoint}"
            print(f"  - Endpoint: {base_url}")
            
            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": host
            }
            
            try:
                # Probar con parámetros comunes para búsqueda
                for key, value in params.items():
                    # Solo probar un parámetro a la vez
                    test_params = {key: value}
                    print(f"    Probando con {key}={value}...")
                    
                    try:
                        response = requests.get(base_url, headers=headers, params=test_params, timeout=5)
                        status = response.status_code
                        
                        if status == 200:
                            print(f"    ¡ÉXITO! Código {status} con parámetro {key}={value}")
                            # Intentar decodificar JSON
                            try:
                                data = response.json()
                                # Verificar si hay resultados
                                if isinstance(data, dict):
                                    for result_key in ["results", "data", "items", "products"]:
                                        if result_key in data:
                                            items = data[result_key]
                                            if isinstance(items, list) and items:
                                                print(f"    Se encontraron {len(items)} resultados en '{result_key}'")
                                                
                                                # Guardar esta información exitosa
                                                results.append({
                                                    "host": host,
                                                    "endpoint": endpoint,
                                                    "param_key": key,
                                                    "param_value": value,
                                                    "result_key": result_key,
                                                    "results_count": len(items),
                                                    "sample": items[0] if items else None
                                                })
                                                
                                                # Guardar respuesta para análisis
                                                with open(f"api_test_{host.replace('.', '_')}_{endpoint.replace('/', '_')}_{key}.json", "w", encoding="utf-8") as f:
                                                    json.dump(data, f, indent=2, ensure_ascii=False)
                            except:
                                print(f"    No se pudo analizar la respuesta como JSON")
                        elif status == 404:
                            print(f"    Endpoint no encontrado: {status}")
                        else:
                            print(f"    Código de estado: {status}")
                    
                    except requests.RequestException as e:
                        print(f"    Error de conexión: {str(e)[:50]}")
                
            except Exception as e:
                print(f"  Error general: {e}")
    
    # Mostrar resultados exitosos
    if results:
        print("\n\n=== ENDPOINTS EXITOSOS ENCONTRADOS ===")
        for i, result in enumerate(results):
            print(f"\n{i+1}. Host: {result['host']}")
            print(f"   Endpoint: {result['endpoint']}")
            print(f"   Parámetro: {result['param_key']}={result['param_value']}")
            print(f"   Resultados en: {result['result_key']}")
            print(f"   Cantidad: {result['results_count']}")
            
        # Guardar resultados exitosos
        with open("rapidapi_mercadolibre_endpoints.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("\nResultados guardados en rapidapi_mercadolibre_endpoints.json")
    else:
        print("\nNo se encontraron endpoints funcionales.")

if __name__ == "__main__":
    main()
