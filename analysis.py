import os
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import utils
import navigation


def count_files(path: str) -> Tuple[bool, int]:
    """
    Рекурсивный подсчет файлов в Windows каталоге
    
    Использует navigation.list_directory() для получения содержимого директории
    Рекурсивно обходит подкаталоги, подсчитывая общее количество файлов
    """
    if not os.path.exists(path):
        return False, 0

    total_files = 0
    # Получаем содержимое текущей директории
    success, items = navigation.list_directory(path)

    if not success:
        return False, 0

    for item in items:
        # Формируем полный путь к элементу
        item_path = os.path.join(path, item['name'])

        if item['type'] == 'directory':
            # Рекурсивный вызов для подкаталогов
            sub_success, sub_count = count_files(item_path)
            if sub_success:
                total_files += sub_count
        else:
            # Считаем файл
            total_files += 1

    return True, total_files


def count_bytes(path: str) -> Tuple[bool, int]:
    """
    Рекурсивный подсчет размера файлов в Windows
    
    Использует count_files() как основу для обхода файловой системы
    Суммирует размеры всех файлов в байтах
    """
    if not os.path.exists(path):
        return False, 0

    total_size = 0

    def recursive_calc(current_path: str) -> None:
        # nonlocal позволяет изменять переменную из внешней функции
        nonlocal total_size

        # Получаем содержимое текущей директории
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])

            # Пропускаем символьные ссылки (symlinks) чтобы избежать циклов
            if os.path.islink(item_path):
                continue

            if item['type'] == 'directory':
                # Рекурсивный обход подкаталогов
                recursive_calc(item_path)
            else:
                # Пропускаем системные файлы Windows
                if item['name'].lower() in ['pagefile.sys', 'hiberfil.sys',
                                            'swapfile.sys']:
                    continue
                try:
                    # Получаем размер файла и добавляем к общей сумме
                    total_size += os.path.getsize(item_path)
                except (OSError, PermissionError):
                    # Некоторые файлы могут быть недоступны для чтения размера
                    continue

    # Запускаем рекурсивный подсчет
    recursive_calc(path)
    return True, total_size


def analyze_windows_file_types(path: str) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """
    Анализ типов файлов с учетом Windows расширений
    
    Собирает статистику по расширениям характерным для Windows:
    .exe, .dll, .msi, .bat, .ps1, .docx, .xlsx и т.д.
    Группирует файлы по расширениям, подсчитывает количество и суммарный размер
    """
    if not os.path.exists(path):
        return False, {}

    # Определяем категории Windows-расширений для классификации
    windows_extension_categories = {
        'executables': {'.exe', '.dll', '.msi', '.sys', '.com'},
        'scripts': {'.bat', '.cmd', '.ps1', '.vbs', '.js'},
        'office_docs': {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'},
        'archives': {'.zip', '.rar', '.7z', '.cab', '.iso'},
        'system_files': {'.ini', '.inf', '.reg', '.dmp', '.log'},
        'shortcuts': {'.lnk', '.url'},
        'drivers': {'.drv', '.sys', '.vxd'},
        'media': {'.wmv', '.wma', '.asf'}  # Windows Media форматы
    }

    # Собираем все Windows-специфичные расширения в один набор
    all_windows_extensions = set()
    for category in windows_extension_categories.values():
        all_windows_extensions.update(category)




    def create_default_stats():
        """Создает словарь со стандартными значениями статистики"""
        return {
            'count': 0,          # Количество файлов с данным расширением
            'total_size': 0,     # Суммарный размер в байтах
            'category': 'other', # Категория расширения
            'is_windows': False  # Является ли расширение Windows-специфичным
        }

    # Используем defaultdict для автоматического создания записей
    extensions_stats = defaultdict(create_default_stats)

    def collect_extensions(current_path: str) -> None:
        """Рекурсивный сбор статистики по расширениям файлов"""
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])

            if item['type'] == 'directory':
                # Рекурсивно обходим подкаталоги
                collect_extensions(item_path)
            else:
                # Извлекаем расширение файла
                filename = item['name']
                if '.' in filename:
                    # Берем последнюю часть после точки и добавляем саму точку
                    ext = '.' + filename.lower().split('.')[-1]
                else:
                    ext = 'без расширения'

                # Определяем категорию файла
                category = 'other'
                is_windows = ext in all_windows_extensions

                # Ищем категорию в словаре Windows-расширений
                for cat_name, cat_exts in windows_extension_categories.items():
                    if ext in cat_exts:
                        category = cat_name
                        break

                # Получаем размер файла
                try:
                    file_size = os.path.getsize(item_path)
                except (OSError, PermissionError):
                    file_size = 0

                # Обновляем статистику для данного расширения
                stats = extensions_stats[ext]
                stats['count'] += 1
                stats['total_size'] += file_size
                stats['category'] = category
                stats['is_windows'] = is_windows

    # Запускаем сбор статистики
    collect_extensions(path)

    # Преобразуем defaultdict в обычный словарь
    result = dict(extensions_stats)
    
    # Добавляем отформатированный размер для каждого расширения
    for ext in result:
        stats = result[ext]
        stats['formatted_size'] = utils.format_size(stats['total_size'])

    # Сортируем расширения по количеству файлов (по убыванию)
    sorted_items = sorted(result.items(), key=get_item_count, reverse=True)
    sorted_result = dict(sorted_items)

    return True, sorted_result


def get_windows_file_attributes_stats(path: str) -> Dict[str, int]:
    """
    Статистика по атрибутам файлов Windows
    
    Анализирует атрибуты файлов: скрытые, системные, только для чтения
    Использует utils.is_hidden_windows_file() и другие проверки
    Возвращает статистику: {'hidden': X, 'system': Y, 'readonly': Z, 'archive': W}
    """
    stats = {
        'hidden': 0,    # Скрытые файлы
        'system': 0,    # Системные файлы
        'readonly': 0,  # Файлы только для чтения
        'archive': 0    # Архивированные файлы
    }

    def collect_attributes(current_path: str) -> None:
        """Рекурсивный сбор статистики по атрибутам файлов"""
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])

            # Проверяем только файлы (не папки)
            if item['type'] == 'file':
                try:
                    # 1. Проверка скрытых файлов
                    if utils.is_hidden_windows_file(item_path):
                        stats['hidden'] += 1

                    # 2. Проверка системных файлов по расширению и расположению
                    filename = item['name'].lower()
                    dirname = os.path.dirname(item_path).lower()

                    # Системные файлы обычно находятся в системных папках
                    if (filename.endswith(('.sys', '.dll', '.drv')) and
                       ('windows' in dirname or 'system32' in dirname or
                        'winnt' in dirname)):
                        stats['system'] += 1

                    # 3. Проверка файлов только для чтения
                    if not os.access(item_path, os.W_OK):
                        stats['readonly'] += 1

                    # 4. Проверка архивных файлов по расширению
                    if filename.endswith(('.zip', '.rar', '.7z', '.tar',
                                          '.gz', '.cab')):
                        stats['archive'] += 1

                except (OSError, PermissionError):
                    # Если нет доступа к файлу, пропускаем его
                    continue
            else:
                # Если это папка, рекурсивно обходим её
                collect_attributes(item_path)

    # Запускаем сбор статистики если путь существует
    if os.path.exists(path):
        collect_attributes(path)

    return stats


def get_item_count(item_tuple):
    """
    Вспомогательная функция для получения количества файлов из элемента
    
    Принимает кортеж (расширение, статистика) и возвращает количество файлов
    Используется как ключ для сортировки в analyze_windows_file_types()
    """
    # item_tuple[1] - это словарь статистики, ['count'] - количество файлов
    return item_tuple[1]['count']


def show_windows_directory_stats(path: str) -> bool:
    """
    Комплексный вывод статистики Windows каталога
    
    Использует ВСЕ вышеперечисленные функции анализа
    Выводит сводную информацию о каталоге:
    - Общее количество файлов и папок
    - Распределение по типам файлов
    - Статистика по атрибутам
    - Крупнейшие файлы
    Возвращает True при успешном выполнении
    """
    if not os.path.exists(path):
        print(f"Путь не существует: {path}")
        return False

    # Вывод заголовка
    print(f"\nСТАТИСТИКА КАТАЛОГА: {path}")
    print("=" * 60)

    # 1. Общая информация (файлы и размер)
    print("\n1. ОБЩАЯ ИНФОРМАЦИЯ:")
    print("-" * 40)

    success_files, file_count = count_files(path)
    if success_files:
        print(f"Файлов: {file_count}")

    success_size, total_bytes = count_bytes(path)
    if success_size:
        print(f"Общий размер: {utils.format_size(total_bytes)}")

    # 2. Распределение по типам файлов
    print("\n2. ТИПЫ ФАЙЛОВ (ТОП-5):")
    print("-" * 40)

    success_types, types_stats = analyze_windows_file_types(path)
    if success_types and types_stats:
        # Сортируем и берем топ-5 самых распространенных расширений
        sorted_items = sorted(types_stats.items(),
                              key=get_item_count,
                              reverse=True)[:5]
        for ext, stats in sorted_items:
            print(f"  {ext}: {stats['count']} файлов, {stats['formatted_size']}")

    # 3. Статистика по атрибутам файлов
    print("\n3. АТРИБУТЫ ФАЙЛОВ:")
    print("-" * 40)

    attr_stats = get_windows_file_attributes_stats(path)
    for attr_name, attr_value in attr_stats.items():
        print(f"  {attr_name}: {attr_value}")

    # 4. Поиск крупнейших файлов
    print("\n4. КРУПНЕЙШИЕ ФАЙЛЫ (ТОП-3):")
    print("-" * 40)

    largest_files = []

    def get_file_size(item):
        """Вспомогательная функция для получения размера файла из словаря"""
        return item['size']

    def find_large_files(current_path: str,
                         file_list: list,
                         max_files: int = 3) -> None:
        """Рекурсивный поиск крупных файлов в директории"""
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])


            if item['type'] == 'file':
                try:
                    file_size = os.path.getsize(item_path)
                    # Добавляем информацию о файле в список
                    file_list.append({
                        'path': item_path,
                        'name': item['name'],
                        'size': file_size
                    })

                    # Сортируем по размеру (по убыванию)
                    file_list.sort(key=get_file_size, reverse=True)
                    # Оставляем только max_files самых больших
                    if len(file_list) > max_files:
                        file_list.pop()  # Удаляем самый маленький
                except (OSError, PermissionError):
                    continue
            else:
                # Рекурсивно ищем в подкаталогах
                find_large_files(item_path, file_list, max_files)

    # Запускаем поиск крупных файлов
    find_large_files(path, largest_files, 3)

    if largest_files:
        # Выводим найденные файлы с форматированием
        for i, file_info in enumerate(largest_files, 1):
            filename = file_info['name']
            # Обрезаем длинные имена файлов
            if len(filename) > 30:
                filename = filename[:27] + "..."
            size_str = utils.format_size(file_info['size'])
            print(f"  {i}. {filename:<35} {size_str}")
    else:
        print("  Не найдено")

    print("\n" + "=" * 60)
    return True