"""
Utilidades comunes para todos los agentes.
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List, Union
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Configuración de logging
logger = logging.getLogger(__name__)

# Constantes comunes
REQUEST_TIMEOUT = 15  # segundos

def get_secrets() -> Dict[str, str]:
    """
    Obtiene los secretos necesarios del Azure Key Vault o variables de entorno.
    
    Returns:
        Un diccionario con las claves de API necesarias
    
    Raises:
        EnvironmentError: Si no se pueden obtener los secretos necesarios
    """
    # Lista de secretos requeridos
    required_secrets = ["RAPIDAPI-KEY", "GOOGLE-API-KEY", "GOOGLE-CSE-ID"]
    secrets = {}
    
    # Intenta obtener secretos de variables de entorno primero
    env_secrets = {}
    for secret_name in required_secrets:
        # Convertir guiones a guiones bajos para variables de entorno
        env_name = secret_name.replace("-", "_")
        env_value = os.getenv(env_name)
        if env_value:
            env_secrets[secret_name] = env_value
            logger.info(f"Secreto {secret_name} obtenido de variable de entorno.")
    
    # Si encontramos todos los secretos en variables de entorno, usarlos
    if len(env_secrets) == len(required_secrets):
        logger.info("Todos los secretos obtenidos de variables de entorno.")
        return env_secrets
    
    # Intentar con Key Vault si faltaron secretos en variables de entorno
    key_vault_uri = os.getenv("KEY_VAULT_URI")
    if not key_vault_uri:
        # Si no tenemos todos los secretos y no hay Key Vault configurado
        if env_secrets:
            missing = [s for s in required_secrets if s not in env_secrets]
            logger.error(f"Faltan secretos: {missing}")
            raise EnvironmentError(
                f"Faltan los siguientes secretos y no hay KEY_VAULT_URI configurado: {missing}"
            )
        else:
            logger.error("No hay KEY_VAULT_URI configurado ni variables de entorno con secretos.")
            raise EnvironmentError(
                "Configure KEY_VAULT_URI o las variables de entorno con los secretos requeridos."
            )
    
    # Intentar obtener secretos del Key Vault
    try:
        logger.info(f"Obteniendo credenciales de Azure Key Vault: {key_vault_uri}")
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_uri, credential=credential)
        
        # Obtener los secretos que falten del Key Vault
        missing_secrets = [s for s in required_secrets if s not in env_secrets]
        for secret_name in missing_secrets:
            try:
                secret = client.get_secret(secret_name)
                secrets[secret_name] = secret.value
                logger.info(f"Secreto {secret_name} obtenido correctamente de Key Vault.")
            except Exception as e:
                logger.error(f"Error al obtener secreto {secret_name} del Key Vault: {e}")
                # Si el secreto tampoco está en variables de entorno, es un error crítico
                if secret_name not in env_secrets:
                    raise
        
        # Combinar secretos de Key Vault y variables de entorno
        secrets.update(env_secrets)
        
        # Verificar que tenemos todos los secretos
        if all(secret in secrets for secret in required_secrets):
            return secrets
        else:
            missing = [s for s in required_secrets if s not in secrets]
            logger.error(f"Faltan secretos después de intentar Key Vault y variables de entorno: {missing}")
            raise EnvironmentError(f"No se pudieron obtener todos los secretos necesarios: {missing}")
            
    except Exception as e:
        # Si ya tenemos algunos secretos de variables de entorno, intentamos usarlos
        if env_secrets and len(env_secrets) == len(required_secrets):
            logger.warning(f"Error al acceder a Key Vault: {e}, pero se usarán variables de entorno")
            return env_secrets
        else:
            logger.error(f"Error crítico al obtener secretos del Key Vault: {e}", exc_info=True)
            raise ConnectionError(f"No se pudieron obtener los secretos del Key Vault: {e}")
