"""
Agente para búsqueda en Google Custom Search.
Este agente se encarga de buscar información de contacto de vendedores.
Utiliza el APIClient centralizado para todas las peticiones HTTP.
"""
import re
import logging
from typing import Dict, Optional, Any

# Importar el APIClient centralizado
from utils.api_client import APIClient

# Configurar logging para este módulo
logger = logging.getLogger(__name__)

class AgenteGoogle:
    """Agente especializado en búsquedas en Google para información de contacto."""
    
    # URL base de la API de Google Custom Search
    GOOGLE_API_HOST = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, google_api_key: str, google_cse_id: str, 
                 api_client: Optional[APIClient] = None, 
                 cache=None, 
                 monitor=None):
        """
        Inicializa el agente con las credenciales de Google Custom Search.
        
        Args:
            google_api_key: Clave API de Google
            google_cse_id: ID del motor de búsqueda personalizado
            api_client: Instancia de APIClient (opcional, se crea una por defecto)
            cache: Objeto cache para almacenar resultados (opcional)
            monitor: Objeto para monitoreo y métricas (opcional)
        """
        self.api_key = google_api_key
        self.cse_id = google_cse_id
        self.cache = cache
        self.monitor = monitor
        self.contact_cache = {}  # Caché en memoria para evitar búsquedas repetidas
        
        # Usar el APIClient proporcionado o crear uno nuevo
        self.api_client = api_client or APIClient(
            default_timeout=30,
            max_retries=3
        )
        
        # Configurar headers comunes para las peticiones a Google
        self.api_client.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        logger.info("AgenteGoogle inicializado correctamente.")
    
    def search_seller_contacts(self, seller_nickname: str) -> Dict[str, Optional[str]]:
        """
        Busca información de contacto del vendedor usando Google Custom Search.
        
        Utiliza caché en memoria para evitar búsquedas repetidas del mismo vendedor.
        
        Args:
            seller_nickname: Nombre del vendedor a buscar
            
        Returns:
            Diccionario con información de contacto (teléfono, email, facebook_url)
        """
        # Verificar si ya tenemos el resultado en caché
        cache_key = seller_nickname.lower().strip()
        if cache_key in self.contact_cache:
            logger.info(f"Usando información de contacto en caché para vendedor: '{seller_nickname}'")
            return self.contact_cache[cache_key]
        
        # Construir la consulta de búsqueda
        query = f'"{seller_nickname}" (contacto OR teléfono OR email OR whatsapp) Argentina site:mercadolibre.com.ar OR site:*.mercadoshops.com.ar OR site:instagram.com OR site:facebook.com'
        
        # Parámetros de la búsqueda
        params = {
            'key': self.api_key, 
            'cx': self.cse_id, 
            'q': query,
            'num': 3, 
            'gl': 'ar', 
            'cr': 'countryAR', 
            'lr': 'lang_es'
        }
        
        # Inicializar la información de contacto
        contact_info = {"phone": None, "email": None, "facebook_url": None}

        try:
            logger.info(f"Buscando contactos para: '{seller_nickname}'")
            
            # Usar el APIClient para realizar la petición
            response = self.api_client.get(
                self.GOOGLE_API_HOST,
                params=params
            )
            
            # Procesar la respuesta
            search_items = response.json().get('items', [])
            logger.info(f"Google API devolvió {len(search_items)} items para '{seller_nickname}'.")

            # Procesar cada resultado de búsqueda
            for item in search_items:
                self._process_search_item(item, contact_info)
                
                # Si ya encontramos toda la información necesaria, salir del bucle
                if all(contact_info.values()):
                    break
            
            # Almacenar en caché para futuras consultas
            self.contact_cache[cache_key] = contact_info
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Error al buscar contactos para '{seller_nickname}': {str(e)}")
            if self.monitor:
                self.monitor.track_exception(e, {"context": "google_search", "seller": seller_nickname})
            return contact_info
    
    def _process_search_item(self, item: Dict[str, Any], contact_info: Dict[str, Optional[str]]) -> None:
        """
        Procesa un ítem de resultado de búsqueda y actualiza la información de contacto.
        
        Args:
            item: Ítem de resultado de búsqueda de Google
            contact_info: Diccionario para almacenar la información de contacto
        """
        text_content = f"{item.get('title', '')} {item.get('snippet', '')} {item.get('link', '')}".lower()
        link_url = item.get('link', '').lower()
        
        # Buscar teléfono si aún no se encontró
        if not contact_info["phone"]:
            self._extract_phone(text_content, contact_info)
        
        # Buscar email si aún no se encontró
        if not contact_info["email"]:
            self._extract_email(text_content, contact_info)
        
        # Buscar URL de Facebook si aún no se encontró
        if not contact_info["facebook_url"] and 'facebook.com' in link_url:
            contact_info["facebook_url"] = link_url
    
    def _extract_phone(self, text: str, contact_info: Dict[str, Optional[str]]) -> None:
        """
        Extrae un número de teléfono del texto y lo formatea.
        
        Args:
            text: Texto donde buscar el teléfono
            contact_info: Diccionario para almacenar el teléfono encontrado
        """
        phone_pattern = r'(?:(?:\B\+?54\s?9?)(?:11|[23]\d{1,3})\s?|0?(?:11|[23]\d{1,3})\s?)(?:15)?\s?\d{2,4}[\s\.-]?\d{3,4}\b'
        phone_match = re.search(phone_pattern, text)
        
        if phone_match:
            raw_phone = phone_match.group(0)
            digits_phone = re.sub(r'\D', '', raw_phone)
            
            # Limpiar y formatear el número de teléfono
            if digits_phone.startswith('0'): 
                digits_phone = digits_phone[1:]
            if digits_phone.startswith('15'): 
                digits_phone = digits_phone[2:]
                
            # Manejar números de Argentina
            if len(digits_phone) == 8 and (raw_phone.startswith('11') or raw_phone.startswith('011') or 
                                         (raw_phone.startswith('+5411') and not raw_phone.startswith('+54911'))):
                digits_phone = '9' + digits_phone
                
            if not digits_phone.startswith('54'):
                if len(digits_phone) == 10 and digits_phone.startswith('11'):
                    digits_phone = '549' + digits_phone
                elif len(digits_phone) >= 8:
                    digits_phone = '549' + digits_phone  # Asumir móvil
            
            contact_info["phone"] = f"+{digits_phone}"
    
    def _extract_email(self, text: str, contact_info: Dict[str, Optional[str]]) -> None:
        """
        Extrae una dirección de email del texto.
        
        Args:
            text: Texto donde buscar el email
            contact_info: Diccionario para almacenar el email encontrado
        """
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact_info["email"] = email_match.group(0)
    
    def generate_whatsapp_link(self, phone_number: str, product_title: str) -> str:
        """
        Genera un enlace de WhatsApp para contactar al vendedor.
        
        Args:
            phone_number: Número de teléfono en formato internacional (+549...)
            product_title: Título del producto para incluir en el mensaje
            
        Returns:
            URL de WhatsApp o None si el teléfono no es válido
        """
        if not phone_number or not phone_number.strip():
            return ""
            
        # Limpiar el número de teléfono
        clean_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Si no tiene código de país, asumir Argentina (+54)
        if not clean_number.startswith('+'):
            clean_number = '54' + clean_number.lstrip('0')
        
        # Codificar el mensaje
        message = f"Hola, estoy interesado en {product_title}"
        encoded_message = requests.utils.quote(message)
        
        # Generar el enlace
        return f"https://wa.me/{clean_number}?text={encoded_message}"
