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
    drivers = ["SQL Server", "ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]
    for driver in drivers:
        try:
            connection_string = f"DRIVER={{{driver}}};SERVER={server};DATABASE={db_name};UID={user};PWD={password}"
            print(f"Attempting to connect using driver: {driver}")
            con = pyodbc.connect(connection_string)
            cursor = con.cursor()
            query = f"SELECT * FROM {table_name}"
            cursor.execute(query)
            rows = cursor.fetchall()
            con.close()
            return rows
        except pyodbc.Error as e:
            print(f"Error with driver '{driver}': {e}")
    return None
