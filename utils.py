import os
import platform
from pathlib import Path
from typing import Union, List, Tuple

PathString = Union[str, Path]



def is_windows_os() -> bool:
    '''
    The function verifies that the program is running on Windows
    
    Return:
        bool:
            -True: if running on Windows
            -False: if it is not running on Windows
    '''
    return platform.system() == 'Windows'



def validate_windows_path(path: PathString) -> Tuple[bool, str]:
    '''
    The function checks the correctness of the path for the Windows operating system
    
    Args:
        path (PathString): the path to the file or directory to check
    
    Returns:
        Tuple[bool, str]:
            - (True, "): if the path is valid
            - (False, 'error message'): if the path is invalid
    '''
    path_str = str(path)

    # Checking forbidden characters
    forbidden_chars = '/:*?"<>|'
    for char in forbidden_chars:
        if char in path_str:
            return (False, f'Путь содержит запрещенный символ')

    # Checking the path length
    if len(path_str) > 260:
        return (False, f'Длина пути превышает 260 символов')

    # Checking for the existence of a path
    if not os.path.exists(path_str):
        return (False, 'Путь не существует')

    return (True, '')



def format_size(size_bytes: int) -> str:
    '''
    The function formats the file size from bytes into KB, MB, and GB lines
    
    Args:
        size_bytes (int): the size in bytes to format
    
    Returns:
        str:
        - Size in bytes if less than 1 KB (example: "512 B")
        - Size in KB if less than 1 MB (example: "2.5 KB")
        - Size in MB if less than 1 GB (example: "150.3 MB")
        - Size in GB if 1 GB or more (example: "3.7 GB")
    '''

    if size_bytes < 1024:
        return f'{size_bytes} B'
    if size_bytes < 1024**2:
        return f'{round(size_bytes / 1024, 1)} KB'
    if size_bytes < 1024**3:
        return f'{round(size_bytes / 1024**2, 1)} MB'
    return f'{round(size_bytes / 1024**3, 1)} GB'



def get_parent_path(path: PathString) -> str:
    '''Получение родительского каталога с учетом Windows путей'''
    # Вернуть путь к родительскому каталогу
    # Учесть особенности: C:\ → C:\, C:\Users → C:\
    # Использовать os.path.dirname с учетом Windows

    path_str = str(path)

    # Если путь уже корень диска (сам себе родитель)
    if len(path_str) == 3 and path_str.endswith(':\\'):
        # endswith - проверяет заканчивается ли строка указанным суффиксом
        return path_str

    # Получаем родительскую директорию (находит родительский каталог)
    parent = os.path.dirname(path_str)

    # Если родитель пустой (выдаёт ''), значит это уже корень
    if not parent:
        # Возвращаем путь с добавлением разделителя (os.sep - это системный разделитель пути)
        return path_str + os.sep if not path_str.endswith(os.sep) else path_str

    return parent



def safe_windows_listdir(path: PathString) -> List[str]:
    '''Безопасное получение содержимого каталога в Windows'''
    # Вернуть список элементов каталога или пустой список при ошибке
    # Обрабатывать Windows-specific ошибки:
    # - PermissionError (отказ в доступе)
    # - FileNotFoundError
    # - OSError для длинных путей
    path_str = str(path)
    try:
        # Проверяем, что путь существует и это директория
        if not os.path.exists(path):
            return []

        if not os.path.isdir(path):
            return []

        # Получаем список содержимого (файлов и папок)
        return os.listdir(path)

    except PermissionError:
        print(f'Отказано в доступе к: {path}')
        return []

    except FileNotFoundError:
        print(f'Директория не найдена: {path}')
        return []

    except OSError as e:
        # Обработка ошибок связанных с длинными путями
        if 'слишком длинный' in str(e).lower() or 'too long' in str(e).lower():
            print(f'Путь слишком длинный: {path}')
        else:
            print(f'Системная ошибка при доступе к {path}: {e}')
        return []

    except Exception as e:
        # Остальные ошибки
        print(f'Неизвестная ошибка при чтении {path}: {e}')
        return []



def is_hidden_windows_file(path: PathString) -> bool:
    '''Проверка является ли файл скрытым в Windows'''

    path_str = str(path)

    # Проверка существования
    if not os.path.exists(path_str):
        return False

    file_info = os.stat(path_str)


    # Проверяем, есть ли атрибут st_file_attributes у объекта
    if hasattr(file_info, 'st_file_attributes'):
        # Получаем атрибуты файла
        file_attrs = file_info.st_file_attributes
        # Проверяем бит hidden (значение 2)
        if file_attrs & 2:
            return True

    return False