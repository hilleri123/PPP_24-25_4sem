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


def add_quotes_to_string_values(condition):
    # Разбиваем условие на части по операторам сравнения (=, !=, <, >, <=, >=)
    parts = re.split(r'(\s*=\s*|\s*!=\s*|\s*<\s*|\s*>\s*|\s*<=\s*|\s*>=|\s+LIKE\s+)', condition, flags=re.IGNORECASE)

    # Обрабатываем каждую часть
    for i in range(2, len(parts), 2):
        value = parts[i].strip()
        # Если значение не число и не в кавычках
        if not (value.startswith(("'", '"')) or
                value.replace('.', '', 1).isdigit() or
                value.lower() in ('null', 'true', 'false')):
            parts[i] = f"'{value}'"

    return ''.join(parts)


def process_condition(condition):
    # 1. Добавляем кавычки к строковым значениям
    condition = add_quotes_to_string_values(condition)
    # 2. Заменяем SQL-равенство (=) на Python-равенство (==)
    condition = re.sub(r'(?<!\=)\=(?!\=)', '==', condition)
    return condition


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
            raw_condition = match.group(3).strip()
            condition = process_condition(raw_condition)
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
