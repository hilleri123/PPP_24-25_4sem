import re
import pandas as pd


def load_table(table_name):
    table = pd.read_csv(f"csv_files/{table_name}/{table_name}.csv", encoding='utf-8')
    return table


def filter_df_by_columns(df, columns):
    if columns == '*':
        return df
    else:
        lst = [i.strip() for i in columns.split(',')]
        return df[lst]


def parse_sql_query(sql_query):
    columns = None
    table_name = None
    condition = None

    pattern = r"SELECT\s+(.*?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*?))?(?:\s*;)?$"
    match = re.match(pattern, sql_query, re.IGNORECASE)

    if match:
        if match.group(1):
            columns = match.group(1).strip()
        else:
            raise Exception("Columns were not specified")
        if match.group(2):
            table_name = match.group(2).strip()
        else:
            raise Exception("Table name was not specified")
        if match.group(3):
            condition = match.group(3).strip()
    else:
        raise Exception("Not a sql pattern")

    return columns, table_name, condition


def process_query(query):
    try:
        columns, table_name, condition = parse_sql_query(query)
        df = load_table(table_name)
        if condition is not None:
            df = df.query(condition)
        return filter_df_by_columns(df, columns).to_csv(index=False)
    except Exception as e:
        return 'Incorrect query: ' + str(e)
