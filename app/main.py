import azure.functions as func
import logging
import json
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importar el orquestador
from app.orquestador import Orquestador

# Configuración de logging
logger = logging.getLogger(__name__)


def filter_and_rank_products(ml_listings: List[Dict[str, Any]], country_code: str) -> List[Dict[str, Any]]:
    """Filtra vendedores y rankea los productos."""
    products = []
    logger.info(f"Filtrando y rankeando {len(ml_listings)} listados.")
    for item in ml_listings:
        seller = item.get("seller", {})
        seller_nickname_raw = seller.get("nickname", "") # Mantener original para búsqueda de contactos si es necesario
        
        seller_nickname_lower = seller_nickname_raw.lower()
        if not seller_nickname_lower and seller.get("eshop"):
            seller_nickname_raw = seller.get("eshop", {}).get("nick_name","")
            seller_nickname_lower = seller_nickname_raw.lower()

        if not seller_nickname_lower or any(brand in seller_nickname_lower for brand in EXCLUDED_BRANDS):
            continue
            
        price = float(item.get("price", 0))
        sold_quantity = int(item.get("sold_quantity", 0))
        condition = item.get("condition", "unknown")
        
        price_component = 0.0
        if price >= 0 and (price + 100000.0) > 0 : 
             price_component = 0.4 * max(0, (1 - (price / (price + 100000.0))))
        
        sales_component = 0.4 * min(sold_quantity / 100.0, 1.0)
        condition_component = 0.2 * (1.0 if condition == "new" else 0.0)
        score = price_component + sales_component + condition_component

        products.append({
            "product_id": item.get("id"), "title": item.get("title"), "price": price,
            "currency": item.get("currency_id"), "permalink": item.get("permalink"),
            "seller_id": seller.get("id"), "seller_nickname": seller_nickname_raw, # Usar el raw para búsqueda de contactos
            "sold_quantity": sold_quantity, "condition": condition,
            "score": round(score, 4), "thumbnail": item.get("thumbnail")
        })

    sorted_products = sorted(products, key=lambda x: x["score"], reverse=True)
    logger.info(f"Encontrados {len(sorted_products)} productos después de filtrar y rankear. Tomando top 5.")
    return sorted_products[:5]


def search_seller_contacts(seller_nickname: str, google_api_key: str, google_cse_id: str) -> Dict[str, Optional[str]]:
    """Busca información de contacto del vendedor usando Google Custom Search.
    
    Utiliza caché en memoria para evitar búsquedas repetidas del mismo vendedor.
    
    Args:
        seller_nickname: Nombre del vendedor a buscar
        google_api_key: Clave API de Google 
        google_cse_id: ID del motor de búsqueda personalizado
        
    Returns:
        Diccionario con información de contacto encontrada
    """
    # Verificar si ya tenemos el resultado en caché
    cache_key = seller_nickname.lower().strip()
    if cache_key in SELLER_CONTACT_CACHE:
        logger.info(f"Usando información de contacto en caché para vendedor: '{seller_nickname}'")
        return SELLER_CONTACT_CACHE[cache_key]
        
    # Si no está en caché, realizar la búsqueda
    query = f'"{seller_nickname}" (contacto OR teléfono OR email OR whatsapp) Argentina site:mercadolibre.com.ar OR site:*.mercadoshops.com.ar OR site:instagram.com OR site:facebook.com'
    params = {
        'key': google_api_key, 'cx': google_cse_id, 'q': query,
        'num': 3, 'gl': 'ar', 'cr': 'countryAR', 'lr': 'lang_es'
    }
    contact_info: Dict[str, Optional[str]] = {"phone": None, "email": None, "facebook_url": None}

    try:
        logger.info(f"Buscando contactos para: '{seller_nickname}'")
        response = requests.get(GOOGLE_API_HOST, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        search_items = response.json().get('items', [])
        logger.info(f"Google API devolvió {len(search_items)} items para '{seller_nickname}'.")

        for item in search_items:
            text_content = f"{item.get('title', '')} {item.get('snippet', '')} {item.get('link', '')}".lower()
            link_url = item.get('link', '').lower()

            if not contact_info["phone"]:
                phone_pattern = r'(?:(?:\B\+?54\s?9?)(?:11|[23]\d{1,3})\s?|0?(?:11|[23]\d{1,3})\s?)(?:15)?\s?\d{2,4}[\s\.-]?\d{3,4}\b'
                phone_match = re.search(phone_pattern, text_content)
                if phone_match:
                    raw_phone = phone_match.group(0)
                    digits_phone = re.sub(r'\D', '', raw_phone)
                    if digits_phone.startswith('0'): digits_phone = digits_phone[1:]
                    if digits_phone.startswith('15'): digits_phone = digits_phone[2:]
                    if len(digits_phone) == 8 and (raw_phone.startswith('11') or raw_phone.startswith('011') or (raw_phone.startswith('+5411') and not raw_phone.startswith('+54911'))):
                        digits_phone = '9' + digits_phone
                    if not digits_phone.startswith('54'):
                        if len(digits_phone) == 10 and digits_phone.startswith('11'):
                             digits_phone = '549' + digits_phone
                        elif len(digits_phone) >= 8:
                             digits_phone = '549' + digits_phone # Asumir móvil
                    elif digits_phone.startswith('54') and not digits_phone.startswith('549') and len(digits_phone) == 12 :
                        temp_phone_no_54 = digits_phone[2:]
                        if temp_phone_no_54.startswith('11') and len(temp_phone_no_54) == 10: # CABA
                             digits_phone = '549' + temp_phone_no_54
                    
                    if digits_phone.startswith('549') and len(digits_phone) == 13:
                        contact_info["phone"] = '+' + digits_phone
                    elif digits_phone.startswith('54') and len(digits_phone) == 12 : # Fijo
                        contact_info["phone"] = '+' + digits_phone


            if not contact_info["email"]:
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_content)
                if email_match: contact_info["email"] = email_match.group(0)
            
            if not contact_info["facebook_url"]:
                fb_match = re.search(r'(?:https?:\/\/)?(?:www\.)?facebook\.com\/(?!pages\/|marketplace\/|groups\/|events\/|photo(?:\.php)?|permalink\.php|story\.php|watch\/|sharer\/|login\.php|ajax\/|help\/|policies\/)[a-zA-Z0-9._-]+(?:\?(?:ref|hc_ref|fref)=[^&\s]+)?', link_url)
                if fb_match: contact_info["facebook_url"] = fb_match.group(0).split('?')[0]

            if all(val is not None for val in contact_info.values()): break

        if any(contact_info.values()):
            logger.info(f"Contactos encontrados para '{seller_nickname}': {contact_info}")
        else:
            logger.info(f"No se encontraron contactos para '{seller_nickname}'")
            
        # Guardar resultados en caché
        SELLER_CONTACT_CACHE[cache_key] = contact_info
        return contact_info
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en API Google Custom Search para '{seller_nickname}': {e}")
        return contact_info
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON de Google Custom Search para '{seller_nickname}': {e}")
        return contact_info
    except Exception as e:
        logger.error(f"Error inesperado procesando contactos para '{seller_nickname}': {e}", exc_info=True)
        return contact_info # Devuelve lo que tenga, incluso si está vacío


def generate_whatsapp_link(phone_number: str, product_title: str) -> Optional[str]:
    """Genera un enlace de WhatsApp."""
    if not phone_number or not phone_number.startswith('+54'):
        return None
    cleaned_phone_for_link = phone_number[1:] 
    message = f"Hola, te contacto por tu publicación de '{product_title}' en Mercado Libre."
    encoded_message = quote(message)
    return f"https://wa.me/{cleaned_phone_for_link}?text={encoded_message}"


# --- Azure Function Principal ---
# Esta función será detectada por el archivo function.json en la carpeta AgenteBusquedaTrigger
def agente_search_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logger.info('Procesando una nueva solicitud de búsqueda para Agente.')

    query = req.params.get('query')
    country = req.params.get('country', 'AR')

    if not query:
        logger.warning("Parámetro 'query' faltante en la solicitud.")
        return func.HttpResponse(
             json.dumps({"status": "error", "message": "Por favor, proporciona un parámetro 'query'."}),
             status_code=400,
             mimetype="application/json"
        )

    try:
        secrets = get_secrets_from_keyvault()
        rapidapi_key = secrets["RAPIDAPI-KEY"]
        google_api_key = secrets["GOOGLE-API-KEY"]
        google_cse_id = secrets["GOOGLE-CSE-ID"]

        ml_listings_data = search_ml_listings(query, country, rapidapi_key)
        if not ml_listings_data:
            logger.info(f"No se encontraron listados en ML para la query: '{query}'.")
            return func.HttpResponse(
                json.dumps({"status": "success", "message": "No se encontraron productos en Mercado Libre.", "top_products": []}),
                mimetype="application/json"
            )

        top_ranked_products = filter_and_rank_products(ml_listings_data, country)
        if not top_ranked_products:
            logger.info(f"No quedaron productos después de filtrar y rankear para la query: '{query}'.")
            return func.HttpResponse(
                json.dumps({"status": "success", "message": "No se encontraron productos que cumplan los criterios.", "top_products": []}),
                mimetype="application/json"
            )
        
        results_to_return = []
        for rank_idx, product in enumerate(top_ranked_products): # Usar enumerate para el rank
            # Pasar el seller_nickname original (no el lowercased) a search_seller_contacts
            seller_contact_info = search_seller_contacts(product["seller_nickname"], google_api_key, google_cse_id)
            
            whatsapp_url = None
            if seller_contact_info.get("phone"):
                whatsapp_url = generate_whatsapp_link(seller_contact_info["phone"], product["title"])

            results_to_return.append({
                "rank": rank_idx + 1,
                "product_title": product["title"],
                "price": product["price"],
                "currency": product["currency"],
                "condition": product["condition"],
                "sold_quantity": product["sold_quantity"],
                "listing_url": product["permalink"],
                "seller_nickname": product["seller_nickname"],
                "score": round(product["score"], 2),
                "contact_info": {
                    "phone": seller_contact_info.get("phone"),
                    "email": seller_contact_info.get("email"),
                    "facebook_url": seller_contact_info.get("facebook_url")
                },
                "whatsapp_link": whatsapp_url
            })
            if len(results_to_return) >= 5: break # Ya estaba limitado, pero por si acaso.
        
        logger.info(f"Proceso completado. Devolviendo {len(results_to_return)} productos.")
        return func.HttpResponse(
            json.dumps({"status": "success", "top_products": results_to_return}),
            mimetype="application/json"
        )

    except EnvironmentError as e:
        logger.critical(f"Error de configuración: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": f"Error de configuración: {e}"}), status_code=500, mimetype="application/json")
    except ConnectionError as e:
        logger.error(f"Error de conexión: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": f"Error de conexión externa: {e}"}), status_code=503, mimetype="application/json")
    except Exception as e:
        logger.error(f"Error inesperado: {e}", exc_info=True)
        return func.HttpResponse(json.dumps({"status": "error", "message": f"Ocurrió un error inesperado: {e}"}), status_code=500, mimetype="application/json")