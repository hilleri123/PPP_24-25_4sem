import os

def build_data_structure():
    env_vars = dict(os.environ)  # окружение
    path_value = env_vars.get("PATH", "")
    path_dirs = path_value.split(os.pathsep)

    directories_info = []
    for d in path_dirs:
        if not os.path.isdir(d):
            continue
        executables = []
        try:
            for f in os.listdir(d):
                full_path = os.path.join(d, f)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    executables.append(f)
        except PermissionError:
            pass

        directories_info.append({
            "path": d,
            "executables": executables
        })

    return {
        "env_vars": env_vars,
        "directories": directories_info
    }

def update_env(new_vars):
    for key, value in new_vars.items():
        os.environ[key] = value
