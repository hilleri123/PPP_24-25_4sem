import base64
import json

# Путь к вашему изображению
image_path = "2025-03-28_14-17-11.png"

# Читаем изображение и кодируем его в base64
with open(image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

# Формируем JSON для запроса
request_body = {
    "image": encoded_string,
    "algorithm": "otsu"
}

# Выводим JSON
print(json.dumps(request_body, indent=2))