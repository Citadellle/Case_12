import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
# Importing architect functions
import utils
#ctypes allows you to call functions from Windows DLL libraries directly in Python
import ctypes
# Library for getting string constants
import string


def get_current_drive() -> str:
    '''
    The function returns the current disk in the Windows operating system
    
    Returns:
        str:
            The letter of the current disk with a colon (for example, 'C:')
    '''

    # Returns the absolute path to the current working directory
    current_dir = os.getcwd()

    #splitdrive returns a tuple (the disk name, the rest of the path), separating the path
    # For example: os.path.splitdrive('C:\User\Documents\file.txt')
    # ->
    # ('C:', '\User\Documents\file.txt')
    drive = os.path.splitdrive(current_dir)[0]

    return drive


def list_available_drives() -> List[str]:
    '''
    The function returns a list of all available disks in the Windows operating system
    
    Returns:
        List[str]:
            A list of available drive letters with a colon (['C:', 'D:', 'E:'])
    '''
    drives = []
    
    try:          
        # We get a bitmask of disks (a 32-bit number, where each bit represents a disk)
        # If bit = 1, then the corresponding disk exists
        drives_bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        
        i = 0
        # We go through all the letters from A to Z
        # Each letter is assigned a number: 0 for A, 1 for B, ... 25 for Z
        for letter in string.ascii_uppercase:
            # << is the bitwise shift operator of the left operator to the left 
            # for the number of positions specified by the right operator
            # For example, for i=2: 1 (00000001) << 2 = 4 (00000100 in binary)
            mask = 1 << i
            
            # Check the bit corresponding to the letter
            if drives_bitmask & mask:
                drive_name = f'{letter}:'
                drives.append(drive_name)
            
            i += 1
        
        return drives
    
    except:
        return []


def list_directory(path: str) -> Tuple[bool, List[Dict[str, Any]]]:
    '''
    The function displays the contents of a catalog in Windows with detailed information about each item.
    
    Args:
        path (str): the path to the directory whose contents you want to display
    
    Returns:
        Tuple[bool, List[Dict[str, Any]]]:
            - (True, list_elements): if the operation is successful
            - (False, []): if an error occurs
    
    The structure of the item in the returned list:
        {
            'name': str, # file or folder name
            'type': str, # element type: 'file' or 'directory'
            'size': str, # formatted size (for files) or 0 (for folders)
            'modified': str, # last modified date in 'YYYY-MM-DD' format
            'hidden': bool # is the element hidden
        }
    '''

    data_dir = []
    
    # Checking the path
    valid, _ = utils.validate_windows_path(path)
    if not valid:
        return False, []
    
    # Check the existence of a path
    if not os.path.exists(path):
        return False, []
    
    try:
        # Getting a list of files and folders (names, without full path)
        items = utils.safe_windows_listdir(path)
        
        for item in items:
            # Getting the full path to the element
            full_path = os.path.join(path, item)
            
            try:
                #Element name
                item_name = item

                #Element type
                if os.path.isdir(full_path):
                    item_type = 'directory'
                else:
                    item_type = 'file'

                # Element size
                try:
                    if item_type == 'file':
                        # We get the size of the element in bytes
                        size = os.path.getsize(full_path)
                        # Format the size to a convenient look
                        item_size = utils.format_size(size)
                    else:
                        item_size = 0
                except:
                    item_size = 0
                
                # The time of the last change
                try:
                    # We get the time of the last change as a float, the number of seconds since 1970
                    mod_time = os.path.getmtime(full_path)
                    # We bring the time to the desired form
                    item_modified = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d')
                except:
                    item_modified = 'N/A'

                # Checking for a hidden file
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
       
        # We are returning the collected dictionaries, not the raw names.
        return True, data_dir
        
    except:
        return False, []


def format_directory_output(items: List[Dict[str, Any]]) -> None:
    '''
    The function of formatted output of directory contents to the Windows console
    
    Args:
        items (List[Dict[str, Any]]): A list of catalog items obtained from list_directory()
            Each item must contain the keys:
            - 'name': str - the name of the file/folder
            - 'type': str - type ('file' or 'directory')
            - 'size': str - size (formatted string or number)
            - 'modified': str - date of change in the format 'YYYY-MM-DD'
            - 'hidden': bool - flag of the hidden element
    
    Conclusion:
        Formatted table in the console with columns:
        - TYPE (8 characters): FILE or DIR
        - NAME (45 characters): The element name is truncated if it is longer than 38 characters.
        - SIZE (15 characters): formatted file size or 0 for folders
        - CHANGE (22 characters): the date of the last change
        - HIDDEN (10 characters): "Hidden" or "Not hidden"
    '''

    if not items:
        print('Каталог пуст')
        return
    
    print('-' * 100)
    
    # Column headers
    print(f'{'ТИП':<8} {'ИМЯ':<45} {'РАЗМЕР':<15} {'ИЗМЕНЕНИЕ':<22} {'СКРЫТЫЙ':<10}')
    print('-' * 100)
    
    # Output of elements
    for item in items:
        # Type
        if item['type'] == 'file':
            item_type = 'FILE'
        else:
            item_type = 'DIR'
        
        # Name
        item_name = item['name']
        if len(item_name) > 38:
            item_name = item_name[:35] + '...'

        # Size
        item_size = item['size']

        # Modified
        item_modified = item['modified']
        
        # Hidden
        if item['hidden']:
            item_hidden = 'Скрыт'
        else:
            item_hidden = 'Не скрыт'
        
        print(f'{item_type:<8} {item_name:<45} {item_size:<15} {item_modified:<22} {item_hidden:<10}')


def move_up(current_path: str) -> str:
    '''
    The function navigates to the parent directory or switches disks in Windows
    
    Args:
        current_path (str): the current path in the file system
    
    Returns:
        str: the new path after performing the transition operation
    
    The logic of the work:
        1. If the current path is NOT the root of the disk:
           - Goes to the parent directory
           - Checks the validity of the new path
           - Returns a new path or leaves the current one in case of an error
        
        2. If the current path IS the root of the disk (for example, 'C:\\'):
           - Gets a list of available disks in the system
           - If there is only one disk: it remains on the current disk
           - If there are several disks: cycles to the next available disk
           - Returns the path to the root of the new disk
    '''
    # Getting the path to the parent directory
    parent_path = utils.get_parent_path(current_path)

    # Normal upward transition if the parent is different from the current path
    if parent_path != current_path:
        valid, _ = utils.validate_windows_path(parent_path)
        if valid:
            return parent_path
        else:
            return current_path

    # If parent_path == current_path, then we are at the root of the disk
    # Getting a list of available disks (['C:', 'D:', ...])
    drives = list_available_drives()

    if not drives:
        return current_path

    # If there is only one disk, then we stay on it
    if len(drives) == 1:
        return current_path
    
    # Defining the current disk
    current_drive = os.path.splitdrive(current_path)[0]
    if not current_drive:
        current_drive = get_current_drive()

    # Find the index of the current disk in the list
    try:
        drive_index = drives.index(current_drive)
    except:
        drive_index = 0

    # Switching to the next disk (cyclic)
    new_drive = drives[(drive_index + 1) % len(drives)]
    new_path = new_drive + "\\"

    if not os.path.exists(new_path):
        return current_path

    return new_path


def move_down(current_path: str, target_dir: str) -> Tuple[bool, str]:
    '''
    The function navigates to the specified subdirectory in the Windows operating system
    
    Args:
        current_path (str): the current path in the file system
        target_dir (str): the name of the subdirectory to go to
    
    Returns:
        Tuple[bool, str]:
            - (True, new_put): if the transition is completed successfully
            - (False, current path): if the transition failed
    '''
    
    # Forming a new path
    new_path = os.path.join(current_path, target_dir)
    
    # Validation check
    is_valid, _ = utils.validate_windows_path(new_path)
    if not is_valid:
        return False, current_path
    
    # Checking the existence of a directory
    if not os.path.isdir(new_path):
        return False, current_path
    
    return True, new_path


def get_windows_special_folders() -> Dict[str, str]:
    '''
    The function returns the paths to special folders of the Windows operating system
    
    Returns:
        Dict[str, str]:
            - Key: readable folder name (for example, 'Desktop', 'Downloads')
            - Value: full path to the folder in the file system
    
    Folders to collect:
    
    User folders (from the USERPROFILE environment variable):
        - Desktop: User's desktop
        - Downloads: Downloads folder
        - Documents: User's documents
        - Music: Music files
        - Pictures: Images
        - Videos: Video files
        - AppData: Application data
        - Local/AppData: Local application data
        - Roaming/AppData: Roaming application data (synced)
    
    System folders:
        - Windows: Windows Directory
        - System32: System Libraries (64-bit)
        - SysWOW64: System Libraries (32-bit on a 64-bit system)
        - ProgramFiles: Program files (64-bit)
        - ProgramFilesX86: Program files (32-bit)
    '''
    special_dir = {}
    
    # User folders
    # Getting the path to the current user's profile
    user_profile = os.environ.get('USERPROFILE', '')
            
    user_special = {
        'Desktop' : 'Desktop',
        'Downloads' : 'Downloads',
        'Documents' : 'Documents',
        'Music' : 'Music',
        'Pictures' : 'Pictures',
        'Videos' : 'Videos',
        'AppData' : 'AppData',
        'Local/AppData' : 'AppData\\Local',
        'Roaming/AppData' : 'AppData\\Roaming',
    }

    for name, path in user_special.items():
        # Forming a new path
        full_path = os.path.join(user_profile, path)
        # Checking the existence of a path
        if os.path.exists(full_path):
            special_dir[name] = full_path


    # System folders
    windows = os.environ.get('SystemRoot', '')

    special_dir['Windows'] = windows
    special_dir['System32'] = os.path.join(windows, 'System32')
    special_dir['SysWOW64'] = os.path.join(windows, 'SysWOW64')

    special_dir['ProgramFiles'] = os.environ.get('ProgramFiles', '')
    special_dir['ProgramFilesX86'] = os.environ.get('ProgramFiles(x86)', '')    

    return special_dir
