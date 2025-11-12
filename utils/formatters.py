#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilidades para formatear datos en presentaciones amigables para el usuario.
Este módulo contiene funciones para transformar datos estructurados en formatos
como Markdown, HTML o texto plano para mejor visualización.
"""

import logging
from typing import Dict, List, Any, Optional

# Configurar logging
logger = logging.getLogger(__name__)

def format_business_contact_cards(api_response: Dict[str, Any]) -> str:
    """
    Extrae y formatea información de contacto de negocios desde una respuesta de API
    en formato de tarjetas Markdown.
    
    Procesa resultados de búsqueda de negocios (de RapidAPI Maps Data o Google Places API)
    y extrae solo la información de contacto esencial, presentándola en un formato
    limpio y legible.
    
    Args:
        api_response (dict): Respuesta de API con datos de negocios
            Debe contener las claves "status" y "data" con una lista de resultados
            
    Returns:
        str: Tarjetas de contacto formateadas en Markdown,
             o mensaje indicando que no hay resultados
    """
    if not api_response or api_response.get("status") != "ok" or not api_response.get("data"):
        return "No se encontraron resultados para mostrar."
    
    results = api_response.get("data", [])
    
    # Encabezado con resumen
    markdown_output = f"¡Encontré {len(results)} resultado{'s' if len(results) > 1 else ''} posible{'s' if len(results) > 1 else ''}!\n\n"
    
    for idx, business in enumerate(results):
        # Extraer solo los campos relevantes
        name = business.get("name", "No disponible")
        phone = business.get("phone_number", "No disponible")
        address = business.get("full_address", "No disponible")
        website = business.get("website")
        map_link = business.get("place_link", "No disponible")
        
        # Formatear sitio web
        website_md = f"[{website.replace('http://', '').replace('https://', '').rstrip('/')}]({website})" if website else "No disponible"
        
        # Formatear enlace al mapa
        map_md = f"[Enlace a Google Maps]({map_link})" if map_link else "No disponible"
        
        # Construir tarjeta de contacto
        card = f"**Nombre:** {name}\n"
        card += f"📞 **Teléfono:** `{phone}`\n"
        card += f"📍 **Dirección:** {address}\n"
        card += f"🌐 **Sitio Web:** {website_md}\n"
        card += f"🗺️ **Ver en Mapa:** {map_md}"
        
        # Añadir separador excepto para el último resultado
        markdown_output += card
        if idx < len(results) - 1:
            markdown_output += "\n\n---\n\n"
    
    return markdown_output

def format_contact_list_plain(api_response: Dict[str, Any]) -> str:
    """
    Versión simplificada del formateador de contactos que devuelve texto plano.
    Útil para interfaces que no soportan Markdown.
    
    Args:
        api_response (dict): Respuesta de API con datos de negocios
            
    Returns:
        str: Información de contacto en formato de texto plano
    """
    if not api_response or api_response.get("status") != "ok" or not api_response.get("data"):
        return "No se encontraron resultados."
    
    results = api_response.get("data", [])
    plain_output = f"Se encontraron {len(results)} resultados:\n\n"
    
    for idx, business in enumerate(results):
        name = business.get("name", "No disponible")
        phone = business.get("phone_number", "No disponible")
        address = business.get("full_address", "No disponible")
        
        plain_output += f"[{idx+1}] {name}\n"
        plain_output += f"    Teléfono: {phone}\n"
        plain_output += f"    Dirección: {address}\n\n"
    
    return plain_output
