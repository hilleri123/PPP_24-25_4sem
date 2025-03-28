import numpy as np
from PIL import Image
import base64
import io
# import cv2

def bradley_threshold(image, window_size=5, t=0.15):
    # Нормализуем изображение в диапазон [0, 1]
    image = image.astype(np.float64) / 255.0

    # Создаем интегральное изображение с типом float64
    integral_image = np.cumsum(np.cumsum(image, axis=0), axis=1)

    # Размер изображения
    height, width = image.shape

    # Результат бинаризации
    binarized_image = np.zeros_like(image, dtype=np.uint8)

    # Пройдем по всем пикселям изображения
    for i in range(window_size//2, width - window_size//2):
        for j in range(window_size//2, height - window_size//2):
            # Вычисляем сумму в окне
            x1, y1 = i - window_size//2, j - window_size//2
            x2, y2 = i + window_size//2, j + window_size//2

            window_sum = integral_image[y2, x2] - integral_image[y1, x2] - integral_image[y2, x1] + integral_image[y1, x1]

            # Количество пикселей в окне
            count = window_size * window_size

            # Рассчитываем порог
            threshold = (window_sum / count) * (1 - t)

            # Применяем порог
            if image[j, i] < threshold:
                binarized_image[j, i] = 0
            else:
                binarized_image[j, i] = 255

    return binarized_image

def otsu_threshold(image: np.ndarray) -> np.ndarray:
    # Реализация метода Оцу
    hist = np.histogram(image, bins=256, range=(0, 256))[0]
    hist_norm = hist / hist.sum()
    Q = hist_norm.cumsum()
    bins = np.arange(256)
    fn_min = np.inf
    thresh = -1

    for i in range(1, 256):
        p1, p2 = np.hsplit(hist_norm, [i])
        q1, q2 = Q[i], Q[255] - Q[i]
        if q1 == 0 or q2 == 0:
            continue
        b1, b2 = np.hsplit(bins, [i])  # Split bins into two parts
        m1 = np.sum(p1 * b1) / q1 if q1 > 0 else 0
        m2 = np.sum(p2 * b2) / q2 if q2 > 0 else 0
        v1 = np.sum((b1 - m1) ** 2 * p1) / q1 if q1 > 0 else 0
        v2 = np.sum((b2 - m2) ** 2 * p2) / q2 if q2 > 0 else 0
        fn = v1 * q1 + v2 * q2
        if fn < fn_min:
            fn_min = fn
            thresh = i

    return (image > thresh).astype(np.uint8) * 255

def binarize_image(image_base64: str, algorithm: str) -> str:
    # Декодируем base64
    image_data = base64.b64decode(image_base64)
    image = Image.open(io.BytesIO(image_data)).convert("L")  # Преобразуем в оттенки серого
    image_array = np.array(image)

    # Применяем выбранный алгоритм
    if algorithm == "bradley":
        binarized_array = bradley_threshold(image_array)
    elif algorithm == "otsu":
        binarized_array = otsu_threshold(image_array)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # Преобразуем обратно в base64
    binarized_image = Image.fromarray(binarized_array)
    buffered = io.BytesIO()
    binarized_image.save(buffered, format="PNG")
    binarized_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return binarized_base64