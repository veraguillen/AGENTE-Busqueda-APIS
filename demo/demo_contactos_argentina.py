#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo del Agente de Contactos para Argentina
Muestra el flujo de búsqueda y extracción de información de contacto
"""

import os
import sys
import json
import time
import logging
from colorama import init, Fore, Style, Back

# Inicializar colorama para colores en consola
init()

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Asegurar que podemos acceder a los módulos del proyecto
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importar solo el agente que necesitamos para esta demo
from agents.agente_contacts import AgenteContacts

def imprimir_titulo(texto):
    """Imprime un título con formato destacado"""
    print(f"\n{Back.BLUE}{Fore.WHITE}{Style.BRIGHT} {texto} {Style.RESET_ALL}")
    print(Fore.BLUE + "=" * 70 + Style.RESET_ALL)

def imprimir_subtitulo(texto):
    """Imprime un subtítulo con formato"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{texto}{Style.RESET_ALL}")
    print(Fore.CYAN + "-" * 50 + Style.RESET_ALL)

def imprimir_exito(texto):
    """Imprime un mensaje de éxito"""
    print(f"{Fore.GREEN}✓ {texto}{Style.RESET_ALL}")

def imprimir_error(texto):
    """Imprime un mensaje de error"""
    print(f"{Fore.RED}✗ {texto}{Style.RESET_ALL}")

def main():
    """Función principal de la demostración"""
    try:
        imprimir_titulo("DEMO DE AGENTE DE CONTACTOS - ARGENTINA")
        print("Esta demo muestra el flujo de búsqueda de información de contacto de vendedores en Argentina.")
        
        # Cargar variables de entorno necesarias
        from dotenv import load_dotenv
        load_dotenv()
        
        # Verificar que tenemos las claves necesarias
        google_api_key = os.getenv("GOOGLE_API_KEY")
        google_cse_id = os.getenv("GOOGLE_CSE_ID")
        
        if not google_api_key or not google_cse_id:
            imprimir_error("No se encontraron las variables de entorno necesarias (GOOGLE_API_KEY, GOOGLE_CSE_ID)")
            sys.exit(1)
        
        # Inicializar el agente de contactos
        imprimir_subtitulo("Inicializando Agente de Contactos")
        agente_contactos = AgenteContacts(google_api_key=google_api_key, google_cse_id=google_cse_id)
        imprimir_exito("Agente inicializado correctamente")
        
        # Lista de vendedores de ejemplo para Argentina
        vendedores_arg = [
            "Mercado Tech AR",
            "TecnoStore Argentina",
            "Garbarino",
            "Frávega",
            "Musimundo"
        ]
        
        # Permitir seleccionar un vendedor o ingresar uno personalizado
        print(f"\n{Fore.WHITE}Vendedores disponibles para búsqueda:{Style.RESET_ALL}")
        for i, vendedor in enumerate(vendedores_arg):
            print(f"{i+1}. {vendedor}")
        print(f"{len(vendedores_arg)+1}. Ingresar otro vendedor")
        
        # Solicitar selección
        while True:
            try:
                seleccion = int(input(f"\n{Fore.WHITE}Seleccione una opción (1-{len(vendedores_arg)+1}): {Style.RESET_ALL}"))
                if 1 <= seleccion <= len(vendedores_arg)+1:
                    break
                imprimir_error("Opción no válida")
            except ValueError:
                imprimir_error("Por favor ingrese un número")
        
        # Obtener el vendedor seleccionado
        if seleccion <= len(vendedores_arg):
            vendedor = vendedores_arg[seleccion-1]
        else:
            vendedor = input(f"\n{Fore.WHITE}Ingrese el nombre del vendedor a buscar: {Style.RESET_ALL}")
        
        # Buscar información de contacto
        imprimir_subtitulo(f"Buscando información de contacto para: {vendedor}")
        print(f"País: {Fore.YELLOW}Argentina{Style.RESET_ALL}")
        print(f"Estrategia de búsqueda: {Fore.YELLOW}Completa (Google + Maps){Style.RESET_ALL}")
        
        # Medir el tiempo de búsqueda
        inicio = time.time()
        
        # Realizar la búsqueda con parámetros específicos para Argentina
        resultado = agente_contactos.get_contact_info(
            business_name=vendedor,
            country="argentina",  # Especificar Argentina como país
            search_strategy="full",  # Usar búsqueda completa
            format_output=True  # Formatear salida
        )
        
        tiempo = time.time() - inicio
        
        # Mostrar resultados
        imprimir_subtitulo(f"Resultados encontrados en {tiempo:.2f} segundos")
        
        # Comprobar si hay información de contacto
        if not resultado or not any(resultado.values()):
            imprimir_error(f"No se encontró información de contacto para {vendedor}")
        else:
            # Mostrar la información básica
            print(f"{Fore.GREEN}{Style.BRIGHT}Información de contacto:{Style.RESET_ALL}\n")
            
            # Mostrar cada campo disponible
            for campo, valor in resultado.items():
                if valor and campo != "formatted_cards":
                    print(f"{campo.capitalize()}: {valor}")
            
            # Mostrar la tarjeta formateada si está disponible
            if resultado.get("formatted_cards") and resultado["formatted_cards"].get("plain_text"):
                imprimir_subtitulo("Tarjeta de contacto formateada")
                print(resultado["formatted_cards"]["plain_text"])
        
        print("\n")
        imprimir_titulo("FIN DE LA DEMOSTRACIÓN")
        
    except KeyboardInterrupt:
        print("\nOperación interrumpida por el usuario")
    except Exception as e:
        imprimir_error(f"Error inesperado: {str(e)}")
        logger.exception("Error en la ejecución")

if __name__ == "__main__":
    main()
