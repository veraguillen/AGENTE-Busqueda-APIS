"""
Módulo para buscar productos en MercadoLibre mediante web scraping.
Reemplaza la función de búsqueda por API con una versión basada en scraping web.
"""

import time
import logging
import requests
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

# Configurar logging
logger = logging.getLogger(__name__)

class MercadoLibreWebSearch:
    """
    Clase para buscar productos directamente en el sitio web de MercadoLibre
    utilizando técnicas de web scraping.
    """
    
    def __init__(self, delay: float = 1.0):
        """
        Inicializa el buscador web.
        
        Args:
            delay: Tiempo de espera entre solicitudes para evitar ser bloqueado
        """
        self.delay = delay
        self.session = requests.Session()
        
        # Configurar headers para simular un navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        })
    
    def _wait(self):
        """Espera un tiempo para evitar hacer solicitudes demasiado rápido"""
        time.sleep(self.delay)
    
    def search(self, query: str, country: str = 'ar', max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Busca productos en MercadoLibre directamente en el sitio web.
        
        Args:
            query: Término de búsqueda
            country: Código del país (ar, mx, cl, etc.)
            max_pages: Máximo número de páginas a procesar
            
        Returns:
            Lista de productos encontrados
        """
        products = []
        country_domain_map = {
            'ar': 'com.ar',
            'mx': 'com.mx',
            'br': 'com.br',
            'cl': 'cl',
            'co': 'com.co',
            'pe': 'com.pe',
            've': 'com.ve',
            'ec': 'com.ec',
            'uy': 'com.uy',
            'bo': 'com.bo',
            'py': 'com.py',
            'do': 'com.do',
            'pa': 'com.pa',
            'cr': 'co.cr',
            'gt': 'com.gt',
            'sv': 'com.sv',
            'hn': 'com.hn',
            'ni': 'com.ni',
            'pt': 'pt',
            'cu': 'com.cu',
        }
        
        domain = country_domain_map.get(country.lower(), 'com.ar')
        base_url = f"https://listado.mercadolibre.{domain}/{quote_plus(query)}"
        
        logger.info(f"Iniciando búsqueda web en MercadoLibre: {query} en {country}")
        
        try:
            for page in range(1, max_pages + 1):
                page_url = f"{base_url}_Desde_{(page-1)*50+1}" if page > 1 else base_url
                
                logger.info(f"Procesando página {page}: {page_url}")
                
                try:
                    response = self.session.get(page_url, timeout=15)
                    self._wait()  # Esperar entre solicitudes
                    
                    if response.status_code != 200:
                        logger.error(f"Error al obtener la página {page}: Status {response.status_code}")
                        break
                    
                    # Parsear HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Obtener lista de productos
                    product_listings = soup.select('li.ui-search-layout__item')
                    
                    if not product_listings:
                        # Formato alternativo para algunos países
                        product_listings = soup.select('div.ui-search-result')
                    
                    if not product_listings:
                        logger.warning(f"No se encontraron productos en la página {page}.")
                        break
                    
                    logger.info(f"Encontrados {len(product_listings)} productos en la página {page}")
                    
                    # Procesar cada producto
                    for listing in product_listings:
                        product_data = self._extract_product_data(listing)
                        if product_data:
                            products.append(product_data)
                            logger.debug(f"Producto procesado: {product_data.get('title', 'Sin título')}")
                    
                    # Verificar si hay más páginas
                    next_page = soup.select_one('a.andes-pagination__link[title="Siguiente"]')
                    if not next_page:
                        logger.info("No hay más páginas disponibles")
                        break
                        
                except Exception as e:
                    logger.error(f"Error procesando la página {page}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error general durante la búsqueda: {e}", exc_info=True)
        
        logger.info(f"Búsqueda completada. Encontrados {len(products)} productos en total.")
        return products
    
    def _extract_product_data(self, product_element: Any) -> Optional[Dict[str, Any]]:
        """
        Extrae la información relevante de un elemento producto en el HTML.
        
        Args:
            product_element: Elemento HTML que representa un producto
            
        Returns:
            Diccionario con los datos extraídos del producto
        """
        try:
            # Extraer URL del producto
            link_element = product_element.select_one('a.ui-search-link, a.ui-search-item__group__element, a.ui-search-result__content')
            if not link_element:
                # Buscar cualquier enlace dentro del elemento producto
                link_element = product_element.select_one('a[href]')
            
            if not link_element:
                return None
                
            product_url = link_element.get('href', '')
            
            # Limpiar y normalizar la URL
            if product_url:
                # Quitar fragmentos y parámetros de consulta
                product_url = product_url.split('#')[0]
                
                # Verificar si hay parámetros malformados (URL truncada)
                if '"' in product_url or '?' in product_url and not '&' in product_url and not '=' in product_url:
                    product_url = product_url.split('?')[0]
                    
                # Corregir URLs dobles (un problema común en el scraping)
                if product_url.count('https://') > 1:
                    product_url = 'https://' + product_url.split('https://')[-1]
            
            # Extraer ID del producto
            product_id = None
            if 'MLA' in product_url or '/p/' in product_url:
                import re
                # Intentar extraer ID (formato MLA123456 o similar)
                id_match = re.search(r'(MLA|MLB|MLM|MLC|MCO|MPE|MLV|MEC|MLU|MBO|MPY|MRD|MPA|MCR|MGT|MSV|MHN|MPT|MCU)-?\d+', product_url)
                if id_match:
                    product_id = id_match.group(0)
                else:
                    # Formato alternativo: extraer de la URL
                    id_parts = product_url.split('-')
                    if len(id_parts) > 1:
                        product_id = id_parts[-1]
            
            # Extraer título
            title_element = product_element.select_one('h2.ui-search-item__title, .ui-search-item__title, .ui-search-result__title')
            
            title = title_element.text.strip() if title_element else "Sin título"
            
            # Extraer precio
            price_element = product_element.select_one('span.price-tag-fraction')
            price = 0
            
            if price_element:
                price_text = price_element.text.strip().replace('.', '').replace(',', '.')
                try:
                    price = float(price_text)
                except ValueError:
                    price = 0
            
            # Extraer moneda
            currency_element = product_element.select_one('span.price-tag-symbol')
            currency = currency_element.text.strip() if currency_element else "$"
            
            # Extraer información del vendedor (limitada en la página de búsqueda)
            seller_info = {}
            seller_element = product_element.select_one('p.ui-search-official-store-label')
            
            if seller_element:
                seller_info = {
                    "nickname": seller_element.text.strip().replace("por ", ""),
                    "official_store": True,
                    "needs_extraction": True  # Indicar que necesitamos extraer más información
                }
            else:
                seller_info = {
                    "needs_extraction": True
                }
            
            # Extraer imagen (thumbnail)
            img_element = product_element.select_one('img.ui-search-result-image__element, img[data-src]')
            thumbnail = ""
            if img_element:
                thumbnail = img_element.get('src', '') or img_element.get('data-src', '')
            
            # Construir objeto de producto
            product = {
                "id": product_id,
                "title": title,
                "price": price,
                "currency": currency,
                "url": product_url,
                "thumbnail": thumbnail,
                "seller": seller_info,
                "source": "web_scraping",
                "condition": self._extract_condition(product_element)
            }
            
            return product
            
        except Exception as e:
            logger.error(f"Error extrayendo datos del producto: {e}")
            return None
    
    def _extract_condition(self, product_element: Any) -> str:
        """
        Extrae la condición del producto (nuevo, usado, etc.)
        
        Args:
            product_element: Elemento HTML que representa un producto
            
        Returns:
            String con la condición del producto
        """
        condition_element = product_element.select_one('span.ui-search-item__condition')
        if condition_element:
            condition = condition_element.text.strip().lower()
            if 'nuevo' in condition:
                return 'new'
            elif 'usado' in condition:
                return 'used'
            else:
                return condition
        return 'unknown'
