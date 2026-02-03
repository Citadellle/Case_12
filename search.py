import os
import re
from typing import List, Dict, Any, Tuple, Optional

import utils
import navigation
import analysis


def _normalize_windows_path(path: str) -> str:
    """Нормализует путь под Windows (обратные слеши, normpath)."""
    path = str(path).strip().replace("/", "\\")
    return os.path.normpath(path)


def _wildcard_to_regex(pattern: str, case_sensitive: bool) -> re.Pattern:
    """Преобразует wildcard-шаблон (*, ?) в regex, строго на всё имя."""
    pattern = pattern.strip()
    # Экранируем regex-символы, затем возвращаем * и ?
    escaped = ""
    for ch in pattern:
        if ch == "*":
            escaped += ".*"
        elif ch == "?":
            escaped += "."
        else:
            escaped += re.escape(ch)
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(rf"^{escaped}$", flags=flags)


def _iter_tree(root: str) -> Tuple[int, List[str]]:
    """Итеративный обход дерева каталогов. Возвращает (сканировано_файлов, список_каталогов)."""
    root = _normalize_windows_path(root)
    stack = [root]
    visited = set()
    total_files_scanned = 0
    dirs_scanned: List[str] = []

    while stack:
        current = _normalize_windows_path(stack.pop())
        if current in visited:
            continue
        visited.add(current)

        success, items = navigation.list_directory(current)
        if not success:
            continue

        dirs_scanned.append(current)

        for it in items:
            item_path = os.path.join(current, it["name"])
            if it["type"] == "directory":
                stack.append(item_path)
            else:
                total_files_scanned += 1

    return total_files_scanned, dirs_scanned


def find_files_windows(pattern: str, path: str, case_sensitive: bool = False) -> List[str]:
    """Поиск файлов по wildcard-шаблону (*, ?) начиная с корня path."""
    path = _normalize_windows_path(path)
    rx = _wildcard_to_regex(pattern, case_sensitive)

    stack = [path]
    visited = set()
    result_files: List[str] = []

    while stack:
        current = _normalize_windows_path(stack.pop())
        if current in visited:
            continue
        visited.add(current)

        success, items = navigation.list_directory(current)
        if not success:
            continue

        for it in items:
            name = str(it["name"]).strip()
            if not name:
                continue
            full_path = _normalize_windows_path(os.path.join(current, name))

            if it["type"] == "directory":
                stack.append(full_path)
                continue

            if rx.match(name):
                result_files.append(full_path)

    return result_files


def find_by_windows_extension(extensions: List[str], path: str) -> List[str]:
    """Поиск файлов по расширениям (exe, .dll, txt...) начиная с корня path."""
    path = _normalize_windows_path(path)

    norm_exts: List[str] = []
    for ext in extensions:
        ext = str(ext).strip().lower()
        if not ext:
            continue
        if not ext.startswith("."):
            ext = "." + ext
        norm_exts.append(ext)

    stack = [path]
    visited = set()
    search_result: List[str] = []

    while stack:
        current = _normalize_windows_path(stack.pop())
        if current in visited:
            continue
        visited.add(current)

        success, items = navigation.list_directory(current)
        if not success:
            continue

        for it in items:
            name = str(it["name"]).strip()
            if not name:
                continue
            full_path = _normalize_windows_path(os.path.join(current, name))

            if it["type"] == "directory":
                stack.append(full_path)
                continue

            _, ext = os.path.splitext(name.lower())
            if ext in norm_exts:
                search_result.append(full_path)

    return search_result


def find_large_files_windows(min_size_mb: float, path: str) -> List[Dict[str, Any]]:
    """Поиск файлов размером >= min_size_mb (МБ) начиная с корня path."""
    path = _normalize_windows_path(path)
    min_bytes = int(float(min_size_mb) * 1024 * 1024)

    stack = [path]
    visited = set()
    result: List[Dict[str, Any]] = []

    while stack:
        current = _normalize_windows_path(stack.pop())
        if current in visited:
            continue
        visited.add(current)

        success, items = navigation.list_directory(current)
        if not success:
            continue

        for it in items:
            name = str(it["name"]).strip()
            if not name:
                continue
            full_path = _normalize_windows_path(os.path.join(current, name))

            if it["type"] == "directory":
                stack.append(full_path)
                continue

            try:
                size_bytes = os.path.getsize(full_path)
            except (OSError, PermissionError):
                continue

            if size_bytes >= min_bytes:
                _, ext = os.path.splitext(name)
                result.append({
                    "path": full_path,
                    "size_mb": round(size_bytes / (1024 * 1024), 2),
                    "type": ext.lower() if ext else ""
                })

    result.sort(key=lambda x: x["size_mb"], reverse=True)
    return result


def find_windows_system_files(path: str) -> List[str]:
    """Поиск системных файлов (.exe, .dll, .sys) в типовых папках Windows."""
    path = _normalize_windows_path(path)

    special = navigation.get_windows_special_folders()
    roots: List[str] = []

    # Эти ключи добавляются в navigation.get_windows_special_folders() через SystemRoot/ProgramFiles
    for key in ["Windows", "System32", "SysWOW64", "ProgramFiles", "ProgramFilesX86"]:
        if key in special and os.path.exists(special[key]):
            roots.append(special[key])

    if not roots:
        roots.append(path)

    system_files: List[str] = []
    for root in roots:
        system_files.extend(find_by_windows_extension([".exe", ".dll", ".sys"], root))

    return system_files


def search_menu_handler(current_path: str) -> bool:
    """Меню поиска для консольного интерфейса."""
    current_path = _normalize_windows_path(current_path)

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
        case_sensitive = cs_input == "y"

        results = find_files_windows(pattern, current_path, case_sensitive)
        format_windows_search_results(results, "pattern")
        return True

    if choice == "2":
        raw = input("Введите расширения через запятую (exe, msi, .dll): ").strip()
        exts = [p.strip() for p in raw.split(",") if p.strip()]
        results = find_by_windows_extension(exts, current_path)
        format_windows_search_results(results, "extensions")
        return True

    if choice == "3":
        raw = input("Минимальный размер (MB): ").strip().replace(",", ".")
        try:
            min_mb = float(raw)
        except ValueError:
            print("Некорректное значение размера.")
            return True

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
    """Форматированный вывод результатов поиска."""
    print("\n" + "=" * 60)
    print("Тип поиска: " + str(search_type))
    print("Найдено: " + str(len(results)))
    print("=" * 60)

    if not results:
        print("Ничего не найдено.")
        print("=" * 60 + "\n")
        return

    # Список словарей (large files)
    if isinstance(results[0], dict):
        for i, item in enumerate(results, 1):
            p = item.get("path", "")
            size_mb = item.get("size_mb", 0)
            ftype = item.get("type", "")
            print(str(i).rjust(4) + ". " + p + "   [" + str(ftype) + "]   (" + str(size_mb) + " MB)")
        print("=" * 60 + "\n")
        return

    # Список путей
    for i, fp in enumerate(results, 1):
        fp = str(fp)
        if os.path.exists(fp):
            try:
                size_b = os.path.getsize(fp)
                size_str = utils.format_size(size_b)
                print(str(i).rjust(4) + ". " + fp + "   (" + size_str + ")")
            except (OSError, PermissionError):
                print(str(i).rjust(4) + ". " + fp)
        else:
            print(str(i).rjust(4) + ". " + fp)

    print("=" * 60 + "\n")
