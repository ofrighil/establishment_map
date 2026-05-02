import csv
import logging
import sqlite3
from uuid import uuid7

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "establishments.db"
TABLE_NAME = "greater_ny"
TABLE_SCHEMA = {
    "id": "TEXT PRIMAY KEY",
    "name": "TEXT NOT NULL",
    "website": "TEXT",
    "phone_number": "TEXT",
    "street": "TEXT NOT NULL",
    "city": "TEXT NOT NULL",
    "state": "TEXT NOT NULL",
    "zip_code": "TEXT NOT NULL",
    "latitude": "REAL NOT NULL",
    "longitude": "REAL NOT NULL",
    "category": "TEXT NOT NULL",
    "cuisine": "TEXT",
    "have_been": "INTEGER NOT NULL",
    "closed": "INTEGER NOT NULL",
    "would_return": "INTEGER",
}
INDEXES = ["category", "cuisine", "have_been"]
VIEW_FULL_ADDRESS = "v_full_address"

assert TABLE_SCHEMA.keys() > set(INDEXES)

def convert(name: str, value: str):
    if value == "NULL":
        return None
    if name in ["have_been", "closed", "would_return"]:
        return True if value == "TRUE" else False

    return value

def sync(file_name: str):
    with open(file_name, "r") as f:
        reader = csv.reader(f)

        header = next(reader)
        assert set(header) > (TABLE_SCHEMA.keys() - {"id"})

        rows = []
        # for row in reader:
        #     row = [value for name, value in zip(header, row) if name in TABLE_SCHEMA]
        #     rows.append([str(uuid7())] + row)
        for data in reader:
            row = []
            for name, value in zip(header, data):
                if name in TABLE_SCHEMA:
                    row.append(convert(name, value))
            rows.append([str(uuid7())] + row)

        connection = sqlite3.connect(DB_NAME, autocommit=True)
        with connection:
            logger.info(f"dropping TABLE {TABLE_NAME} in DATABASE {DB_NAME}")
            connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
            logger.info(f"TABLE {TABLE_NAME} in DATABASE {DB_NAME} dropped")

            logger.info(f"creating TABLE {TABLE_NAME} in DATABASE {DB_NAME}")
            connection.execute(
                f"CREATE TABLE {TABLE_NAME}({', '.join(f'{k} {v}' for k, v in TABLE_SCHEMA.items())});"
            )
            logger.info(f"TABLE {TABLE_NAME} in DATABASE {DB_NAME} created")

            for index in INDEXES:
                logger.info(f"creating INDEX {index} in TABLE {TABLE_NAME}")
                connection.execute(
                    f"CREATE INDEX idx_{TABLE_NAME.lower()}_{index} ON {TABLE_NAME}({index})"
                )
                logger.info(f"INDEX {index} in TABLE {TABLE_NAME} created")

            logger.info(f"Adding {len(rows)} rows to TABLE {TABLE_NAME}")
            connection.executemany(
                f"INSERT INTO {TABLE_NAME} VALUES({', '.join('?' for _ in range(len(TABLE_SCHEMA)))});",
                rows,
            )
            n = connection.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};").fetchone()[0]
            logger.info(f"{n} rows added to TABLE {TABLE_NAME}")

            logger.info(f"dropping VIEW {VIEW_FULL_ADDRESS} in DATABASE {DB_NAME}")
            connection.execute(f"DROP VIEW IF EXISTS {VIEW_FULL_ADDRESS};")
            logger.info(f"VIEW {VIEW_FULL_ADDRESS} in DATABASE {DB_NAME} dropped")

            logger.info(f"creating VIEW {VIEW_FULL_ADDRESS} in DATABASE {DB_NAME}")
            connection.execute(
                f"""
                CREATE VIEW {VIEW_FULL_ADDRESS} AS
                SELECT
                    id,
                    street || ', ' || city || ', ' || state || ' ' || zip_code AS full_address
                FROM {TABLE_NAME};
                """
            )
            logger.info(f"VIEW {VIEW_FULL_ADDRESS} in DATABASE {DB_NAME} created")

if __name__ == "__main__":
    sync("./nyc_food_db.csv")
