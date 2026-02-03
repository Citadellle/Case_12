import os
import platform
from pathlib import Path
from typing import Union, List, Tuple
import ctypes

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
            - (True, ''): if the path is valid
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
        - Size in bytes if less than 1 KB
        - Size in KB if less than 1 MB
        - Size in MB if less than 1 GB
        - Size in GB if 1 GB or more
    '''

    if size_bytes < 1024:
        return f'{size_bytes} B'
    
    if size_bytes < 1024**2:
        return f'{round(size_bytes / 1024, 1)} KB'
    
    if size_bytes < 1024**3:
        return f'{round(size_bytes / 1024**2, 1)} MB'
    
    return f'{round(size_bytes / 1024**3, 1)} GB'


def get_parent_path(path: PathString) -> str:
    '''
    The function returns the path to the parent directory, taking into account the features of Windows
    
    Args:
        path (PathString): the source path to find the parent directory for.
    
    Returns:
        str:
            - Path to the parent directory
            - For Windows root paths returns the same path
    
    Example:
        - For the path 'C:\Users ' parent directory: 'C:\'
        - For the path 'C:\' returns 'C:\' (unchanged)
    '''
    path_str = str(path)

    # Windows root path processing
    if os.name == 'nt':
        # Checking if it is the root of the disk
        if len(path_str) == 3 and path_str.endswith(':\\'):
            return path_str

    # Getting the parent directory
    parent = os.path.dirname(path_str)

    # If the parent is empty (''), then the original path is already the root.
    if not parent:
        # Returning the path with the correct separator
        if path_str.endswith(os.sep):
            path_str
        else:
            path_str + os.sep

    return parent


def safe_windows_listdir(path: PathString) -> List[str]:
    '''
    The function safely retrieves directory contents in Windows with error handling
    
    Args:
        path (PathString): the path to the directory whose contents you want to get
    
    Returns:
        List[str]:
            - A list of strings with file names and subdirectories in the specified directory
            - Empty list [] in case of access errors
    
    Handled errors:
        - PermissionError: lack of access rights to the directory
        - FileNotFoundError: the specified directory does not exist
        - OSError: system errors, paths that are too long (>260 characters)
    
    '''
    path_obj = Path(path)
    contents_list = []

    try:
        for child in path_obj.iterdir():
            contents_list.append(str(child))

    # Access error
    except PermissionError:
        print(f'Отказано в доступе к: {path}')
        return []

    # The directory does not exist
    except FileNotFoundError:
        print(f'Директория не найдена: {path}')
        return []

    # Other system errors, including paths that are too long
    except OSError as e:
        print(f'Путь слишком длинный: {path}')
        return []
    
    return contents_list


def is_hidden_windows_file(path: PathString) -> bool:
    '''
    The function checks whether the file is hidden
    
    Args:
        path (PathString): the path to the file to be checked
    
    Returns:
        bool:
            - True: if the file has the "hidden" attribute
            - False: if the file does not have the "hidden" attribute
    
    Note:
        The function uses the Windows API by ctypes to verify file attributes.
        kernel32.dll — this is the main Windows system library containing functions
        for managing files, processes, memory, and other low-level operations.
        
        The principle of operation:
        The GetFileAttributesW function is used, which returns a bitmask of file attributes.
        The value of FILE_ATTRIBUTE_HIDDEN bit (value 0x2) is checked using the bitwise operation: AND (&).
        
        Example (Windows file basic attributes):
        FILE_ATTRIBUTE_READONLY    = 0x1
        FILE_ATTRIBUTE_HIDDEN      = 0x2
        FILE_ATTRIBUTE_SYSTEM      = 0x4
        FILE_ATTRIBUTE_DIRECTORY   = 0x10
        FILE_ATTRIBUTE_ARCHIVE     = 0x20
    '''

    path_str = str(path)

    # Getting the file attributes
    file_atr = ctypes.windll.kernel32.GetFileAttributesW(path_str)

    # Check the hidden bit (FILE_ATTRIBUTE_HIDDEN = 0x2)
    if file_atr & 2:
        return True
    
    return False
