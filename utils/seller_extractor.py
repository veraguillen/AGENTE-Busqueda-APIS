"""
Módulo para extraer información de vendedores a partir de URLs de productos de MercadoLibre.
"""

import re
import time
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from agents.seller_db import SellerDatabase

# Configurar logging
logger = logging.getLogger(__name__)

class SellerExtractor:
    """
    Clase para extraer información de vendedores a partir de las URLs de los productos.
    Utiliza técnicas de web scraping y solicitudes a APIs públicas.
    """
    
    def __init__(self, user_agent: str = None, delay: float = 1.0):
        """
        Inicializa el extractor de vendedores.
        
        Args:
            user_agent: User-Agent para las solicitudes HTTP
            delay: Tiempo de espera entre solicitudes para evitar ser bloqueado
        """
        self.delay = delay
        self.session = requests.Session()
        
        if user_agent:
            self.user_agent = user_agent
        else:
            self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive'
        })
        
        # Base de datos para almacenar información de vendedores
        self.db = SellerDatabase()
        
    def _wait(self):
        """Espera un tiempo para evitar hacer solicitudes demasiado rápido"""
        time.sleep(self.delay)
        
    def extract_seller_from_product_url(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Extrae información del vendedor a partir de la URL del producto.
        
        Args:
            product_url: URL del producto en MercadoLibre
            
        Returns:
            Diccionario con información del vendedor o None si no se pudo extraer
        """
        if not product_url:
            logger.warning("URL de producto vacía")
            return None
            
        try:
            logger.info(f"Extrayendo información del vendedor para: {product_url}")
            
            # Limpiar URL
            product_url = product_url.strip().replace("&amp;", "&")
            
            # Limpiar y normalizar URL (puede haber caracteres extra)
            product_url = product_url.strip().replace('\t', '').replace('\n', '')
            if '"' in product_url:
                product_url = product_url.split('"')[0]
                
            logger.debug(f"URL normalizada: {product_url}")
                
            # Realizar solicitud HTTP
            response = self.session.get(product_url, timeout=15)
            self._wait()  # Esperar para no sobrecargar el servidor
            
            # Guardar HTML para debug si es necesario
            with open(f"debug_product_page_{int(time.time())}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            if response.status_code != 200:
                logger.error(f"Error al acceder a la URL del producto: {response.status_code}")
                return None
                
            # Analizar HTML para extraer información del vendedor
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar la sección del vendedor - hay varias formas posibles según la estructura de MercadoLibre
            seller_info = {}
            
            # Método 1: Sección de vendedor estándar (2023-2025)
            seller_section = soup.select_one('div.ui-pdp-seller__header, div.ui-pdp-seller-info')
            if seller_section:
                # Obtener nombre de vendedor
                seller_name_elem = seller_section.select_one('a.ui-pdp-action-modal__link, p.ui-pdp-seller__info-name, a.ui-pdp-seller__info-link, span.ui-pdp-seller__info-name')
                if seller_name_elem:
                    seller_info["nickname"] = seller_name_elem.text.strip()
                    seller_info["url"] = seller_name_elem.get('href', '')
                
                # Obtener reputación
                reputation_elem = seller_section.select_one('.ui-pdp-seller__status-info span, .ui-pdp-seller__info-reputation')
                if reputation_elem:
                    seller_info["reputation_level"] = reputation_elem.text.strip()
            
            # Método 2: Vendedor en formato de tienda oficial
            if not seller_info.get("nickname"):
                official_store = soup.select_one('a.ui-pdp-media__action-link, a.ui-pdp-official-store-link, div.ui-pdp-store__title a, div.ui-pdp-info__title a')
                if official_store:
                    seller_info["nickname"] = official_store.text.strip()
                    seller_info["url"] = official_store.get('href', '')
                    seller_info["official_store"] = True
            
            # Método 3: Buscar datos en scripts embebidos (formato JSON-LD)
            script_tags = soup.find_all('script', {'type': 'application/ld+json'})
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'seller' in data:
                        seller_data = data.get('seller', {})
                        if 'name' in seller_data and not seller_info.get("nickname"):
                            seller_info["nickname"] = seller_data.get('name')
                        if '@id' in seller_data and not seller_info.get("url"):
                            seller_info["url"] = seller_data.get('@id')
                except:
                    continue
            
            # Si tenemos URL del vendedor, extraer el ID
            if seller_info.get("url"):
                # Extraer ID del vendedor de la URL
                matches = re.search(r'\/perfil\/([^\/]+)', seller_info["url"])
                if matches:
                    seller_info["id"] = matches.group(1)
                else:
                    # Intentar otro formato de URL
                    url_parts = urlparse(seller_info["url"])
                    path_parts = url_parts.path.split('/')
                    if len(path_parts) >= 2:
                        seller_info["id"] = path_parts[-1]
            
            # Si tenemos suficiente información del vendedor, obtener datos adicionales
            if seller_info.get("id") or seller_info.get("url"):
                # Enriquecer con información adicional si es posible
                detailed_info = self.get_seller_details(seller_info)
                if detailed_info:
                    seller_info.update(detailed_info)
                
                # Agregar a la base de datos
                if seller_info:
                    self.db.add_seller(seller_info)
                    logger.info(f"Vendedor guardado en base de datos: {seller_info.get('nickname')}")
                
            return seller_info if seller_info else None
                
        except Exception as e:
            logger.error(f"Error extrayendo información del vendedor: {e}")
            return None
    
    def get_seller_details(self, seller_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtiene detalles adicionales del vendedor a partir de su página de perfil.
        
        Args:
            seller_info: Información básica del vendedor
            
        Returns:
            Diccionario con información detallada del vendedor
        """
        # Verificar si tenemos URL del vendedor
        seller_url = seller_info.get("url")
        if not seller_url:
            return {}
            
        try:
            logger.info(f"Obteniendo detalles del vendedor: {seller_url}")
            
            # Realizar solicitud HTTP
            response = self.session.get(seller_url, timeout=10)
            self._wait()
            
            if response.status_code != 200:
                return {}
                
            # Analizar HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraer información adicional
            additional_info = {}
            
            # Ubicación del vendedor
            location_elem = soup.select_one('p.card-subtitle, p.ui-seller-info__status-info, div.location-info p')
            if location_elem:
                additional_info["location"] = location_elem.text.strip()
            
            # Reputación / nivel
            reputation_elem = soup.select_one('div.seller-reputation span, div.reputation-data span, div.ui-seller-info__status-info span, span.seller-level')
            if reputation_elem:
                additional_info["reputation_level"] = reputation_elem.text.strip()
            
            # Datos de contacto (si están disponibles públicamente)
            contact_section = soup.select_one('section.seller-info')
            if contact_section:
                # Email (normalmente no visible por políticas de MercadoLibre)
                email_elem = contact_section.select_one('span.email')
                if email_elem:
                    additional_info["email"] = email_elem.text.strip()
                
                # Teléfono (normalmente no visible por políticas de MercadoLibre)
                phone_elem = contact_section.select_one('span.phone')
                if phone_elem:
                    additional_info["phone"] = phone_elem.text.strip()
                
                # Sitio web
                website_elem = contact_section.select_one('a[href^="http"]')
                if website_elem:
                    additional_info["website"] = website_elem.get('href', '')
            
            return additional_info
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles del vendedor: {e}")
            return {}
    
    def extract_multiple_sellers(self, products: List[Dict[str, Any]], save_to_db: bool = True) -> List[Dict[str, Any]]:
        """
        Procesa una lista de productos y extrae información de sus vendedores.
        
        Args:
            products: Lista de productos con URLs
            save_to_db: Si se debe guardar la información en la base de datos
            
        Returns:
            Lista de diccionarios con información de los vendedores
        """
        sellers = []
        
        for product in products:
            # Verificar si el producto tiene URL
            url = product.get("url")
            if not url:
                continue
                
            # Verificar si el vendedor ya existe en la base de datos
            seller_info = product.get("seller", {})
            seller_id = seller_info.get("id")
            
            if seller_id:
                existing_seller = self.db.get_seller_by_id(seller_id) if save_to_db else None
                if existing_seller:
                    # Actualizar producto con información del vendedor
                    if save_to_db:
                        self.db.add_product(product, seller_id, "")
                    sellers.append(existing_seller)
                    continue
            
            # Si no hay información del vendedor o no está en la base de datos, extraerla
            if seller_info.get("needs_extraction", True):
                extracted_seller = self.extract_seller_from_product_url(url)
                if extracted_seller:
                    # Actualizar producto con la información del vendedor extraída
                    product["seller"] = extracted_seller
                    
                    # Guardar en base de datos si es necesario
                    if save_to_db and extracted_seller.get("id"):
                        self.db.add_product(product, extracted_seller["id"], "")
                    
                    sellers.append(extracted_seller)
        
        return sellers
    
    def close(self):
        """Cierra recursos"""
        if self.db:
            self.db.close()
