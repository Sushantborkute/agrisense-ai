
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

server = os.getenv("FABRIC_SERVER")
database = os.getenv("FABRIC_DATABASE")

if not server or not database:
    raise ValueError("FABRIC_SERVER or FABRIC_DATABASE is missing from .env")

connection_string = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server={server};"
    f"Database={database};"
    "Authentication=ActiveDirectoryInteractive;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

print("Connecting to Microsoft Fabric...")
connection = pyodbc.connect(connection_string, timeout=30)

try:
    cursor = connection.cursor()
    cursor.execute("""
        SELECT TOP 5
            farm_id, zone_id, crop_type, soil_moisture_pct
        FROM dbo.farm_sensor_readings
        ORDER BY timestamp DESC
    """)

    for row in cursor.fetchall():
        print(row)

    print("\nFabric connection successful!")
finally:
    connection.close()
