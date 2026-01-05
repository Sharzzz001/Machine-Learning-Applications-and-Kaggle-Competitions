def ensure_unique_index():
    conn = get_access_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            CREATE UNIQUE INDEX ux_account_filedate
            ON {TABLE_NAME} (AccountNumber, FileDate)
        """)
        conn.commit()
        print("Unique index created")
    except pyodbc.Error:
        # Index already exists
        pass

    conn.close()