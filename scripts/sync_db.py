import csv
import sqlite3


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
    "zip_code": "NUMERIC",  # non-nullable
    "latitude": "REAL",  # non-nullable
    "longitude": "REAL",  # non-nullable
    "category": "TEXT",
    "cuisine": "TEXT",
    "specialty": "TEXT",
    "latest_visit": "TEXT",  # date
    "have_been": "NUMERIC",  # boolean, non-nullable
    "closed": "NUMERIC",  # boolean, non-nullable
    "would_return": "TEXT",
    "comments": "TEXT",
}


def replace_null(row: list) -> list:
    for i, value in enumerate(row):
        if value == "NULL":
            row[i] = None

    return row


def sync(file_name: str):
    with open(file_name, "r") as f:
        reader = csv.reader(f)

        header = next(reader)
        assert header == list(TABLE_SCHEMA.keys())

        rows = (tuple(replace_null(row)) for row in reader)

        connection = sqlite3.connect(DB_NAME, autocommit=True)
        with connection:
            connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
            connection.execute(f"CREATE TABLE {TABLE_NAME}({', '.join(f'{k} {v}' for k, v in TABLE_SCHEMA.items())})")
            connection.executemany(f"INSERT INTO {TABLE_NAME} VALUES({', '.join('?' for _ in range(len(TABLE_SCHEMA)))})", rows)


if __name__ == "__main__":
    sync("./nyc_food_db.csv")
