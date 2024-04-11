import os

import pyodbc


def value_or_none(value, condition, _return):
    return value if value != condition else _return


# Connect to MS SQL Server and get data of specific table
def table_data(table_name: str):
    # Get env values
    server = os.environ.get('MSSQL_HOST')
    db_name = os.environ.get('MSSQL_DATABASE')
    user = os.environ.get('MSSQL_USER')
    password = os.environ.get('MSSQL_PASSWORD')
    try:
        connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={db_name};UID={user};PWD={password}'
        print(f"--- --- --- TEST SQL SERVER --- --- ---")
        con = pyodbc.connect(connection_string)
        print(f'{con}')
        cursor = con.cursor()
        print(f'{cursor}')
        query = f'SELECT * FROM {table_name}'
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f'{rows}')
        con.close()
        return rows
    except pyodbc.Error as e:
        print(f"Error: {e}")
        return None
