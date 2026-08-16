#!/usr/bin/env python3
"""Проверяет обновления мода Skin Helper и обновляет шаблоны."""

from __future__ import annotations  # str | None на python 3.9 (сервер на Debian 11)

import os
import re
import sys
import json
import shutil
import zipfile
import tempfile
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKINHELPER_DIR = os.path.join(BASE_DIR, "SkinHelper")
VERSION_FILE = os.path.join(BASE_DIR, "version.txt")
CAR_NAMES_FILE = os.path.join(BASE_DIR, "car_names.json")
MOD_PAGE_URL = "https://www.beamng.com/resources/skin-helper.15037/"
DOWNLOAD_URL = "https://www.beamng.com/resources/skin-helper.15037/download?version={version_id}"


def get_current_version() -> str:
    try:
        with open(VERSION_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def get_latest_version() -> str | None:
    req = urllib.request.Request(MOD_PAGE_URL, headers={"User-Agent": "SkinBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    match = re.search(r'download\?version=(\d+)', html)
    if match:
        return match.group(1)
    return None


def download_mod(version_id: str) -> str:
    url = DOWNLOAD_URL.format(version_id=version_id)
    tmp = tempfile.mktemp(suffix=".zip")
    req = urllib.request.Request(url, headers={"User-Agent": "SkinBot/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, 'wb') as f:
        shutil.copyfileobj(resp, f)
    return tmp


def extract_templates(zip_path: str) -> None:
    if os.path.exists(SKINHELPER_DIR):
        shutil.rmtree(SKINHELPER_DIR)
    os.makedirs(SKINHELPER_DIR)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for entry in zf.namelist():
            if not entry.startswith("vehicles/"):
                continue
            parts = entry.split("/")
            if len(parts) < 3:
                continue

            car_id = parts[1]
            rel_path = "/".join(parts[2:])

            lower = entry.lower()
            if lower.endswith(('.dds', '.png', '.jpg', '.pc')):
                continue

            if not (lower.endswith('.jbeam') or lower.endswith('.json')):
                continue

            basename = os.path.basename(entry)
            if basename.startswith("info_"):
                continue

            dest = os.path.join(SKINHELPER_DIR, car_id, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with zf.open(entry) as src, open(dest, 'wb') as dst:
                shutil.copyfileobj(src, dst)


def check_new_cars() -> list[str]:
    try:
        with open(CAR_NAMES_FILE, 'r') as f:
            known = json.load(f)
    except FileNotFoundError:
        known = {}

    new_cars = []
    for name in sorted(os.listdir(SKINHELPER_DIR)):
        if os.path.isdir(os.path.join(SKINHELPER_DIR, name)) and name not in known:
            new_cars.append(name)
    return new_cars


def main():
    current = get_current_version()
    print(f"Текущая версия: {current}")

    latest = get_latest_version()
    if latest is None:
        print("Не удалось определить версию мода")
        sys.exit(1)
    print(f"Последняя версия: {latest}")

    if current == latest:
        print("Обновлений нет")
        sys.exit(0)

    print("Найдено обновление, скачиваю...")
    zip_path = download_mod(latest)
    try:
        print("Извлекаю шаблоны...")
        extract_templates(zip_path)

        with open(VERSION_FILE, 'w') as f:
            f.write(latest)

        new_cars = check_new_cars()
        if new_cars:
            print(f"Новые машины без display-имени: {', '.join(new_cars)}")
            print("Добавьте их в car_names.json вручную")

        print(f"Обновлено: {current} -> {latest}")
    finally:
        os.unlink(zip_path)


if __name__ == "__main__":
    main()
