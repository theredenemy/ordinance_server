import sqlite3


def add_column_if_not_exists(db, table, column_name, column_type, default=None):
    with sqlite3.connect(db) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = []
        for row in cursor.fetchall():
            columns.append(row[1])
        if column_name not in columns:
            if default:
                sql_cmd = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type} NOT NULL DEFAULT {default}"
            else:
                sql_cmd = f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}"
            print(sql_cmd)
            cursor.execute(sql_cmd)
            conn.commit()