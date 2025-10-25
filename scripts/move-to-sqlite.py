import json
import sqlite3
import os
import sys
from dotenv import load_dotenv

load_dotenv()
DATA_FOLDER = os.getenv('SCRAPY_OUTPUT_DIR')
DB_PATH = os.getenv('SQLITE_FILE_PATH')

def insert_json_to_sqlite(json_file, db_file="jobs-data.db", table_name="jobs-data"):
    # Ensure JSON file exists
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        sys.exit(1)

    # Read JSON data
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # JSON may be a list of items or a single dict
    if isinstance(data, dict):
        data = [data]

    if not data:
        print("⚠️ No data found in JSON file.")
        return

    # Extract columns from first item
    columns = list(data[0].keys())

    # Connect to SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create table if not exists
    columns_def = ", ".join([f'"{col}" TEXT' for col in columns])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})")

    # Insert data
    placeholders = ", ".join(["?"] * len(columns))
    insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

    for item in data:
        values = [str(item.get(col, "")) for col in columns]
        cursor.execute(insert_query, values)

    conn.commit()
    conn.close()

    print(f"✅ Inserted {len(data)} records into '{table_name}' in {db_file}")


if __name__ == "__main__":

    json_path = DATA_FOLDER
    insert_json_to_sqlite(json_path)
