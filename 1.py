import datetime

# Получаем текущее время
current_time = datetime.datetime.now()

# Форматируем время в строку (например, 'часы:минуты:секунды')
formatted_time = current_time.strftime("%H:%M:%S")

# Выводим текущее время
print("Текущее время:", formatted_time)
