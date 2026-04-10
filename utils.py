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

# Словарь соответствия игровых названий и внутренних идентификаторов
CAR_NAMES = {
    'autobello': 'Autobello Piccolina',
    'midtruck': 'Autobello Stambecco',
    'bastion': 'Bruckell Bastion',
    'legran': 'Bruckell LeGran',
    'moonhawk': 'Bruckell Moonhawk',
    'burnside': 'Burnside Special',
    'vivace': 'Cherrier Vivace',
    'bolide': 'Civetta Bolide',
    'scintilla': 'Civetta Scintilla',
    'etk800': 'ETK 800-Series',
    'etki': 'ETK I-Series',
    'etkc': 'ETK K-Series',
    'barstow': 'Gavril Barstow',
    'bluebuck': 'Gavril Bluebuck',
    'pickup': 'Gavril D-Series',
    'fullsize': 'Gavril Grand Marshal',
    'van': 'Gavril H-Series',
    'md_series': 'Gavril MD-Series',
    'roamer': 'Gavril Roamer',
    'sbr': 'Hirochi SBR4',
    'sunburst2': 'Hirochi Sunburst',
    'bx': 'Ibishu 200BX',
    'covet': 'Ibishu Covet',
    'hopper': 'Ibishu Hopper',
    'miramar': 'Ibishu Miramar',
    'pessima': 'Ibishu Pessima (88-91)',
    'pigeon': 'Ibishu Pigeon',
    'wigeon': 'Ibishu Wigeon',
    'lansdale': 'Soliad Lansdale',
    'wendover': 'Soliad Wendover',
    'racetruck': 'SP Dunekicker',
    'rockbouncer': 'SP Rockbasher',
    'citybus': 'Wentward DT40L'
}

# Список доступных машин (внутренние идентификаторы)
CARS = [
    'autobello', 'barstow', 'bastion', 'bluebuck', 'bolide', 'burnside',
    'bx', 'citybus', 'covet', 'etk800', 'etkc', 'etki',
    'fullsize', 'hopper', 'lansdale', 'legran', 'md_series', 'midsize', 'midtruck',
    'miramar', 'moonhawk', 'pessima', 'pickup', 'pigeon', 'racetruck',
    'roamer', 'rockbouncer', 'sbr', 'scintilla', 'sunburst2',
    'van', 'vivace', 'wendover', 'wigeon'
]

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
    # Путь к папке с шаблонами (относительно расположения скрипта)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "SkinHelper", car_id, "SKINNAME")
    logger.info(f"Ищем шаблоны в директории: {template_dir}")
    
    if not os.path.exists(template_dir):
        logger.error(f"Директория с шаблонами не найдена: {template_dir}")
        raise ValueError(f"Шаблоны для машины {car_id} не найдены")
    
    # Если ищем jbeam файл, находим любой .jbeam файл в папке
    if template_name.endswith('.jbeam'):
        for file in os.listdir(template_dir):
            if file.endswith('.jbeam'):
                jbeam_path = os.path.join(template_dir, file)
                logger.info(f"Найден jbeam шаблон: {jbeam_path}")
                return jbeam_path
        logger.error(f"Jbeam шаблон не найден в директории: {template_dir}")
        raise ValueError(f"Jbeam шаблон для машины {car_id} не найден")
    
    # Для других файлов (например, materials.json) используем точное имя
    path = os.path.join(template_dir, template_name)
    if not os.path.exists(path):
        logger.error(f"Шаблон не найден: {path}")
        raise ValueError(f"Шаблон {template_name} для машины {car_id} не найден")
    
    return path

def create_jbeam_content(car_id: str, skin_name: str, display_name: str) -> str:
    """Создает содержимое jbeam файла на основе шаблона"""
    template_path = get_template_path(car_id, "any.jbeam")  # Имя файла не важно, главное расширение
    
    logger.info(f"Читаем шаблон jbeam: {template_path}")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем все возможные варианты отображаемого имени
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '"name"' in line:
            if 'YOUR SKIN NAME' in line:
                lines[i] = f'       "name":"{display_name}",'
            elif 'SKIN NAME' in line:
                lines[i] = f'       "name":"{display_name}",'
        elif '"authors"' in line:
            lines[i] = f'       "authors":"Skin Helper Bot",'
    
    content = '\n'.join(lines)
    
    # Заменяем SKINNAME (это всегда название скина в одно слово)
    content = content.replace("SKINNAME", skin_name)
    
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
    
    # Заменяем все вхождения SKINNAME
    content = content.replace("SKINNAME", skin_name)
    
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
        dds_path = f"{car_id}/{skin_name}/{car_id}_skin_{skin_name}.dds"
        jbeam_path = f"{car_id}/{skin_name}/{car_id}.jbeam"
        materials_path = f"{car_id}/{skin_name}/materials.json"
        
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
    """Проверяет корректность названия скина"""
    return name.isalpha() and name.islower() 