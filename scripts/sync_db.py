import csv
import sqlite3
from uuid import uuid7

DB_NAME = "establishments.db"
TABLE_NAME = "greater_ny"
TABLE_SCHEMA = {
    "uuid": "TEXT",  # non-nullable
    "name": "TEXT",  # non-nullable
    "website": "TEXT",
    "phone_number": "TEXT",
    "street": "TEXT",  # non-nullable
    "city": "TEXT",  # non-nullable
    "state": "TEXT",  # non-nullable
    "zip_code": "TEXT",  # non-nullable
    "latitude": "REAL",  # non-nullable
    "longitude": "REAL",  # non-nullable
    "category": "TEXT",
    "cuisine": "TEXT",
    "have_been": "NUMERIC",  # boolean, non-nullable
    "closed": "NUMERIC",  # boolean, non-nullable
    "would_return": "NUMERIC",  # boolean, non-nullable
}


def sync(file_name: str):
    with open(file_name, "r") as f:
        reader = csv.reader(f)

        header = next(reader)
        assert set(header) > (TABLE_SCHEMA.keys() - {"uuid"})

        rows = []
        for row in reader:
            row = [value for name, value in zip(header, row) if name in TABLE_SCHEMA]
            rows.append([str(uuid7())] + row)

        connection = sqlite3.connect(DB_NAME, autocommit=True)
        with connection:
            connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
            connection.execute(
                f"CREATE TABLE {TABLE_NAME}({', '.join(f'{k} {v}' for k, v in TABLE_SCHEMA.items())})"
            )
            connection.executemany(
                f"INSERT INTO {TABLE_NAME} VALUES({', '.join('?' for _ in range(len(TABLE_SCHEMA)))})",
                rows,
            )


if __name__ == "__main__":
    sync("./nyc_food_db.csv")
