# python -m venv venv
# ./venv/Scripts/Activate.ps1
# pip install -r requirements.txt
# python structure.py
# deactivate

import pyodbc
import json

# Configuración de la conexión a SQL Server
server = 'tu_servidor'
database = 'tu_base_de_datos'
username = 'tu_usuario'
password = 'tu_contraseña'
conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Conectar a la base de datos
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Obtener la lista de tablas
cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
tables = [row.TABLE_NAME for row in cursor.fetchall()]

# Inicializar la estructura JSON
db_structure = {"tables": []}

for table in tables:
    # Obtener las columnas de la tabla
    cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table}'
    """)
    columns = []
    for row in cursor.fetchall():
        column_name = row.COLUMN_NAME
        data_type = row.DATA_TYPE
        max_length = row.CHARACTER_MAXIMUM_LENGTH
        
        # Formatear el tipo de dato
        if max_length:
            data_type = f"{data_type}({max_length})"
        
        # Verificar si es una clave primaria
        cursor.execute(f"""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_NAME), 'IsPrimaryKey') = 1
            AND TABLE_NAME = '{table}'
        """)
        primary_key = cursor.fetchone()
        is_primary_key = primary_key and primary_key.COLUMN_NAME == column_name
        
        # Verificar si es una clave foránea
        cursor.execute(f"""
            SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = '{table}'
            AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        foreign_key = cursor.fetchone()
        is_foreign_key = foreign_key and foreign_key.COLUMN_NAME == column_name
        foreign_key_ref = f"{foreign_key.REFERENCED_TABLE_NAME}.{foreign_key.REFERENCED_COLUMN_NAME}" if is_foreign_key else None
        
        # Añadir la columna a la lista
        column_info = {"name": column_name, "type": data_type}
        if is_primary_key:
            column_info["primary_key"] = True
        if is_foreign_key:
            column_info["foreign_key"] = foreign_key_ref
        
        columns.append(column_info)
    
    # Añadir la tabla a la estructura JSON
    db_structure["tables"].append({"name": table, "columns": columns})

# Convertir la estructura a JSON
json_output = json.dumps(db_structure, indent=4)

# Guardar el JSON en un archivo
with open('db_structure.json', 'w') as json_file:
    json_file.write(json_output)

# Cerrar la conexión
cursor.close()
conn.close()

print("Estructura de la base de datos exportada a db_structure.json")