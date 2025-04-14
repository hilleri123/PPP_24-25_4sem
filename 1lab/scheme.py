import json
import pandas as pd
from pathlib import Path


def load_all_csv_files(root_dir='csv_files'):
    dataframes = {}
    root_path = Path(root_dir)

    for csv_file in root_path.glob('**/*.csv'):
        rel_path = csv_file.relative_to(root_path)
        dict_key = rel_path.name.replace(".csv", "")

        df = pd.read_csv(csv_file)

        dataframes[dict_key] = list(df.columns)

    return dataframes


def get_json_scheme():
    scheme = json.dumps(load_all_csv_files())
    return scheme
