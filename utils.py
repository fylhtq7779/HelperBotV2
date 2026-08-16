import os
import json
import zipfile
import logging
from io import BytesIO
from typing import List, Optional, Set, Dict, Any
from collections import Counter

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKINHELPER_DIR = os.path.join(BASE_DIR, "SkinHelper")
CAR_NAMES_FILE = os.path.join(BASE_DIR, "car_names.json")


def load_car_names() -> dict:
    """Загружает маппинг car_id -> display name из car_names.json"""
    try:
        with open(CAR_NAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("car_names.json не найден, display-имена недоступны")
        return {}


def scan_available_cars() -> list:
    """Сканирует SkinHelper/ и возвращает отсортированный список car_id"""
    cars = []
    if not os.path.isdir(SKINHELPER_DIR):
        logger.error(f"Директория SkinHelper не найдена: {SKINHELPER_DIR}")
        return cars
    for name in sorted(os.listdir(SKINHELPER_DIR)):
        car_dir = os.path.join(SKINHELPER_DIR, name)
        if not os.path.isdir(car_dir):
            continue
        has_template = any(
            os.path.isdir(os.path.join(car_dir, sub))
            for sub in os.listdir(car_dir)
            if sub.lower() == "skinname"
        )
        if has_template:
            cars.append(name)
    return cars


CAR_NAMES = load_car_names()
CARS = scan_available_cars()

# Пути к файлам
STATS_FILE = "skin_stats.json"
USERS_FILE = "bot_users.json"

def save_stats(stats: Counter) -> None:
    """Сохраняет статистику в файл"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dict(stats), f, ensure_ascii=False, indent=2)
        logger.info("Статистика успешно сохранена")
    except Exception as e:
        logger.error(f"Ошибка при сохранении статистики: {e}")

def load_stats() -> Counter:
    """Загружает статистику из файла"""
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                stats_dict = json.load(f)
            logger.info("Статистика успешно загружена")
            return Counter(stats_dict)
    except Exception as e:
        logger.error(f"Ошибка при загрузке статистики: {e}")
    return Counter()

def save_users(users: Set[int]) -> None:
    """Сохраняет список пользователей в файл"""
    with open('users.json', 'w') as f:
        json.dump(list(users), f)

def load_users() -> Set[int]:
    """Загружает список пользователей из файла"""
    try:
        with open('users.json', 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def get_car_display_name(car_id: str) -> str:
    """Получает игровое название машины по её внутреннему идентификатору"""
    return CAR_NAMES.get(car_id, car_id)

def get_template_path(car_id: str, template_name: str) -> str:
    """Получает путь к шаблону для конкретной машины"""
    car_dir = os.path.join(SKINHELPER_DIR, car_id)
    template_dir = None
    for sub in os.listdir(car_dir):
        if sub.lower() == "skinname" and os.path.isdir(os.path.join(car_dir, sub)):
            template_dir = os.path.join(car_dir, sub)
            break
    if template_dir is None:
        raise ValueError(f"Шаблоны для машины {car_id} не найдены")

    if template_name.endswith('.jbeam'):
        for file in os.listdir(template_dir):
            if file.endswith('.jbeam'):
                return os.path.join(template_dir, file)
        raise ValueError(f"Jbeam шаблон для машины {car_id} не найден")

    path = os.path.join(template_dir, template_name)
    if os.path.exists(path):
        return path
    alt_path = os.path.join(template_dir, "skin.materials.json")
    if template_name == "materials.json" and os.path.exists(alt_path):
        return alt_path
    raise ValueError(f"Шаблон {template_name} для машины {car_id} не найден")

def create_jbeam_content(car_id: str, skin_name: str, display_name: str) -> str:
    """Создает содержимое jbeam файла на основе шаблона"""
    template_path = get_template_path(car_id, "any.jbeam")  # Имя файла не важно, главное расширение
    
    logger.info(f"Читаем шаблон jbeam: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем имя и автора в jbeam
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '"name"' in line:
            line_lower = line.lower()
            if 'skin name' in line_lower or 'skin_name' in line_lower:
                lines[i] = f'       "name":"{display_name}",'
        elif '"authors"' in line:
            lines[i] = f'       "authors":"Skin Helper Bot",'

    content = '\n'.join(lines)

    # Заменяем SKINNAME/skinname (шаблоны непоследовательны в регистре)
    content = content.replace("SKINNAME", skin_name)
    content = content.replace("skinname", skin_name)
    
    logger.info(f"Создан jbeam контент: {content}")
    return content

def create_materials_content(car_id: str, skin_name: str) -> str:
    """Создает содержимое materials.json на основе шаблона"""
    template_path = get_template_path(car_id, "materials.json")
    
    if not os.path.exists(template_path):
        logger.error(f"Шаблон не найден: {template_path}")
        raise ValueError(f"Шаблон для машины {car_id} не найден")
    
    logger.info(f"Читаем шаблон materials: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем SKINNAME/skinname (шаблоны непоследовательны в регистре)
    content = content.replace("SKINNAME", skin_name)
    content = content.replace("skinname", skin_name)
    
    logger.info(f"Создан materials контент: {content}")
    return content

def create_skin_archive(car_id: str, skin_name: str, display_name: str, dds_content: bytes) -> BytesIO:
    """Создает ZIP архив со скином"""
    logger.info(f"Создаем архив для машины {car_id}, скин {skin_name}")
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Создаем структуру папок и файлов
        jbeam_content = create_jbeam_content(car_id, skin_name, display_name)
        materials_content = create_materials_content(car_id, skin_name)
        
        # Добавляем файлы в архив
        # BeamNG ищет содержимое мода в /vehicles/ от корня архива
        dds_path = f"vehicles/{car_id}/{skin_name}/{car_id}_skin_{skin_name}.dds"
        jbeam_path = f"vehicles/{car_id}/{skin_name}/{car_id}.jbeam"
        materials_path = f"vehicles/{car_id}/{skin_name}/materials.json"
        
        logger.info(f"Добавляем файлы в архив:")
        logger.info(f"DDS: {dds_path}")
        logger.info(f"JBEAM: {jbeam_path}")
        logger.info(f"MATERIALS: {materials_path}")
        
        zip_file.writestr(dds_path, dds_content)
        zip_file.writestr(jbeam_path, jbeam_content)
        zip_file.writestr(materials_path, materials_content)
    
    zip_buffer.seek(0)
    return zip_buffer

def validate_skin_name(name: str) -> bool:
    """Проверяет корректность названия скина.

    Только строчная латиница: имя уходит в пути внутри архива,
    кириллица и юникод там ломают загрузку мода игрой.
    """
    return bool(name) and all('a' <= ch <= 'z' for ch in name)