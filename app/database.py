"""
Módulo para manejar la conexión a la base de datos PostgreSQL en Neon.tech
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager

# Cargar variables de entorno
load_dotenv()

def get_connection():
    """Obtiene una conexión a la base de datos."""
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')

@contextmanager
def get_cursor():
    ""
    Context manager para manejar la conexión a la base de datos.
    
    Uso:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM tabla")
            result = cur.fetchall()
    """
    conn = None
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
            conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error en la base de datos: {e}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    try:
        with get_cursor() as cur:
            # Crear tabla de vendedores
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vendedores (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    nick VARCHAR(100) UNIQUE NOT NULL,
                    telefono VARCHAR(50),
                    email VARCHAR(255),
                    ubicacion JSONB,
                    reputacion FLOAT,
                    ventas_totales INTEGER,
                    fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear tabla de productos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id VARCHAR(50) PRIMARY KEY,
                    titulo TEXT NOT NULL,
                    precio DECIMAL(10, 2) NOT NULL,
                    moneda VARCHAR(10) NOT NULL,
                    condicion VARCHAR(50),
                    envio_gratis BOOLEAN,
                    url TEXT,
                    url_imagen TEXT,
                    vendedor_nick VARCHAR(100) REFERENCES vendedores(nick) ON DELETE CASCADE,
                    fecha_publicacion TIMESTAMP WITH TIME ZONE,
                    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    datos_adicionales JSONB
                )
            """)
            
            # Crear tabla de búsquedas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS busquedas (
                    id SERIAL PRIMARY KEY,
                    termino_busqueda VARCHAR(255) NOT NULL,
                    fecha_busqueda TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    total_resultados INTEGER,
                    parametros_busqueda JSONB
                )
            """)
            
            # Índices para mejorar el rendimiento
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_vendedores_nick ON vendedores(nick);
                CREATE INDEX IF NOT EXISTS idx_productos_vendedor ON productos(vendedor_nick);
                CREATE INDEX IF NOT EXISTS idx_busquedas_termino ON busquedas(termino_busqueda);
            """)
            
            print("Base de datos inicializada correctamente")
            
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise

if __name__ == "__main__":
    init_db()
