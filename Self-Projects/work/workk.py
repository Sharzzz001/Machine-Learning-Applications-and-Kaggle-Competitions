def file_date_exists(cursor, table_name, file_date):
    query = f"SELECT COUNT(*) FROM [{table_name}] WHERE file_date = ?"
    cursor.execute(query, file_date)
    count = cursor.fetchone()[0]
    return count > 0