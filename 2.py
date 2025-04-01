import random

def computer_guess_the_number():
    print("Компьютер будет угадывать число от 1 до 100.")
    
    # Загадываем случайное число для компьютера
    number_to_guess = random.randint(1, 100)
    low = 1
    high = 100
    attempts = 0

    while True:
        attempts += 1
        
        # Компьютер делает предположение
        guess = random.randint(low, high)
        print(f"Попытка {attempts}: Компьютер думает, что это {guess}")
        
        # Проверяем, угадал ли компьютер число
        if guess == number_to_guess:
            print(f"Компьютер угадал число {number_to_guess} за {attempts} попыток!")
            break
        else:
            # Если предположение неверно, обновляем диапазон
            if guess < number_to_guess:
                print("Компьютер ошибся. Загаданное число больше.")
                low = guess + 1
            else:
                print("Компьютер ошибся. Загаданное число меньше.")
                high = guess - 1

if __name__ == "__main__":
    computer_guess_the_number()
