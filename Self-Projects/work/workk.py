def ensure_table_exists(cursor, table_name, col_types):
    if not table_exists(cursor, table_name):
        col_defs = ", ".join([f"[{col}] {dtype}" for col, dtype in col_types.items()])
        create_sql = f"CREATE TABLE [{table_name}] ({col_defs});"
        cursor.execute(create_sql)
        print(f"✅ Created table '{table_name}' with {len(col_types)} columns.")