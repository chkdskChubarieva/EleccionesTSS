"""
Configuración de conexión a MySQL
Usa variables de entorno para seguridad
"""
import os
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

class DatabaseConfig:
    """Configuración centralizada de base de datos"""
    
    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = int(os.getenv('DB_PORT', 3306))
    DATABASE = os.getenv('DB_NAME', 'elecciones_tss')
    USER = os.getenv('DB_USER', 'root')
    PASSWORD = os.getenv('DB_PASSWORD', '')
    
    @classmethod
    def get_config(cls):
        """Retorna diccionario de configuración"""
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.DATABASE,
            'user': cls.USER,
            'password': cls.PASSWORD,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False
        }

@contextmanager
def get_db_connection():
    """
    Context manager para manejar conexiones a la base de datos
    Uso:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM encuestas")
    """
    connection = None
    try:
        connection = mysql.connector.connect(**DatabaseConfig.get_config())
        yield connection
    except Error as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection and connection.is_connected():
            connection.close()

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✓ Conexión exitosa a MySQL")
            print(f"  Versión: {version[0]}")
            
            cursor.execute("SELECT COUNT(*) FROM encuestas")
            count = cursor.fetchone()[0]
            print(f"  Encuestas registradas: {count}")
            
            return True
    except Error as e:
        print(f"✗ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    test_connection()