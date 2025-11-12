#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo de búsqueda de contactos usando GMaps con RapidAPI
"""

import os
import sys
import json
import time
import logging
import dotenv
from colorama import init, Fore, Style, Back

# Inicializar colorama
init()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Cargar variables de entorno
dotenv.load_dotenv()

def print_color(text, color=Fore.WHITE, bright=False):
    """Imprime texto con color"""
    if bright:
        print(f"{color}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    else:
        print(f"{color}{text}{Style.RESET_ALL}")

def main():
    """Función principal de la demo"""
    print_color("DEMO DE BÚSQUEDA DE CONTACTOS CON GMAPS/RAPIDAPI", Fore.BLUE, True)
    print_color("-" * 60, Fore.BLUE)
    
    # Verificar disponibilidad de RapidAPI Key
    rapid_api_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_api_key:
        print_color("Error: No se encontró la variable RAPIDAPI_KEY en el entorno", Fore.RED)
        return
    
    print_color("✓ API Key encontrada", Fore.GREEN)
    
    # Importar agente de GMaps
    from agents.agente_gmaps import AgenteGMaps
    
    # Inicializar agente
    print_color("Inicializando agente...", Fore.CYAN)
    agente_maps = AgenteGMaps(google_api_key=rapid_api_key)
    print_color("✓ Agente inicializado correctamente", Fore.GREEN)
    
    # Bucle principal
    while True:
        print("\n" + "-" * 60)
        print_color("Búsqueda de contactos por nombre de vendedor/negocio", Fore.YELLOW, True)
        
        # Solicitar nombre del negocio
        seller = input(f"{Fore.WHITE}Nombre del vendedor/negocio (o 'salir' para terminar): {Style.RESET_ALL}")
        if seller.lower() == "salir":
            break
        
        if not seller:
            print_color("Por favor ingrese un nombre válido", Fore.RED)
            continue
        
        # Solicitar país
        country = input(f"{Fore.WHITE}País (ej: argentina, mexico, brasil): {Style.RESET_ALL}")
        if not country:
            country = "argentina"  # Valor predeterminado
        
        # Búsqueda en GMaps
        print_color(f"Buscando información para '{seller}' en {country}...", Fore.CYAN)
        
        try:
            # Medir tiempo de ejecución
            start_time = time.time()
            
            # Realizar búsqueda
            result = agente_maps.find_business(seller)
            
            # Calcular tiempo de respuesta
            elapsed_time = time.time() - start_time
            
            # Mostrar resultados
            if result:
                print_color(f"✓ Información encontrada en {elapsed_time:.2f} segundos:", Fore.GREEN, True)
                
                # Mostrar datos básicos
                if isinstance(result, dict):
                    # Priorizar los campos más importantes
                    important_fields = ["name", "formatted_address", "phone", "website", "rating"]
                    
                    for field in important_fields:
                        if field in result and result[field]:
                            print_color(f"{field.capitalize()}: {result[field]}", Fore.WHITE)
                    
                    # Mostrar otros campos disponibles
                    for key, value in result.items():
                        if key not in important_fields and value and not isinstance(value, (list, dict)):
                            print_color(f"{key.capitalize()}: {value}", Fore.WHITE)
                    
                    # Si hay reviews, mostrar la primera
                    if "reviews" in result and result["reviews"]:
                        print_color("\nEjemplo de review:", Fore.CYAN)
                        review = result["reviews"][0]
                        print(f"Rating: {review.get('rating', 'N/A')}")
                        print(f"Autor: {review.get('author_name', 'Anónimo')}")
                        print(f"Comentario: {review.get('text', 'Sin comentario')[:100]}...")
                    
                    # Guardar resultado completo en archivo JSON para revisión
                    with open(f"info_{seller.replace(' ', '_')}_{int(time.time())}.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                        print_color(f"\nResultado completo guardado en archivo JSON", Fore.GREEN)
                
                elif isinstance(result, list) and result:
                    print_color(f"Se encontraron {len(result)} resultados", Fore.CYAN)
                    
                    # Mostrar el primer resultado
                    first = result[0]
                    print_color("Primer resultado:", Fore.CYAN)
                    for key, value in first.items():
                        if not isinstance(value, (list, dict)) and value:
                            print_color(f"{key.capitalize()}: {value}", Fore.WHITE)
                    
                    # Guardar todos los resultados
                    with open(f"resultados_{seller.replace(' ', '_')}_{int(time.time())}.json", "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                        print_color(f"\nResultados completos guardados en archivo JSON", Fore.GREEN)
                else:
                    print_color(f"Respuesta recibida pero en formato inesperado: {type(result)}", Fore.YELLOW)
            else:
                print_color("No se encontró información para este vendedor/negocio", Fore.RED)
        
        except Exception as e:
            print_color(f"Error al buscar información: {str(e)}", Fore.RED)
            logger.exception("Error en búsqueda de GMaps")
    
    print_color("\nGracias por usar la demo de búsqueda de contactos", Fore.BLUE, True)

if __name__ == "__main__":
    main()
