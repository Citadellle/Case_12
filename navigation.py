import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
import utils  # Импорт функций архитектора


def get_current_drive() -> str:
    '''Получение текущего диска Windows'''

    try:
        # Возвращает абсолютный путь к текущей рабочей директории
        current_dir = os.getcwd()

        # Возвращает кортеж (имя диска, остальной путь)
        # Например: os.path.splitdrive('C:\User\Documents\file.txt')
        # ->
        # ('C:', '\User\Documents\file.txt')
        drive = os.path.splitdrive(current_dir)[0]
        return drive
    
    except:
        return 'C:'



def list_available_drives() -> List[str]:
    '''Получение списка доступных дисков Windows'''

    # ctypes позволяет вызывать функции из DLL библиотек Windows напрямую в Python
    import ctypes
    # Библиотека для получения строковых констант
    import string

    drives = []
    
    try:          
        # Получаем битовую маску дисков (32 битное число, где каждый бит представляет диск)
        # Если бит = 1, значит, соответствующий диск существует
        drives_bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        
        i = 0
        # Проходим по всем буквам от A до Z
        # enumerate дает номер каждой букве: 0 для A, 1 для B, ... 25 для Z
        for letter in string.ascii_uppercase:
            # << - оператор побитового сдвига левого оператора влево 
            # на количество позиций, указанное правым оператором
            # Например для C (i=2): 1 (00000001) << 2 = 4 (00000100 в двоичной)
            mask = 1 << i
            
            # Проверяем соответствующий букве бит
            if drives_bitmask & mask:
                drive_name = f'{letter}:'
                drives.append(drive_name)
            
            i += 1
        
        return drives
    
    except:
        return []



def list_directory(path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    '''Отображение содержимого каталога в Windows'''

    data_dir = []
    
    # Проверяем путь
    valid, _ = utils.validate_windows_path(path)
    if not valid:
        return False, []
    
    # Проверяем существование пути
    if not os.path.exists(path):
        return False, []
    
    try:
        # Получаем список файлов и папок
        items = utils.safe_windows_listdir(path)
        
        for item in items:
            # Получаем полный путь до элемента
            full_path = os.path.join(path, item)
            
            try:
                #Имя элемента
                item_name = item

                # Тип элемента
                if os.path.isdir(full_path):
                    item_type = 'directory'
                else:
                    item_type = 'file'

                # Размер элемента
                try:
                    if item_type == 'file':
                        # Получаем размер элемента в байтах
                        size = os.path.getsize(full_path)
                        # Форматируем размер к удобному виду
                        item_size = utils.format_size(size)
                    else:
                        item_size = 0
                except:
                    item_size = 0
                
                # Время последнего изменения
                try:
                    # Получаем время последнего изменения в виде float, количество секунды с 1970 года 
                    mod_time = os.path.getmtime(full_path)
                    # Приводим время к нужному виду
                    item_modified = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                except:
                    item_modified = 'N/A'

                # Проверка на скрытый файл
                item_hidden = utils.is_hidden_windows_file(full_path)
                

                data_dir.append({
                    'name' : item_name,
                    'type' : item_type,
                    'size' : item_size,
                    'modified' : item_modified,
                    'hidden' : item_hidden
                })
                
            except:
                continue
       
        return True, items
        
    except:
        return False, []



def format_directory_output(items: List[Dict[str, Any]]) -> None:
    '''Форматированный вывод содержимого каталога для Windows'''

    if not items:
        print('Каталог пуст')
        return
    
    print('-' * 100)
    
    # Заголовки колонок
    print(f'{'ТИП':<8} {'ИМЯ':<45} {'РАЗМЕР':<15} {'ИЗМЕНЕНИЕ':<22} {'СКРЫТЫЙ':<10}')
    print('-' * 100)
    
    # Вывод элементов
    for item in items:
        # Тип
        if item['type'] == 'file':
            item_type = 'FILE'
        else:
            item_type = 'DIR'
        
        # Имя
        item_name = item['name']
        if len(item_name) > 38:
            item_name = item_name[:35] + '...'

        # Размер
        item_size = item['size']

        # Изменение
        item_modified = item['modified']
        
        # Скрыт
        if item['hidden']:
            item_hidden = 'Скрыт'
        else:
            item_hidden = 'Не скрыт'
        
        print(f'{item_type:<8} {item_name:<45} {item_size:<15} {item_modified:<22} {item_hidden:<10}')



def move_up(current_path: str) -> str:
    '''
    Переход в родительский каталог в Windows

    - Если parent_path != current_path — обычный переход вверх.
    - Если на корне диска (например 'C:\\') — переключаемся на следующий доступный диск
      в списке, циклически (например, C: -> D:).
    '''
    # Получаем путь к родительскому каталогу
    parent_path = utils.get_parent_path(current_path)

    # Обычный переход вверх, если родитель отличается от текущего пути
    if parent_path != current_path:
        valid, _ = utils.validate_windows_path(parent_path)
        if valid:
            return parent_path
        else:
            return current_path

    # Если parent_path == current_path, значит мы в корне диска
    # Получаем список доступных дисков (['C:', 'D:', ...])
    drives = list_available_drives()

    if not drives:
        return current_path

    # Если всего только один диск, то остаемся на нем
    if len(drives) == 1:
        return current_path
    
    # Определяем текущий диск
    current_drive = os.path.splitdrive(current_path)[0]
    if not current_drive:
        current_drive = get_current_drive()

    # Найдем индекс текущего диска в списке
    drive_index = drives.index(current_drive)

    # Переход на следующий диск
    new_drive = drives[drive_index + 1]
    new_path = f'{new_drive}'

    if not os.path.exists(parent_path):
        return current_path
    
    return new_path



def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    '''Переход в указанный подкаталог в Windows'''
    
    # Формирование нового пути
    new_path = os.path.join(current_path, target_dir)
    
    # Проверка валидность
    is_valid, _ = utils.validate_windows_path(new_path)
    if not is_valid:
        return False, current_path
    
    # Проверка существования директории
    if not utils.safe_windows_listdir(new_path):
        return False, current_path
    
    return True, new_path



def get_windows_special_folders() -> Dict[str, str]:
    '''Получение путей к специальным папкам Windows'''
    special_dir = {}
    
    user_profile = os.environ.get('USERPROFILE', '')
            
    special = {
        'Desktop' : 'Desktop',
        'Downloads' : 'Downloads',
        'Documents' : 'Documents',
        'Music' : 'Music',
        'Pictures' : 'Pictures',
        'Videos' : 'Videos',
        'AppData' : 'AppData',
        'Local_AppData' : 'AppData\\Local',
        'Roaming_AppData' : 'AppData\\Roaming',
    }

    for name, path in special.items():
        # Формирование нового пути
        full_path = os.path.join(user_profile, path)
        # Проверка существования пути
        if os.path.exists(full_path):
            special_dir[name] = full_path

    return special_dir