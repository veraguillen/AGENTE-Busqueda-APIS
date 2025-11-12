#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demostración integrada del sistema de búsqueda en MercadoLibre y contactos de vendedores.
Este script muestra el flujo completo de:
1. Búsqueda de productos en MercadoLibre
2. Extracción de información de vendedores
3. Búsqueda y formateo de información de contacto
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

def imprimir_producto(idx, producto):
    """Imprime la información de un producto con formato"""
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}[#{idx+1}] {producto.get('title', 'Sin título')}{Style.RESET_ALL}")
    
    # Mostrar precio
    precio = producto.get('price')
    if isinstance(precio, (int, float)):
        print(f"Precio: ${precio:,.2f}")
    else:
        print(f"Precio: {precio}")
    
    # Mostrar vendedor con formato especial
    vendedor = "No disponible"
    if isinstance(producto.get('seller'), dict) and producto['seller'].get('nickname'):
        vendedor = producto['seller']['nickname']
    elif isinstance(producto.get('seller'), str):
        if producto['seller'].startswith("Por "):
            vendedor = producto['seller'][4:]
        else:
            vendedor = producto['seller']
    
    # Añadir color al vendedor para destacarlo
    print(f"Vendedor: {Fore.GREEN}{Style.BRIGHT}{vendedor}{Style.RESET_ALL}")
    
    # Mostrar URL
    url = producto.get('permalink')
    if url:
        print(f"URL: {url}")
    
    # Mostrar si tiene información de contacto disponible
    tiene_contacto = bool(producto.get('contact_info') and any(producto['contact_info'].values()))
    if tiene_contacto:
        print(f"{Fore.CYAN}✓ Información de contacto disponible{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}? Se buscará información de contacto al seleccionar{Style.RESET_ALL}")

def main():
    """Función principal de la demostración"""
    try:
        imprimir_titulo("SISTEMA DE BÚSQUEDA Y CONTACTO - DEMO INTEGRADA")
        
        # Importar e inicializar el orquestador
        imprimir_subtitulo("Inicializando sistema...")
        from app.orquestador import Orquestador
        orquestador = Orquestador()
        imprimir_exito("Sistema listo para usar")
        
        # Solicitar término de búsqueda
        while True:
            query = input(f"\n{Fore.WHITE}Ingrese término de búsqueda (o 'salir'): {Style.RESET_ALL}")
            if query.lower() in ['salir', 'exit', 'q', 'quit']:
                break
            
            if not query:
                imprimir_error("Por favor ingrese un término de búsqueda válido")
                continue
            
            # Realizar la búsqueda con medición de tiempo
            imprimir_subtitulo(f"Buscando '{query}' en MercadoLibre...")
            inicio = time.time()
            
            # Ejecutar la búsqueda principal
            resultados = orquestador.buscar_productos(query)
            
            tiempo = time.time() - inicio
            
            # Verificar si la búsqueda fue exitosa
            if resultados['status'] != 'success':
                imprimir_error(f"Error en la búsqueda: {resultados.get('message', 'Sin detalles')}")
                continue
            
            # Mostrar estadísticas de la búsqueda
            productos = resultados.get('top_products', [])
            if not productos:
                imprimir_error("No se encontraron productos para su búsqueda")
                continue
            
            imprimir_exito(f"Búsqueda completada en {tiempo:.2f} segundos")
            imprimir_exito(f"Se encontraron {len(productos)} productos destacados")
            
            # Mostrar resultados
            imprimir_titulo("PRODUCTOS ENCONTRADOS")
            
            # Mostrar los 5 primeros productos
            for i, producto in enumerate(productos[:5]):
                imprimir_producto(i, producto)
            
            # Menú de opciones
            while True:
                print(f"\n{Fore.WHITE}{Style.BRIGHT}Opciones:{Style.RESET_ALL}")
                print("1. Ver información detallada de contacto")
                print("2. Realizar otra búsqueda")
                print("3. Salir")
                
                opcion = input(f"\n{Fore.WHITE}Seleccione una opción (1-3): {Style.RESET_ALL}")
                
                if opcion == "1":
                    # Mostrar información de contacto de un producto
                    try:
                        idx = int(input(f"{Fore.WHITE}Número del producto (1-{min(len(productos), 5)}): {Style.RESET_ALL}")) - 1
                        if 0 <= idx < min(len(productos), 5):
                            producto = productos[idx]
                            
                            # Extraer información del vendedor
                            vendedor = "No disponible"
                            if isinstance(producto.get('seller'), dict) and producto['seller'].get('nickname'):
                                vendedor = producto['seller']['nickname']
                            elif isinstance(producto.get('seller'), str):
                                if producto['seller'].startswith("Por "):
                                    vendedor = producto['seller'][4:]
                                else:
                                    vendedor = producto['seller']
                                    
                            # Si sigue siendo No disponible pero hay ID, usarlo
                            if vendedor == "No disponible" and isinstance(producto.get('seller'), dict) and producto['seller'].get('id'):
                                vendedor = f"ID: {producto['seller']['id']}"
                            
                            imprimir_titulo(f"INFORMACIÓN DE CONTACTO - {vendedor}")
                            
                            # Mostrar la tarjeta de contacto formateada si existe
                            if producto.get('formatted_contact_cards'):
                                print(producto['formatted_contact_cards']['plain_text'])
                            else:
                                # Mostrar la información de contacto básica
                                info_contacto = producto.get('contact_info', {})
                                if info_contacto and any(info_contacto.values()):
                                    for campo, valor in info_contacto.items():
                                        if valor:
                                            print(f"{campo.capitalize()}: {valor}")
                                else:
                                    print(f"{Fore.RED}No se encontró información de contacto para el vendedor {Fore.WHITE}{Style.BRIGHT}{vendedor}{Style.RESET_ALL}")
                                    print(f"Esto puede deberse a que el vendedor no tiene información pública disponible.")
                            
                            # Mostrar enlaces adicionales
                            if producto.get('whatsapp_link'):
                                print(f"\n{Fore.GREEN}Link de WhatsApp: {producto['whatsapp_link']}{Style.RESET_ALL}")
                        else:
                            imprimir_error("Número de producto fuera de rango")
                    except ValueError:
                        imprimir_error("Por favor ingrese un número válido")
                
                elif opcion == "2":
                    # Salir al bucle de búsqueda
                    break
                
                elif opcion == "3":
                    # Salir del programa
                    return
                
                else:
                    imprimir_error("Opción no válida")
        
        imprimir_titulo("FIN DE LA DEMOSTRACIÓN")
        
    except KeyboardInterrupt:
        print("\nOperación interrumpida por el usuario")
    except Exception as e:
        imprimir_error(f"Error inesperado: {str(e)}")
        logger.exception("Error en la ejecución")

if __name__ == "__main__":
    main()
