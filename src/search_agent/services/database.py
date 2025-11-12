"""
Módulo para manejar la conexión a la base de datos PostgreSQL en Neon.tech
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Iterator, Any, Dict, List, Optional

# Cargar variables de entorno
load_dotenv()

def get_connection():
    """Obtiene una conexión a la base de datos."""
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode='require')

@contextmanager
def get_cursor() -> Iterator[Any]:
    """
    Context manager para manejar la conexión a la base de datos.
    
    Uso:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM tabla")
            result = cur.fetchone()
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Inicializa la base de datos creando las tablas necesarias si no existen."""
    with get_cursor() as cur:
        # Crear tabla de vendedores
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendedores (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellido TEXT,
                email TEXT,
                telefono TEXT,
                direccion TEXT,
                ciudad TEXT,
                pais TEXT,
                codigo_postal TEXT,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de productos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                id_vendedor INTEGER REFERENCES vendedores(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio DECIMAL(10, 2) NOT NULL,
                moneda TEXT DEFAULT 'ARS',
                categoria TEXT,
                stock INTEGER DEFAULT 0,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Crear tabla de búsquedas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS busquedas (
                id SERIAL PRIMARY KEY,
                termino_busqueda TEXT NOT NULL,
                pais TEXT NOT NULL,
                fecha_busqueda TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                resultados_obtenidos INTEGER DEFAULT 0,
                id_usuario INTEGER,
                parametros_busqueda JSONB
            )
        """)
        
        # Crear tabla de historial de precios
        cur.execute("""
            CREATE TABLE IF NOT EXISTS historial_precios (
                id SERIAL PRIMARY KEY,
                id_producto INTEGER REFERENCES productos(id) ON DELETE CASCADE,
                precio_anterior DECIMAL(10, 2),
                precio_nuevo DECIMAL(10, 2) NOT NULL,
                fecha_cambio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                motivo_cambio TEXT
            )
        """)
        
        # Crear índices para mejorar el rendimiento
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_vendedor ON productos(id_vendedor)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_busquedas_fecha ON busquedas(fecha_busqueda)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_historial_precios_producto ON historial_precios(id_producto)")
        
        # Crear función para actualizar automáticamente la fecha de actualización
        cur.execute("""
            CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.fecha_actualizacion = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Crear triggers para actualizar automáticamente las fechas de actualización
        for tabla in ["vendedores", "productos"]:
            cur.execute(f"""
                DROP TRIGGER IF EXISTS actualizar_{tabla}_fecha_actualizacion ON {tabla};
                CREATE TRIGGER actualizar_{tabla}_fecha_actualizacion
                BEFORE UPDATE ON {tabla}
                FOR EACH ROW
                EXECUTE FUNCTION actualizar_fecha_actualizacion();
            """)

class DatabaseManager:
    """Clase para manejar operaciones comunes de la base de datos."""
    
    @staticmethod
    def execute_query(query: str, params: Optional[tuple] = None, fetch_all: bool = True) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL y devuelve los resultados.
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            fetch_all: Si es True, devuelve todos los resultados; si es False, solo el primero
            
        Returns:
            Lista de diccionarios con los resultados
        """
        with get_cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall() if fetch_all else cur.fetchone()
    
    @staticmethod
    def execute_update(query: str, params: Optional[tuple] = None) -> int:
        """
        Ejecuta una consulta de actualización y devuelve el número de filas afectadas.
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            
        Returns:
            Número de filas afectadas
        """
        with get_cursor() as cur:
            cur.execute(query, params or ())
            return cur.rowcount
    
    @staticmethod
    def insert(table: str, data: Dict[str, Any], return_id: bool = False) -> Optional[int]:
        """
        Inserta un nuevo registro en la tabla especificada.
        
        Args:
            table: Nombre de la tabla
            data: Diccionario con los datos a insertar
            return_id: Si es True, devuelve el ID del registro insertado
            
        Returns:
            ID del registro insertado (si return_id=True) o None
        """
        if not data:
            return None
            
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = tuple(data.values())
        
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
        """
        
        if return_id:
            query += " RETURNING id"
            with get_cursor() as cur:
                cur.execute(query, values)
                result = cur.fetchone()
                return result["id"] if result else None
        else:
            with get_cursor() as cur:
                cur.execute(query, values)
                return None
