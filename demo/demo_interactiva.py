#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo Interactiva de Búsqueda y Contactos
Permite al usuario buscar productos en MercadoLibre y obtener información de contacto
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

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

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

def buscar_y_mostrar_contactos():
    """Función principal para buscar productos y mostrar contactos"""
    try:
        # Importar orquestador y agente de contactos directamente
        from app.orquestador import Orquestador
        from agents.agente_contacts import AgenteContacts
        
        # Inicializar orquestador (maneja toda la lógica de búsqueda)
        imprimir_titulo("SISTEMA DE BÚSQUEDA Y CONTACTO")
        imprimir_subtitulo("Inicializando sistema...")
        
        orquestador = Orquestador()
        imprimir_exito("Sistema listo para búsquedas")
        
        # Bucle principal
        while True:
            # Menú principal
            imprimir_subtitulo("¿Qué desea hacer?")
            print("1. Buscar productos")
            print("2. Buscar información de contacto directamente")
            print("3. Salir")
            
            opcion = input(f"\n{Fore.WHITE}Seleccione una opción (1-3): {Style.RESET_ALL}")
            
            if opcion == "1":
                # Buscar productos
                query = input(f"\n{Fore.WHITE}¿Qué producto desea buscar?: {Style.RESET_ALL}")
                if not query:
                    imprimir_error("Por favor ingrese un término de búsqueda válido")
                    continue
                
                # País para la búsqueda
                imprimir_subtitulo("Seleccione el país")
                print("1. Argentina")
                print("2. México")
                print("3. Brasil")
                
                pais_opcion = input(f"\n{Fore.WHITE}Seleccione un país (1-3): {Style.RESET_ALL}")
                
                if pais_opcion == "1":
                    pais = "ar"
                elif pais_opcion == "2":
                    pais = "mx"
                elif pais_opcion == "3":
                    pais = "br"
                else:
                    pais = "ar"  # Por defecto Argentina
                
                imprimir_subtitulo(f"Buscando '{query}' en MercadoLibre ({pais.upper()})...")
                inicio = time.time()
                
                # Ejecutar búsqueda
                resultados = orquestador.buscar_productos(query, country_code=pais)
                
                tiempo = time.time() - inicio
                
                # Verificar resultados
                if resultados['status'] != 'success' or not resultados.get('top_products'):
                    imprimir_error(f"No se encontraron productos: {resultados.get('message', 'Sin detalles')}")
                    continue
                
                productos = resultados['top_products']
                imprimir_exito(f"Búsqueda completada en {tiempo:.2f} segundos")
                imprimir_exito(f"Se encontraron {len(productos)} productos destacados")
                
                # Mostrar productos
                imprimir_subtitulo("PRODUCTOS ENCONTRADOS")
                max_display = min(len(productos), 5)  # Mostrar máximo 5 productos
                
                for i in range(max_display):
                    imprimir_producto(i, productos[i])
                
                # Preguntar qué producto consultar
                prod_idx = input(f"\n{Fore.WHITE}Número del producto para ver información de contacto (1-{max_display}) o 0 para volver: {Style.RESET_ALL}")
                
                try:
                    idx = int(prod_idx) - 1
                    if idx == -1:
                        continue  # Volver al menú principal
                    
                    if 0 <= idx < max_display:
                        producto = productos[idx]
                        
                        # Obtener información del vendedor
                        vendedor = "Desconocido"
                        if isinstance(producto.get('seller'), dict) and producto['seller'].get('nickname'):
                            vendedor = producto['seller']['nickname']
                        elif isinstance(producto.get('seller'), str):
                            if producto['seller'].startswith("Por "):
                                vendedor = producto['seller'][4:]
                            else:
                                vendedor = producto['seller']
                        
                        imprimir_subtitulo(f"Buscando información de contacto para: {vendedor}")
                        
                        # Buscar información de contacto usando el orquestador
                        contacto = orquestador.obtener_info_contacto(producto)
                        
                        # Mostrar información de contacto
                        if contacto:
                            imprimir_exito("Información de contacto encontrada:")
                            
                            if contacto.get('formatted_contact_cards') and contacto['formatted_contact_cards'].get('plain_text'):
                                print(contacto['formatted_contact_cards']['plain_text'])
                            else:
                                for campo, valor in contacto.get('contact_info', {}).items():
                                    if valor:
                                        print(f"{campo.capitalize()}: {valor}")
                        else:
                            imprimir_error(f"No se pudo obtener información de contacto para {vendedor}")
                    else:
                        imprimir_error("Número de producto no válido")
                except ValueError:
                    imprimir_error("Por favor ingrese un número válido")
            
            elif opcion == "2":
                # Buscar información de contacto directamente
                nombre_negocio = input(f"\n{Fore.WHITE}Nombre del negocio o vendedor: {Style.RESET_ALL}")
                if not nombre_negocio:
                    imprimir_error("Por favor ingrese un nombre de negocio válido")
                    continue
                
                # País para la búsqueda
                imprimir_subtitulo("Seleccione el país")
                print("1. Argentina")
                print("2. México")
                print("3. Brasil")
                print("4. Otro")
                
                pais_opcion = input(f"\n{Fore.WHITE}Seleccione un país (1-4): {Style.RESET_ALL}")
                
                if pais_opcion == "1":
                    pais = "argentina"
                elif pais_opcion == "2":
                    pais = "mexico"
                elif pais_opcion == "3":
                    pais = "brasil"
                elif pais_opcion == "4":
                    pais = input(f"\n{Fore.WHITE}Ingrese el nombre del país: {Style.RESET_ALL}")
                else:
                    pais = "argentina"  # Por defecto Argentina
                
                imprimir_subtitulo(f"Buscando información de contacto para: {nombre_negocio}")
                print(f"País: {pais.capitalize()}")
                
                # Inicializar agente de contactos directamente
                try:
                    google_api_key = os.getenv("GOOGLE_API_KEY")
                    google_cse_id = os.getenv("GOOGLE_CSE_ID")
                    
                    if not google_api_key or not google_cse_id:
                        imprimir_error("No se encontraron las variables de entorno necesarias (GOOGLE_API_KEY, GOOGLE_CSE_ID)")
                        continue
                    
                    agente_contactos = AgenteContacts(google_api_key=google_api_key, google_cse_id=google_cse_id)
                    
                    # Buscar información de contacto
                    inicio = time.time()
                    resultado = agente_contactos.get_contact_info(
                        seller_name=nombre_negocio,
                        search_strategy="all",
                        format_results=True
                    )
                    tiempo = time.time() - inicio
                    
                    # Mostrar resultados
                    imprimir_subtitulo(f"Resultados encontrados en {tiempo:.2f} segundos")
                    
                    if resultado and any(v for k, v in resultado.items() if k != "formatted_cards"):
                        imprimir_exito("Información de contacto encontrada:")
                        
                        # Mostrar tarjeta formateada si está disponible
                        if resultado.get("formatted_cards") and resultado["formatted_cards"].get("plain_text"):
                            print(resultado["formatted_cards"]["plain_text"])
                        else:
                            # Mostrar la información básica
                            for campo, valor in resultado.items():
                                if valor and campo != "formatted_cards":
                                    print(f"{campo.capitalize()}: {valor}")
                    else:
                        imprimir_error(f"No se encontró información de contacto para {nombre_negocio}")
                
                except Exception as e:
                    imprimir_error(f"Error al buscar información de contacto: {str(e)}")
            
            elif opcion == "3":
                # Salir
                imprimir_titulo("GRACIAS POR USAR EL SISTEMA")
                break
            
            else:
                imprimir_error("Opción no válida")
                
            # Pausa antes de continuar
            input(f"\n{Fore.WHITE}Presione Enter para continuar...{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        imprimir_error("\nOperación interrumpida por el usuario")
    except Exception as e:
        imprimir_error(f"Error inesperado: {str(e)}")
        logger.exception("Error en la ejecución")

if __name__ == "__main__":
    buscar_y_mostrar_contactos()
