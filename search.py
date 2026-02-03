import os
import re
from typing import List, Dict, Any

import utils
import navigation
import analysis


def find_files_windows(pattern: str, path: str, case_sensitive: bool = False) -> List[str]:
    """Поиск файлов по шаблону в Windows"""

    pattern = pattern.strip()
    path = path.strip().replace("/", "\\")
    path = os.path.normpath(path)

    regex_special = [".", "^", "$", "+", "{", "}", "[", "]", "(", ")", "|", "\\"]

    reg_ex = ""

    for letter in pattern:
        if letter == "*":
            reg_ex += "(.)*"
        elif letter == "?":
            reg_ex += "(.)"
        else:
            cur = letter
            if case_sensitive == False:
                cur = cur.lower()

            if cur in regex_special:
                reg_ex += "\\" + cur
            else:
                reg_ex += cur
                
    stack = [path]
    visited = set()
    result_files: List[str] = []

    total_files = 0

    while len(stack) > 0:
        current = stack.pop()
        current = current.replace("/", "\\")
        current = os.path.normpath(current)

        if current in visited:
            continue
        visited.add(current)

        dirs, files = navigation.list_directory(current)

        for file_info in files:
            file_name = str(file_info["name"]).strip()
            if len(file_name) == 0:
                continue

            total_files += 1

            if case_sensitive:
                name_to_check = file_name
            else:
                name_to_check = file_name.lower()

            for r_item in re.finditer(reg_ex, name_to_check):
                if r_item.group() == name_to_check:
                    full_path = os.path.join(current, file_name)
                    full_path = full_path.replace("/", "\\")
                    full_path = os.path.normpath(full_path)
                    result_files.append(full_path)

        for dir_name in dirs:
            dir_name = str(dir_name).strip()
            if len(dir_name) == 0:
                continue

            dir_path = os.path.join(current, dir_name)
            dir_path = dir_path.replace("/", "\\")
            dir_path = os.path.normpath(dir_path)
            stack.append(dir_path)

    analysis.count_files(total_files)
    return result_files



def find_by_windows_extension(extensions: List[str], path: str) -> List[str]:
    """Поиск файлов по списку расширений Windows"""

    path = path.strip().replace("/", "\\")
    path = os.path.normpath(path)

    for i in range(len(extensions)):
        extensions[i] = str(extensions[i]).strip().lower()
        if len(extensions[i]) == 0:
            continue
        if extensions[i][0] != ".":
            extensions[i] = "." + extensions[i]

    stack = [path]
    visited = set()

    search_result: List[str] = []
    all_files_for_analysis: List[str] = []

    while len(stack) > 0:
        current = stack.pop()
        current = current.replace("/", "\\")
        current = os.path.normpath(current)

        if current in visited:
            continue
        visited.add(current)

        dirs, files = navigation.list_directory(current)

        for file_info in files:
            file_name = str(file_info["name"]).strip()
            file_type = str(file_info["type"]).strip().lower()

            if len(file_name) == 0:
                continue

            full_path = os.path.join(current, file_name)
            full_path = full_path.replace("/", "\\")
            full_path = os.path.normpath(full_path)

            all_files_for_analysis.append(full_path)

            for ext in extensions:
                if file_type == ext:
                    search_result.append(full_path)

        for dir_name in dirs:
            dir_name = str(dir_name).strip()
            if len(dir_name) == 0:
                continue

            dir_path = os.path.join(current, dir_name)
            dir_path = dir_path.replace("/", "\\")
            dir_path = os.path.normpath(dir_path)
            stack.append(dir_path)

    analysis.analyze_windows_file_types(all_files_for_analysis)

    return search_result


def find_large_files_windows(min_size_mb: float, path: str) -> List[Dict[str, Any]]:
    """Поиск крупных файлов в Windows"""
    path = path.strip().replace("/", "\\")
    path = os.path.normpath(path)

    min_bytes = int(min_size_mb * 1024 * 1024)

    stack = [path]
    visited = set()

    result: List[Dict[str, Any]] = []
    total_bytes = 0

    while len(stack) > 0:
        current = stack.pop()
        current = current.replace("/", "\\")
        current = os.path.normpath(current)

        if current in visited:
            continue
        visited.add(current)

        dirs, files = navigation.list_directory(current)

        for file_info in files:
            file_name = str(file_info["name"]).strip()
            file_type = str(file_info["type"]).strip()

            if len(file_name) == 0:
                continue

            full_path = os.path.join(current, file_name)
            full_path = full_path.replace("/", "\\")
            full_path = os.path.normpath(full_path)

            if os.path.exists(full_path) == False:
                continue

            size_bytes = os.path.getsize(full_path)
            total_bytes += size_bytes

            if size_bytes >= min_bytes:
                size_mb = size_bytes / (1024 * 1024)

                info = {
                    "path": full_path,
                    "size_mb": round(size_mb, 2),
                    "type": file_type
                }
                result.append(info)

        for dir_name in dirs:
            dir_name = str(dir_name).strip()
            if len(dir_name) == 0:
                continue

            dir_path = os.path.join(current, dir_name)
            dir_path = dir_path.replace("/", "\\")
            dir_path = os.path.normpath(dir_path)

            stack.append(dir_path)

    analysis.count_bytes(total_bytes)

    result.sort(key=lambda x: x["size_mb"], reverse=True)

    return result


def find_windows_system_files(path: str) -> List[str]:
    """Поиск системных файлов Windows"""

    path = path.strip().replace("/", "\\")
    path = os.path.normpath(path)

    special = navigation.get_windows_special_folders()

    roots: List[str] = []

    if "Windows" in special:
        roots.append(special["Windows"])
    if "System32" in special:
        roots.append(special["System32"])
    if "SysWOW64" in special:
        roots.append(special["SysWOW64"])
    if "ProgramFiles" in special:
        roots.append(special["ProgramFiles"])
    if "ProgramFilesX86" in special:
        roots.append(special["ProgramFilesX86"])

    if len(roots) == 0:
        roots.append(path)

    system_files: List[str] = []

    for root in roots:
        root = str(root).strip().replace("/", "\\")
        root = os.path.normpath(root)
        if len(root) == 0:
            continue

        found = find_by_windows_extension([".exe", ".dll", ".sys"], root)
        system_files += found

    return system_files



def search_menu_handler(current_path: str) -> bool:
    """Обработчик меню поиска для Windows"""
    current_path = current_path.strip().replace("/", "\\")
    current_path = os.path.normpath(current_path)

    print("\n=== МЕНЮ ПОИСКА (Windows) ===")
    print("Текущий путь: " + current_path)
    print("1) Поиск по шаблону (*, ?)")
    print("2) Поиск по расширениям")
    print("3) Поиск крупных файлов")
    print("4) Поиск системных файлов Windows")
    print("0) Назад")

    choice = input("Выберите пункт: ").strip()

    if choice == "0":
        return True

    if choice == "1":
        pattern = input("Введите шаблон (например: *.txt): ").strip()
        cs_input = input("Учитывать регистр? (y/N): ").strip().lower()
        case_sensitive = False
        if cs_input == "y":
            case_sensitive = True

        results = find_files_windows(pattern, current_path, case_sensitive)
        format_windows_search_results(results, "pattern")
        return True

    if choice == "2":
        raw = input("Введите расширения через запятую (exe, msi, .dll): ").strip()
        parts = raw.split(",")
        exts: List[str] = []
        for p in parts:
            p = p.strip()
            if len(p) > 0:
                exts.append(p)

        results = find_by_windows_extension(exts, current_path)
        format_windows_search_results(results, "extensions")
        return True

    if choice == "3":
        raw = input("Минимальный размер (MB): ").strip().replace(",", ".")
        min_mb = float(raw)

        results = find_large_files_windows(min_mb, current_path)
        format_windows_search_results(results, "large")
        return True

    if choice == "4":
        results = find_windows_system_files(current_path)
        format_windows_search_results(results, "system")
        return True

    print("Неизвестный пункт меню.")
    return True


def format_windows_search_results(results: List, search_type: str) -> None:
    """Форматированный вывод результатов поиска для Windows"""
    print("\n" + "=" * 60)
    print("Тип поиска: " + str(search_type))
    print("Найдено: " + str(len(results)))
    print("=" * 60)

    if len(results) == 0:
        print("Ничего не найдено.")
        print("=" * 60 + "\n")
        return

    if isinstance(results[0], dict):
        i = 1
        for item in results:
            p = item["path"]
            size_mb = item["size_mb"]
            ftype = item["type"]
            print(str(i).rjust(4) + ". " + p + "   [" + str(ftype) + "]   (" + str(size_mb) + " MB)")
            i += 1
        print("=" * 60 + "\n")
        return

    i = 1
    for fp in results:
        fp = str(fp)
        if os.path.exists(fp):
            size_b = os.path.getsize(fp)
            size_str = utils.format_size(size_b)
            print(str(i).rjust(4) + ". " + fp + "   (" + size_str + ")")
        else:
            print(str(i).rjust(4) + ". " + fp)
        i += 1

    stats = analysis.get_windows_file_attributes_stats(results)
    if isinstance(stats, dict) and len(stats) > 0:
        print("\n[Атрибуты файлов] Статистика:")
        for k in stats:
            print(" - " + str(k) + ": " + str(stats[k]))

    print("=" * 60 + "\n")
