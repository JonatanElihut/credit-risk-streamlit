"""
Configuración específica para MySQL
"""

MYSQL_CONFIG = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'echo': False,
    'isolation_level': 'READ COMMITTED',
    'connect_args': {
        'charset': 'utf8mb4',
        'use_unicode': True,
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': True
    }
}

# Parámetros de conexión directa (para mysql-connector-python)
MYSQL_DIRECT_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'CreditRiskDB',
    'user': 'root',
    'password': '',
    'charset': 'utf8mb4',
    'use_unicode': True,
    'get_warnings': True,
    'raise_on_warnings': False,
    'pool_name': 'creditrisk_pool',
    'pool_size': 5,
    'pool_reset_session': True
}