import os
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import utils
import navigation


def count_files(path: str) -> Tuple[bool, int]:
"""
Recursive counting of files in a Windows directory
    
    Uses navigation.list_directory() to get the contents of the directory
    Recursively traverses subdirectories, counting the total number of files
"""
    if not os.path.exists(path):
        return False, 0

    total_files = 0
    # Getting the contents of the current directory
    success, items = navigation.list_directory(path)

    if not success:
        return False, 0

    for item in items:
        # Creating the full path to the element
        item_path = os.path.join(path, item['name'])

        if item['type'] == 'directory':
            # Recursive call for subdirectories
            sub_success, sub_count = count_files(item_path)
            if sub_success:
                total_files += sub_count
        else:
            # Counting the file
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
        # nonlocal allows you to change a variable from an external function
        nonlocal total_size

        # Getting the contents of the current directory
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])

            # Skip symlinks to avoid loops
            if os.path.islink(item_path):
                continue

            if item['type'] == 'directory':
                # Recursive traversal of subdirectories
                recursive_calc(item_path)
            else:
                # Skip Windows system files
                if item['name'].lower() in ['pagefile.sys', 'hiberfil.sys',
                                            'swapfile.sys']:
                    continue
                try:
                    # We get the file size and add it to the total amount
                    total_size += os.path.getsize(item_path)
                except (OSError, PermissionError):
                    # Some files may be unreadable in size
                    continue

    # Starting the recursive calculation
    recursive_calc(path)
    return True, total_size


def analyze_windows_file_types(path: str) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """
    File type analysis based on Windows extensions
    
        Collects statistics on extensions specific to Windows:
        .exe, .dll, .msi, .bat, .ps1, .docx, .xlsx, etc.
        Groups files by extensions, calculates the number and total size
    """
    if not os.path.exists(path):
        return False, {}

    # Defining categories of Windows extensions for classification
    windows_extension_categories = {
        'executables': {'.exe', '.dll', '.msi', '.sys', '.com'},
        'scripts': {'.bat', '.cmd', '.ps1', '.vbs', '.js'},
        'office_docs': {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'},
        'archives': {'.zip', '.rar', '.7z', '.cab', '.iso'},
        'system_files': {'.ini', '.inf', '.reg', '.dmp', '.log'},
        'shortcuts': {'.lnk', '.url'},
        'drivers': {'.drv', '.sys', '.vxd'},
        'media': {'.wmv', '.wma', '.asf'}  # Windows Media Formats
    }

    # We collect all Windows-specific extensions in one set
    all_windows_extensions = set()
    for category in windows_extension_categories.values():
        all_windows_extensions.update(category)


    def create_default_stats():
        """Creates a dictionary with standard statistics values"""
        return {
            'count': 0,          # Number of files with this extension
            'total_size': 0,     # Total size in bytes
            'size': 0,           # alias for compatibility (main.py )
            'category': 'other', # Extension category
            'is_windows': False  # Is the extension Windows-specific
        }

    # Using defaultdict to automatically create records
    extensions_stats = defaultdict(create_default_stats)

    
    def collect_extensions(current_path: str) -> None:
        """Recursive collection of statistics on file extensions"""
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])

            if item['type'] == 'directory':
                # Recursively traversing subdirectories
                collect_extensions(item_path)
            else:
                # Extract the file extension
                filename = item['name']
                if '.' in filename:
                    # We take the last part after the dot and add the dot itself
                    ext = '.' + filename.lower().split('.')[-1]
                else:
                    ext = 'без расширения'

                # Defining the file category
                category = 'other'
                is_windows = ext in all_windows_extensions

                # Looking for a category in the dictionary of Windows extensions
                for cat_name, cat_exts in windows_extension_categories.items():
                    if ext in cat_exts:
                        category = cat_name
                        break

                # Getting the file size
                try:
                    file_size = os.path.getsize(item_path)
                except (OSError, PermissionError):
                    file_size = 0

                # Updating statistics for this extension
                stats = extensions_stats[ext]
                stats['count'] += 1
                stats['total_size'] += file_size
                stats['size'] = stats['total_size']
                stats['category'] = category
                stats['is_windows'] = is_windows

    # Starting statistics collection
    collect_extensions(path)

    # Convert defaultdict to a regular dictionary
    result = dict(extensions_stats)
    
    # Add formatted size for each extension
    for ext in result:
        stats = result[ext]
        stats['formatted_size'] = utils.format_size(stats['total_size'])
        # Synchronize the alias (in case the dict came from outside)
        stats['size'] = stats['total_size']

    # Sort extensions by the number of files (in descending order)
    sorted_items = sorted(result.items(), key=get_item_count, reverse=True)
    sorted_result = dict(sorted_items)

    return True, sorted_result


def get_windows_file_attributes_stats(path: str) -> Dict[str, int]:
    """
    Statistics on Windows file attributes
    
    Analyzes file attributes: hidden, system, read-only
    Uses utils.is_hidden_windows_file() and other checks
    Returns statistics: {'hidden': X, 'system': Y, 'readonly':Z, 'archive': W}
    """
    stats = {
        'hidden': 0,    # Hidden files
        'system': 0,    # System files
        'readonly': 0,  # Read-only files
        'archive': 0    # Archived files
    }

    def collect_attributes(current_path: str) -> None:
        """Recursive collection of statistics on file attributes"""
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])

            # We check only files (not folders)
            if item['type'] == 'file':
                try:
                    #1. Checking hidden files
                    if utils.is_hidden_windows_file(item_path):
                        stats['hidden'] += 1

                    #2. Checking system files by extension and location
                    filename = item['name'].lower()
                    dirname = os.path.dirname(item_path).lower()

                    # System files are usually located in system folders
                    if (filename.endswith(('.sys', '.dll', '.drv')) and
                       ('windows' in dirname or 'system32' in dirname or
                        'winnt' in dirname)):
                        stats['system'] += 1

                    #3. Checking read-only files
                    if not os.access(item_path, os.W_OK):
                        stats['readonly'] += 1

                    #4. Checking archived files by extension
                    if filename.endswith(('.zip', '.rar', '.7z', '.tar',
                                          '.gz', '.cab')):
                        stats['archive'] += 1

                except (OSError, PermissionError):
                    #4. Checking archived files by extension
                    continue
            else:
                # If it's a folder, recursively bypass it
                collect_attributes(item_path)

    # Start collecting statistics if the path exists
    if os.path.exists(path):
        collect_attributes(path)

    return stats


def get_item_count(item_tuple):
    """
    Auxiliary function for getting the number of files from an element
    
    Accepts a tuple (extension, statistics) and returns the number of files
    Used as the sorting key in analyze_windows_file_types()
    """
    # item_tuple[1] is a dictionary of statistics, ['count'] is the number of files
    return item_tuple[1]['count']


def show_windows_directory_stats(path: str) -> bool:
    """
    Comprehensive output of Windows catalog statistics
    
    Uses ALL of the above analysis functions
    Displays summary information about the catalog:
    - Total number of files and folders
    - Distribution by file type
    - Attribute statistics
    - Largest files
    Returns True on success of
    """
    if not os.path.exists(path):
        print(f"Путь не существует: {path}")
        return False

    # Header output
    print(f"\nСТАТИСТИКА КАТАЛОГА: {path}")
    print("=" * 60)

    #1. General information (files and size)
    print("\n1. ОБЩАЯ ИНФОРМАЦИЯ:")
    print("-" * 40)

    success_files, file_count = count_files(path)
    if success_files:
        print(f"Файлов: {file_count}")

    success_size, total_bytes = count_bytes(path)
    if success_size:
        print(f"Общий размер: {utils.format_size(total_bytes)}")

    #2. Distribution by file type
    print("\n2. ТИПЫ ФАЙЛОВ (ТОП-5):")
    print("-" * 40)

    success_types, types_stats = analyze_windows_file_types(path)
    if success_types and types_stats:
        # Sorting and taking the top 5 most common extensions
        sorted_items = sorted(types_stats.items(),
                              key=get_item_count,
                              reverse=True)[:5]
        for ext, stats in sorted_items:
            print(f"  {ext}: {stats['count']} файлов, {stats['formatted_size']}")

    # 3. Statistics on file attributes
    print("\n3. АТРИБУТЫ ФАЙЛОВ:")
    print("-" * 40)

    attr_stats = get_windows_file_attributes_stats(path)
    for attr_name, attr_value in attr_stats.items():
        print(f"  {attr_name}: {attr_value}")

    #4. Search for the largest files
    print("\n4. КРУПНЕЙШИЕ ФАЙЛЫ (ТОП-3):")
    print("-" * 40)

    largest_files = []

    def get_file_size(item):
        """Auxiliary function for getting the file size from the dictionary"""
        return item['size']

    def find_large_files(current_path: str,
                         file_list: list,
                         max_files: int = 3) -> None:
        """Recursive search for large files in the directory"""
        success, items = navigation.list_directory(current_path)
        if not success:
            return

        for item in items:
            item_path = os.path.join(current_path, item['name'])


            if item['type'] == 'file':
                try:
                    file_size = os.path.getsize(item_path)
                    # Adding information about the file to the list
                    file_list.append({
                        'path': item_path,
                        'name': item['name'],
                        'size': file_size
                    })

                    # Sort by size (descending)
                    file_list.sort(key=get_file_size, reverse=True)
                    # Leaving only the max_files of the largest ones
                    if len(file_list) > max_files:
                        file_list.pop()  # Delete the smallest one
                except (OSError, PermissionError):
                    continue
            else:
                # Recursively searching in subdirectories
                find_large_files(item_path, file_list, max_files)

    # Starting the search for large files
    find_large_files(path, largest_files, 3)

    if largest_files:
        # Output the found files with formatting
        for i, file_info in enumerate(largest_files, 1):
            filename = file_info['name']
            # Truncating long file names
            if len(filename) > 30:
                filename = filename[:27] + "..."
            size_str = utils.format_size(file_info['size'])
            print(f"  {i}. {filename:<35} {size_str}")
    else:
        print(" Не найдено")

    print("\n" + "=" * 60)
    return True
