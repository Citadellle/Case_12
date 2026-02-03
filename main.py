import os
import sys
from typing import NoReturn
import utils  # Собственный модуль
import navigation  # Модуль инженера навигации
import analysis  # Модуль аналитика
import search  # Модуль эксперта поиска


def check_windows_environment() -> bool:
    """Checking that the program is running on Windows"""
    # Checking that the system is Windows
    if not utils.is_windows_os():
        print("-" * 50)
        print("ОШИБКА: Эта программа предназначена только для Windows!")
        print(f"Текущая операционная система: {sys.platform}")
        print("-" * 50)
        return False
            
    return True
    

def display_windows_banner() -> None:
    """Displaying a banner with information about Windows"""
    print("-" * 80)
    print(" " * 20 + "ФАЙЛОВЫЙ МЕНЕДЖЕР")
    print("-" * 80)

    # Current drive
    current_drive = navigation.get_current_drive()
    print(f"Текущий диск💿: {current_drive}")

    # Available drives
    drives = navigation.list_available_drives()
    print(f"Доступные диски💿: {', '.join(drives)}")

    # Current path
    current_path = os.getcwd()
    print(f"Текущий путь: {current_path}")

    # Special folders
    print("\nСпециальные папки Windows📁:")
    special_folders = navigation.get_windows_special_folders()
    for name, path in special_folders.items():
        if os.path.exists(path):
            print(f"  {name}: {path}")

    print("-" * 80)
    print()


def display_main_menu(current_path: str) -> None:
    """Displaying the main menu for Windows"""
    print(f"\nТекущий путь: {current_path}")
    print("-" * 80)
    print("Доступные диски:")
    print(navigation.list_available_drives())
    print("-" * 80)
    print("Доступные команды:")
    print(" 1. Содержимое текущего каталога 📁")
    print(" 2. Статистика текущей директории 📊")
    print(" 3. Поиск файлов и директорий 🔍")
    print(" 4. Анализ типов файлов 📈")
    print(" 5. Переход в родительский каталог (..) ⬆")
    print(" 6. Переход в подкаталог ⬇")
    print(" 7. Сменить диск 💿")
    print(" 8. Переход в системную папку Windows 🖥 ")
    print(" 0. Завершение работы 🚪")
    print("-" * 80)


def handle_windows_navigation(command: str, current_path: str) -> str:
    """Processing navigation commands in Windows"""
    # Switching to the parent directory
    if command == "5":
        new_path = navigation.move_up(current_path)
        print(f"Переход в: {new_path}")
        return new_path

    # Move to a subdirectory
    elif command == "6":
        dir_name = input("Введите имя подкаталога: ").strip()
        success, new_path = navigation.move_down(current_path, dir_name)
        
        if success:
            print(f"Переход в: {new_path}")
            return new_path
        else:
            print(f"Не удалось перейти в: '{dir_name}'")

    # Change the disk
    elif command == "7":
        i = 1
        drives = navigation.list_available_drives()
        print("Доступные диски: ")
        
        for drive in drives:
            print(f" {i}. {drive}")
            i += 1

        try:
            choice = int(input("Выберите номер диска: "))
            
            if 1 <= choice <= len(drives):
                new_drive = drives[choice - 1]
                new_path = new_drive + "\\"
                valid, error = utils.validate_windows_path(new_path)
                
                if valid:
                    # function for changing the working directory
                    os.chdir(new_path)
                    print(f"Переход на диск: {new_drive}")
                    return os.getcwd()
                else:
                    print(f"Ошибка перехода: {error}")
                    
            else:
                print("Некорректный выбор диска")
                
        except ValueError:
            print("Некорректный ввод")

    # Transfer to a special Windows folder
    elif command == "8":
        print("Специальные папки Windows:")

        # Getting the dict
        special_folders = navigation.get_windows_special_folders()
        # Getting a list of tuples
        folders_list = list(special_folders.items())

        i = 1
        for (name, path) in folders_list:
            if os.path.exists(path):
                print(f"  {i}. {name} ({path})")
                i += 1
                
        try:
            choice = int(input("Выберите номер папки: "))
            
            if 1 <= choice <= len(folders_list):
                name, path = folders_list[choice - 1]
                
                if os.path.exists(path):
                    os.chdir(path)
                    print(f"Переход в: {name}")
                    return os.getcwd()
                    
                else:
                    print(f"Папка '{name}' не найдена")
                    
            else:
                print("Неверный номер")
                
        except ValueError:
            print("Введите номер папки")

    return current_path


def handle_windows_analysis(command: str, current_path: str) -> None:
    """Processing Windows file system analysis commands"""
    # Statistics of the current directory
    if command == "2":
        print(f"\nАнализ директории: {current_path}")
        analysis.show_windows_directory_stats(current_path)

    # File type analysis
    elif command == "4":
        print(f"\nАнализ типов файлов в: {current_path}")
        success, stats = analysis.analyze_windows_file_types(current_path)
        
        if success:
            print("\nСтатистика по расширениям файлов:")
            print("-" * 50)
            
            for ext, data in stats.items():
                # Skip files without extension
                if ext:
                    print(f"{ext} : {data['count']} файлов, {utils.format_size(data['size'])}")
            print("-" * 50)
            
        else:
            print("Ошибка при анализе типов файлов")


def handle_windows_search(command: str, current_path: str) -> None:
    """Processing search commands in Windows"""
    if command == "3":
        search.search_menu_handler(current_path)


def run_windows_command(command: str, current_path: str) -> str:
    """Main command handler using match case"""
    new_path = current_path

    match command:
        case "1":
            import navigation
            print(f"\nСодержимое директории: {current_path}")
            success, items = navigation.list_directory(current_path)
            if success:
                navigation.format_directory_output(items)
            else:
                print("Ошибка при получении содержимого директории")

        case "2" | "4":  
            handle_windows_analysis(command, current_path)

        case "3":  
            handle_windows_search(command, current_path)

        case "5" | "6" | "7" | "8":  
            new_path = handle_windows_navigation(command, current_path)

        case "0":  
            print("Выход из программы...")
            sys.exit(0)

        case _:
            print("Неизвестная команда. Пожалуйста, выберите команду из меню.")

    return new_path


def main() -> NoReturn:
    # Проверяем Windows окружение
    if not check_windows_environment():
        print("\nПрограмма будет завершена.")
        sys.exit(1)

    try:
        import navigation
        import analysis
        import search

    except ImportError as e:
        print(f"ОШИБКА: Не удалось импортировать модуль: {e}")
        print("Убедитесь, что все модули находятся в той же папке.")
        sys.exit(1)
    except OSError as e:
        print(f"ОШИБКА Windows: {e}")
        print("Возможно, не хватает системных библиотек.")
        sys.exit(1)

    # Показываем баннер
    display_windows_banner()

    # Основной цикл
    current_path = os.getcwd()

    while True:
        try:
            display_main_menu(current_path)
            command = input("\nВведите команду: ").strip()
            current_path = run_windows_command(command, current_path)

        # Обработка ошибок
        except PermissionError:
            print("\nОШИБКА: Отказано в доступе!")
            print("Запустите программу от имени администратора или выберите другой путь.")
            
        except KeyboardInterrupt:
            print("\nПрограмма прервана пользователем.")
            break

        except OSError as e:
            if hasattr(e, 'winerror'):
                winerror = e.winerror

                ERROR_ACCESS_DENIED = 5
                ERROR_PATH_NOT_FOUND = 3
                ERROR_INVALID_NAME = 123

                if winerror == ERROR_ACCESS_DENIED:
                    print("\nОШИБКА: Отказано в доступе (код 5)")
                    print("Возможно, у вас нет прав на доступ к этому файлу/папке.")
                elif winerror == ERROR_PATH_NOT_FOUND:
                    print("\nОШИБКА: Путь не найден (код 3)")
                    print("Убедитесь, что путь указан правильно.")
                elif winerror == ERROR_INVALID_NAME:
                    print("\nОШИБКА: Неверное имя файла (код 123)")
                    print("Имя содержит недопустимые символы.")
                else:
                    print(f"\nОШИБКА Windows (код {winerror}): {e}")
            else:
                print(f"\nОШИБКА ОС: {e}")

        except Exception as e:
            print(f"\nНеожиданная ошибка: {e}")
            print("Тип ошибки:", type(e).__name__)
            print("Продолжаем работу...")
            
    sys.exit(0)


if __name__ == "__main__":
    main()
