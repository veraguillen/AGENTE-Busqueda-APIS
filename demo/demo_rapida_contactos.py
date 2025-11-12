#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo rápida del Agente de Contactos para Argentina
Script simple que muestra el funcionamiento del agente de contactos
"""

import os
import sys
import json
import dotenv
import logging
from colorama import init, Fore, Style, Back

# Inicializar colorama
init()

# Configurar logging básico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
dotenv.load_dotenv()

# Asegurar que podemos acceder a los módulos
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importar agente de contactos
from agents.agente_contacts import AgenteContacts

def print_color(text, color=Fore.WHITE, bright=False):
    """Imprime texto con color"""
    if bright:
        print(f"{color}{Style.BRIGHT}{text}{Style.RESET_ALL}")
    else:
        print(f"{color}{text}{Style.RESET_ALL}")

def main():
    """Función principal"""
    print_color("DEMO DE AGENTE DE CONTACTOS - ARGENTINA", Fore.BLUE, True)
    print("-" * 50)
    
    # Verificar API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not google_api_key or not google_cse_id:
        print_color("Error: No se encontraron las variables GOOGLE_API_KEY o GOOGLE_CSE_ID", Fore.RED)
        return
    
    # Crear instancia del agente
    print_color("Inicializando agente de contactos...", Fore.CYAN)
    agente = AgenteContacts(google_api_key=google_api_key, google_cse_id=google_cse_id)
    print_color("Agente inicializado correctamente", Fore.GREEN)
    
    # Lista de vendedores para buscar (en Argentina)
    vendedores = [
        "Garbarino",
        "Frávega",
        "Musimundo"
    ]
    
    # Buscar información para cada vendedor
    for vendedor in vendedores:
        print_color(f"\nBuscando información de contacto para: {vendedor}", Fore.YELLOW, True)
        print(f"País: Argentina | Estrategia: búsqueda completa")
        
        try:
            # Obtener información de contacto
            info = agente.get_contact_info(
                business_name=vendedor,
                country="argentina",
                search_strategy="full",
                format_output=True
            )
            
            # Mostrar resultados
            if info and any(info.values()):
                print_color("✓ Información encontrada:", Fore.GREEN)
                
                # Mostrar datos básicos
                for campo, valor in info.items():
                    if valor and campo != "formatted_cards":
                        print(f"  - {campo.capitalize()}: {valor}")
                
                # Mostrar tarjeta formateada si está disponible
                if info.get("formatted_cards") and info["formatted_cards"].get("plain_text"):
                    print_color("\nTarjeta de contacto:", Fore.CYAN)
                    print(info["formatted_cards"]["plain_text"])
            else:
                print_color("✗ No se encontró información de contacto", Fore.RED)
        
        except Exception as e:
            print_color(f"Error al buscar información: {str(e)}", Fore.RED)
    
    print_color("\nDemostración completada.", Fore.BLUE, True)

if __name__ == "__main__":
    main()
