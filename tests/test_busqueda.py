#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para probar el agente de búsqueda de productos
"""

import os
import sys
import logging
import json
from pprint import pprint
from dotenv import load_dotenv

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,  # Cambiado a DEBUG para más detalles
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('busqueda.log')
    ]
)
logger = logging.getLogger(__name__)

def verificar_variables_entorno():
    """Verifica que todas las variables de entorno requeridas estén configuradas."""
    required_vars = [
        "RAPIDAPI_KEY", 
        "RAPIDAPI_HOST",
        "GOOGLE_API_KEY", 
        "GOOGLE_CSE_ID"
    ]
    
    faltantes = [var for var in required_vars if not os.environ.get(var)]
    
    if faltantes:
        logger.error(f"Faltan variables de entorno requeridas: {', '.join(faltantes)}")
        logger.info("Asegúrate de configurar estas variables en el archivo .env")
        return False
    
    logger.info("Todas las variables de entorno requeridas están configuradas.")
    return True

def probar_busqueda(query, country_code="AR", max_pages=1):
    """
    Prueba la búsqueda de productos con los parámetros dados.
    
    Args:
        query: Término de búsqueda
        country_code: Código de país (ej: 'AR', 'MX')
        max_pages: Número de páginas a buscar (máx. 3 para pruebas)
    """
    try:
        # Importar el orquestador (esto cargará todos los agentes)
        logger.info("Importando el orquestador...")
        from app.orquestador import Orquestador
        
        # Crear instancia del orquestador
        logger.info("Inicializando el orquestador...")
        orquestador = Orquestador()
        
        # Realizar la búsqueda
        logger.info(f"\nRealizando búsqueda: '{query}' en {country_code} (páginas: {max_pages})")
        resultados = orquestador.buscar_productos(
            query=query,
            country_code=country_code,
            max_pages=max_pages
        )
        
        # Mostrar resultados
        logger.info("\n" + "="*80)
        logger.info("RESULTADOS DE LA BÚSQUEDA")
        logger.info("="*80)
        
        if not resultados:
            logger.warning("No se encontraron resultados o hubo un error.")
            return False
            
        if "error" in resultados:
            logger.error(f"Error en la búsqueda: {resultados['error']}")
            return False
            
        # Mostrar resumen
        if "top_products" in resultados and resultados["top_products"]:
            logger.info(f"Se encontraron {len(resultados['top_products'])} productos principales:")
            
            # Guardar resultados en un archivo para revisión
            results_path = os.path.join(os.path.dirname(__file__), '..', 'resultados_busqueda.json')
            try:
                with open(results_path, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, indent=2, ensure_ascii=False, default=str)
                logger.info(f"Resultados guardados en: {os.path.abspath(results_path)}")
            except Exception as e:
                logger.error(f"Error al guardar resultados: {str(e)}")
                logger.error(traceback.format_exc())
            
            # Mostrar los primeros 3 productos como ejemplo
            for idx, producto in enumerate(resultados["top_products"][:3], 1):
                logger.info(f"\n{idx}. {producto.get('product_title', 'Sin título')}")
                logger.info(f"   Precio: {producto.get('price', 'N/A')} {producto.get('currency', '')}")
                logger.info(f"   Condición: {producto.get('condition', 'N/A')}")
                logger.info(f"   URL: {producto.get('listing_url', 'N/A')}")
                
                if "seller" in producto:
                    seller = producto["seller"]
                    logger.info(f"   Vendedor: {seller.get('nickname', 'N/A')}")
                    
                    if "contact" in seller:
                        contacto = seller["contact"]
                        if "whatsapp_url" in contacto:
                            logger.info(f"   WhatsApp: {contacto['whatsapp_url']}")
            
            logger.info("\n¡Búsqueda completada exitosamente!")
            return True
        else:
            logger.warning("No se encontraron productos que coincidan con la búsqueda.")
            return False
            
    except Exception as e:
        logger.error(f"Error al realizar la búsqueda: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("="*80)
    print("PRUEBA DE BÚSQUEDA DE PRODUCTOS")
    print("="*80)
    
    # Verificar variables de entorno
    if not verificar_variables_entorno():
        print("\n⚠️  No se pueden realizar pruebas sin las variables de entorno necesarias.")
        print("Por favor, configura el archivo .env con las credenciales requeridas.")
        sys.exit(1)
    
    # Parámetros de búsqueda (puedes modificarlos según necesites)
    query = "smartphone samsung"
    country_code = "AR"  # Argentina
    max_pages = 1  # Número de páginas a buscar (1-3 para pruebas)
    
    print(f"\n🔍 Realizando búsqueda: '{query}' en {country_code}")
    print("Por favor espera, esto puede tomar unos segundos...\n")
    
    # Ejecutar la prueba
    exito = probar_busqueda(query, country_code, max_pages)
    
    # Mostrar resultado final
    print("\n" + "="*80)
    if exito:
        print("✅ ¡Prueba completada exitosamente!")
        print("Revisa el archivo 'resultados_busqueda.json' para ver los resultados completos.")
    else:
        print("❌ La prueba no se completó correctamente.")
        print("Revisa el archivo 'busqueda.log' para más detalles.")
    print("="*80)
