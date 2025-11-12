#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo simplificada del flujo completo de búsqueda y extracción de información de contacto.
"""

import os
import sys
import json
import logging
from colorama import init, Fore, Style

# Inicializar colorama para colores en consola
init()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Asegurar que los módulos del proyecto estén disponibles
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Importar el orquestador
from app.orquestador import Orquestador

def banner(mensaje):
    """Muestra un banner con el mensaje indicado"""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT} {mensaje}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{Style.BRIGHT}{'='*70}{Style.RESET_ALL}\n")

def mostrar_producto(idx, producto):
    """Muestra la información de un producto con formato simple"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[Producto #{idx+1}]{Style.RESET_ALL}")
    
    # Título
    titulo = producto.get('title', 'Sin título')
    print(f"{Fore.WHITE}{Style.BRIGHT}{titulo}{Style.RESET_ALL}")
    
    # Precio
    precio = producto.get('price', 'No disponible')
    if isinstance(precio, (int, float)):
        print(f"Precio: ${precio:,.2f}")
    else:
        print(f"Precio: {precio}")
    
    # Vendedor
    vendedor = "No disponible"
    if isinstance(producto.get('seller'), dict) and producto['seller'].get('nickname'):
        vendedor = producto['seller']['nickname']
    elif isinstance(producto.get('seller'), str):
        vendedor = producto['seller']
    print(f"Vendedor: {vendedor}")
    
    # URL
    url = producto.get('permalink', 'No disponible')
    print(f"URL: {url}")
    
    # Información de contacto
    if 'formatted_contact_cards' in producto:
        print(f"\n{Fore.GREEN}--- Información de contacto ---{Style.RESET_ALL}")
        print(producto['formatted_contact_cards']['plain_text'])

def main():
    banner("DEMO SIMPLE: BÚSQUEDA Y CONTACTOS")
    
    print("Inicializando orquestador...")
    orquestador = Orquestador()
    print(f"{Fore.GREEN}✓ Orquestador inicializado correctamente{Style.RESET_ALL}")
    
    # Término de búsqueda
    termino = input("Ingrese término de búsqueda: ")
    if not termino:
        termino = "notebook dell"  # Valor por defecto
        print(f"Usando término de búsqueda por defecto: {termino}")
    
    print(f"\n{Fore.CYAN}Buscando productos para '{termino}'...{Style.RESET_ALL}")
    resultados = orquestador.buscar_productos(termino)
    
    # Verificar resultados
    if resultados['status'] != 'success':
        print(f"\n{Fore.RED}Error en la búsqueda: {resultados.get('message', 'Sin detalles')}{Style.RESET_ALL}")
        return
    
    productos = resultados.get('top_products', [])
    if not productos:
        print(f"\n{Fore.YELLOW}No se encontraron productos para '{termino}'{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.GREEN}✓ Se encontraron {len(productos)} productos{Style.RESET_ALL}")
    
    # Mostrar productos y sus datos de contacto
    banner("RESULTADOS ENCONTRADOS")
    
    for i, producto in enumerate(productos[:5]):  # Mostrar solo los 5 primeros
        mostrar_producto(i, producto)
    
    # Opción para ver detalles adicionales
    while True:
        print("\n1. Ver más detalles de un producto")
        print("2. Realizar otra búsqueda")
        print("3. Salir")
        
        opcion = input("\nSeleccione una opción (1-3): ")
        
        if opcion == "1":
            try:
                idx = int(input(f"Número de producto (1-{min(len(productos), 5)}): ")) - 1
                if 0 <= idx < len(productos):
                    banner(f"DETALLES COMPLETOS - PRODUCTO #{idx+1}")
                    
                    # Mostrar detalles completos incluyendo información de contacto
                    producto = productos[idx]
                    mostrar_producto(idx, producto)
                    
                    # Mostrar datos de contacto en formato JSON para depuración
                    print(f"\n{Fore.CYAN}Datos técnicos de contacto:{Style.RESET_ALL}")
                    if producto.get('contact_info'):
                        print(json.dumps(producto['contact_info'], indent=2))
                    else:
                        print("No hay datos de contacto disponibles")
                else:
                    print(f"{Fore.RED}Número de producto fuera de rango{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Por favor, ingrese un número válido{Style.RESET_ALL}")
        
        elif opcion == "2":
            main()  # Reiniciar el flujo
            return
        
        elif opcion == "3":
            print("\nFin de la demostración.")
            return
        
        else:
            print(f"{Fore.YELLOW}Opción no válida. Intente nuevamente.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario")
    except Exception as e:
        print(f"\n{Fore.RED}Error inesperado: {str(e)}{Style.RESET_ALL}")
