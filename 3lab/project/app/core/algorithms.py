
import hashlib


def levenshtein_distance(str_1: str, str_2: str) -> int:
    """
    Вычисляет расстояние Левенштейна между двумя строками.
    """
    n, m = len(str_1), len(str_2)
    if n > m:
        str_1, str_2 = str_2, str_1
        n, m = m, n

    current_row = list(range(n + 1))  # Используем list для изменяемости

    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if str_1[j - 1] != str_2[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


# Эти функции теперь могут быть использованы в Celery задаче
# Они принимают уже разделенный список слов
def levenshtein_search_on_list(word: str, corpus_words_list: list[str]) -> list[dict]:
    """
    Применяет расстояние Левенштейна к списку слов.
    Возвращает список словарей {'word': слово, 'distance': расстояние}.
    Сортировка не производится здесь, предполагается, что она будет в вызывающем коде (Celery задаче).
    """
    results = [{"word": w, "distance": levenshtein_distance(word, w)} for w in corpus_words_list]
    return results


def signature_hashing_on_list(word: str, corpus_words_list: list[str]) -> list[dict]:
    """
    Применяет хеширование по сигнатуре к списку слов.
    Возвращает список словарей {'word': слово, 'distance': расстояние_хеша}.
    Использует 'distance' как ключ для единообразия с Левенштейном.
    Сортировка не производится здесь.
    """
    word_hash_obj = hashlib.md5(word.encode('utf-8'))
    word_h = int(word_hash_obj.hexdigest(), 16)

    results = []
    for w in corpus_words_list:
        corpus_word_hash_obj = hashlib.md5(w.encode('utf-8'))
        corpus_word_h = int(corpus_word_hash_obj.hexdigest(), 16)
        results.append({"word": w, "distance": abs(word_h - corpus_word_h)})

    return results