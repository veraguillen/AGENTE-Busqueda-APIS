# Agente de Búsqueda de Productos

Backend en Azure Functions para buscar productos en Mercado Libre, filtrar vendedores, obtener contactos con Google Custom Search, y devolver un top 5 de productos con enlaces de WhatsApp para contactar a los vendedores.

## Estructura del Proyecto

```
c:\Users\veram\OneDrive\Escritorio\Agente Busqueda\
├── .env                      # Variables de entorno
├── agents/                   # Módulo de agentes especializados
│   ├── __init__.py           # Configuración para elegir versión del AgenteML
│   ├── agente_filtro.py      # Agente para filtrado
│   ├── agente_google.py      # Agente para búsquedas en Google
│   ├── agente_ml_simple.py   # Versión simple del agente ML (actualmente en uso)
│   ├── agente_ml_complex.py  # Versión compleja del agente ML
│   ├── agente_ranking.py     # Agente para ranking de resultados
│   ├── common.py             # Funciones comunes para agentes
│   └── google_search.py      # Implementación de búsqueda en Google
├── app/                      # Capa de aplicación
│   ├── __init__.py
│   ├── agente_ml.py          # Archivo puente para importación de agentes
│   ├── main.py               # Punto de entrada principal
│   ├── orquestador.py        # Orquestador del flujo de trabajo
│   └── utils/                # Utilidades de la aplicación
│       ├── check_rapidapi_endpoints.py
│       └── seller_extractor.py
├── functions/                # Funciones serverless (Azure Functions)
│   └── AgenteBusquedaTrigger/
│       ├── __init__.py
│       └── function.json
├── services/                 # Servicios compartidos
│   ├── cache_manager.py      # Gestor de caché
│   └── config_manager.py     # Gestor de configuración
├── README.md                 # Documentación del proyecto
├── requirements.txt          # Dependencias del proyecto
└── host.json                 # Configuración del host de Azure Functions
```

## Flujo de Trabajo

1. El punto de entrada recibe una consulta y país
2. El orquestador coordina el flujo entre los agentes:
   - `AgenteML`: Busca productos en MercadoLibre
   - `AgenteFiltro`: Filtra vendedores que son marcas oficiales
   - `AgenteRanking`: Ordena los resultados por relevancia
   - `AgenteGoogle`: Busca información de contacto y genera enlaces de WhatsApp
3. Se devuelve un JSON con los productos mejor rankeados y enlaces de contacto

## Guía para Desarrolladores

### Para Desarrolladores Backend

#### Configuración Inicial

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   - Crear archivo `.env` con las siguientes variables:
   ```
   RAPIDAPI_KEY=tu_clave_de_rapidapi
   GOOGLE_API_KEY=tu_clave_de_google_api
   GOOGLE_CSE_ID=tu_id_de_custom_search_engine
   ```

3. **Configuración de Azure Functions** (para desarrollo local):
   ```bash
   func start
   ```

#### Pruebas del Sistema

1. **Prueba básica del orquestador**:
   ```python
   # Crear script test_orquestador.py
   from app.orquestador import Orquestador
   
   orq = Orquestador()
   resultados = orq.buscar_productos("smartphone", "ar", max_pages=2)
   print(resultados)
   ```

2. **Prueba de agentes individuales**:
   ```python
   # Probar el agente ML directamente
   from agents import AgenteML
   import os
   
   api_key = os.environ.get("RAPIDAPI_KEY")
   agente = AgenteML(rapidapi_key=api_key)
   resultados = agente.search("smartphone", "ar", max_pages=1)
   print(f"Encontrados: {len(resultados)} productos")
   ```

#### Cambiar entre versiones de AgenteML

Para cambiar entre la versión simple y compleja del AgenteML:

1. **Opción 1**: Editar `agents/__init__.py`
   ```python
   # Para usar la versión simple (actual)
   from .agente_ml_simple import AgenteML
   
   # Para usar la versión compleja, comentar la línea anterior y descomentar:
   # from .agente_ml_complex import AgenteML
   ```

2. **Opción 2**: Modificar directamente la importación en `app/agente_ml.py`

#### Despliegue

Para desplegar en Azure Functions:

```bash
func azure functionapp publish <nombre-de-tu-function-app>
```

### Para Desarrolladores Frontend

#### Endpoints API

1. **Búsqueda de Productos**:
   ```
   GET https://<function-app>.azurewebsites.net/api/main
   ```

   Parámetros:
   - `query` (requerido): Término de búsqueda (ej: "smartphone", "laptop")
   - `country` (opcional): Código de país (por defecto "AR", también acepta "MX", "CL", etc.)

   Respuesta:
   ```json
   {
     "status": "success",
     "top_products": [
       {
         "rank": 1,
         "product_title": "Smartphone XYZ",
         "price": 150000,
         "currency": "ARS",
         "condition": "new",
         "sold_quantity": 42,
         "listing_url": "https://articulo.mercadolibre.com.ar/...",
         "seller": {
           "nickname": "VENDEDOR_OFICIAL",
           "contact": {
             "phone": "+54911XXXXXXXX",
             "email": "contacto@vendedor.com",
             "whatsapp_url": "https://wa.me/54911XXXXXXXX?text=Hola..."
           }
         }
       }
     ]
   }
   ```

2. **Monitoreo de Estado** (Health Check):
   ```
   GET https://<function-app>.azurewebsites.net/api/health
   ```

#### Ejemplos de Integración

**JavaScript (Fetch API)**:
```javascript
async function buscarProductos(query, country = 'AR') {
  const response = await fetch(`https://<function-app>.azurewebsites.net/api/main?query=${encodeURIComponent(query)}&country=${country}`);
  const data = await response.json();
  return data;
}

// Ejemplo de uso
buscarProductos('smartphone')
  .then(data => {
    console.log('Productos encontrados:', data.top_products);
    // Mostrar resultados en la UI
  })
  .catch(error => console.error('Error:', error));
```

## Uso

```bash
# Llamada directa al API
curl "https://<function-app>.azurewebsites.net/api/main?query=iphone&country=AR"

# Prueba local
curl "http://localhost:7071/api/main?query=iphone&country=AR"
```

## Mantenimiento y Troubleshooting

### Registros (Logs)

- Los logs se generan en formato estructurado
- En Azure: revisar Application Insights
- Localmente: revisar la consola durante `func start`

### Problemas Comunes

1. **Error de RapidAPI**: Verificar cuota y validez de la API key
2. **Resultados vacíos**: Revisar el término de búsqueda y el código de país
3. **Cambio de implementación no efectivo**: Asegurarse de modificar el archivo correcto (`agents/__init__.py`)

---

Desarrollado por el equipo de Agente Busqueda, 2025