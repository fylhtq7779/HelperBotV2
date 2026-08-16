import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import NetworkError, TelegramError
from states import UserState
from utils import (
    create_skin_archive, validate_skin_name, CARS, get_car_display_name,
    save_stats, load_stats, save_users, load_users
)
from collections import Counter
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# httpx на INFO печатает полный URL запроса вместе с токеном бота
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")

# Словарь для хранения состояний пользователей
user_states = {}
# Словарь для хранения данных пользователей
user_data = {}
# Словарь для хранения ID сообщений бота
bot_messages = {}
# Счетчик для статистики
skin_stats = load_stats()
# Множество пользователей бота
bot_users = load_users()

async def safe_edit_message(message, text, reply_markup=None):
    """Безопасное редактирование сообщения с повторными попытками"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await message.edit_text(text, reply_markup=reply_markup)
            return True
        except NetworkError as e:
            if attempt == max_retries - 1:
                logger.error(f"Не удалось отредактировать сообщение после {max_retries} попыток: {e}")
                return False
            await asyncio.sleep(1)
        except TelegramError as e:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
            return False
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.message.from_user.id
    bot_users.add(user_id)
    save_users(bot_users)
    
    keyboard = [
        [InlineKeyboardButton("Создать скин", callback_data="create_skin")],
        [InlineKeyboardButton("Статистика", callback_data="stats")],
        [InlineKeyboardButton("Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я бот для создания скинов BeamNG Drive.\n\n"
        "Вы можете:\n"
        "1. Нажать кнопку 'Создать скин'\n"
        "2. Сразу отправить DDS файл\n"
        "3. Посмотреть статистику использования\n\n"
        "Что бы вы хотели сделать?",
        reply_markup=reply_markup
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать статистику использования бота"""
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError as e:
        logger.error(f"Ошибка при ответе на callback query: {e}")
    
    total_skins = sum(skin_stats.values())
    if total_skins == 0:
        stats_text = "Статистика пока пуста. Создайте первый скин!"
    else:
        # Получаем топ-5 машин
        top_cars = skin_stats.most_common(5)
        stats_text = f"📊 Статистика использования бота:\n\n"
        stats_text += f"Всего создано скинов: {total_skins}\n\n"
        stats_text += "Топ-5 популярных машин:\n"
        for car_id, count in top_cars:
            car_name = get_car_display_name(car_id)
            percentage = (count / total_skins) * 100
            stats_text += f"• {car_name}: {count} скинов ({percentage:.1f}%)\n"
    
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(stats_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError as e:
        logger.error(f"Ошибка при ответе на callback query: {e}")
    
    user_id = query.from_user.id
    
    try:
        if query.data == "create_skin":
            keyboard = []
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Отправьте DDS файл скина.\n"
                "Файл должен быть в формате DDS и иметь размер 2048x2048 пикселей.",
                reply_markup=reply_markup
            )
            user_states[user_id] = UserState.WAITING_FOR_DDS
        elif query.data == "help":
            keyboard = [
                [InlineKeyboardButton("Назад", callback_data="back_to_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Как использовать бота:\n\n"
                "1. Отправьте DDS файл скина (2048x2048 пикселей)\n"
                "2. Введите название скина (только английские буквы в нижнем регистре)\n"
                "3. Введите отображаемое имя скина (любые символы)\n"
                "4. Выберите машину из списка\n\n"
                "Бот создаст архив со скином, который можно будет установить в игру.\n\n"
                "Шаблоны скинов из мода Skin Helper\n"
                "Автор: Beamer XD | Поддержка: @Top Tier Studios\n"
                "beamng.com/resources/skin-helper.15037",
                reply_markup=reply_markup
            )
        elif query.data == "stats":
            await show_stats(update, context)
        elif query.data == "back_to_main":
            keyboard = [
                [InlineKeyboardButton("Создать скин", callback_data="create_skin")],
                [InlineKeyboardButton("Статистика", callback_data="stats")],
                [InlineKeyboardButton("Помощь", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Привет! Я бот для создания скинов BeamNG Drive.\n\n"
                "Вы можете:\n"
                "1. Нажать кнопку 'Создать скин'\n"
                "2. Сразу отправить DDS файл\n"
                "3. Посмотреть статистику использования\n\n"
                "Что бы вы хотели сделать?",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        try:
            await query.message.reply_text(
                "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте еще раз."
            )
        except TelegramError as e:
            logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик получения документов"""
    user_id = update.message.from_user.id
    
    # Инициализируем данные пользователя, если их нет
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # Если пользователь не в процессе создания скина, начинаем новый процесс
    if user_id not in user_states or user_states[user_id] == UserState.IDLE:
        user_states[user_id] = UserState.WAITING_FOR_DDS
    
    if user_states[user_id] == UserState.WAITING_FOR_DDS:
        file = await context.bot.get_file(update.message.document.file_id)
        
        # Проверяем расширение файла
        if not update.message.document.file_name.lower().endswith('.dds'):
            await update.message.reply_text(
                "Пожалуйста, отправьте файл в формате DDS."
            )
            return
        
        # Сохраняем DDS файл
        dds_content = await file.download_as_bytearray()
        user_data[user_id]['dds_content'] = dds_content
        
        # Запрашиваем название скина
        keyboard = []
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Введите название скина.\n"
            "Используйте только английские буквы в нижнем регистре, без пробелов и специальных символов.",
            reply_markup=reply_markup
        )
        user_states[user_id] = UserState.WAITING_FOR_SKIN_NAME

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.message.from_user.id
    text = update.message.text
    
    if user_id not in user_states:
        return
    
    if user_states[user_id] == UserState.WAITING_FOR_SKIN_NAME:
        if not validate_skin_name(text):
            await update.message.reply_text(
                "Некорректное название скина.\n"
                "Используйте только английские буквы в нижнем регистре, без пробелов и специальных символов."
            )
            return
        
        user_data[user_id]['skin_name'] = text
        keyboard = []
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Введите отображаемое имя скина.\n"
            "Это имя будет показано в игре, можно использовать любые символы.",
            reply_markup=reply_markup
        )
        user_states[user_id] = UserState.WAITING_FOR_DISPLAY_NAME
    
    elif user_states[user_id] == UserState.WAITING_FOR_DISPLAY_NAME:
        user_data[user_id]['display_name'] = text
        
        # Создаем клавиатуру с машинами
        keyboard = []
        for i in range(0, len(CARS), 2):
            row = []
            for j in range(2):
                if i + j < len(CARS):
                    car_id = CARS[i + j]
                    car_name = get_car_display_name(car_id)
                    row.append(InlineKeyboardButton(car_name, callback_data=f"car_{car_id}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Выберите машину для скина:",
            reply_markup=reply_markup
        )
        user_states[user_id] = UserState.WAITING_FOR_CAR

async def handle_car_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора машины"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id not in user_states or user_states[user_id] != UserState.WAITING_FOR_CAR:
        return
    
    # split с maxsplit=1: иначе md_series и us_semi обрежутся до md и us
    car_id = query.data.split('_', 1)[1]
    user_data[user_id]['car_id'] = car_id
    
    try:
        # Создаем архив со скином
        zip_buffer = create_skin_archive(
            car_id=car_id,
            skin_name=user_data[user_id]['skin_name'],
            display_name=user_data[user_id]['display_name'],
            dds_content=user_data[user_id]['dds_content']
        )
        
        # Обновляем статистику
        skin_stats[car_id] += 1
        save_stats(skin_stats)  # Сохраняем статистику в файл
        
        # Отправляем архив пользователю
        await query.message.reply_text("Создаю архив со скином...")
        await context.bot.send_document(
            chat_id=user_id,
            document=zip_buffer,
            filename=f"{car_id}_{user_data[user_id]['skin_name']}.zip"
        )
        
        # Сбрасываем состояние пользователя
        user_states[user_id] = UserState.IDLE
        user_data[user_id] = {}
        
        # Показываем кнопки снова
        keyboard = [
            [InlineKeyboardButton("Создать скин", callback_data="create_skin")],
            [InlineKeyboardButton("Статистика", callback_data="stats")],
            [InlineKeyboardButton("Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Скин успешно создан! Что дальше?",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании скина: {e}")
        await query.message.reply_text(
            f"Произошла ошибка при создании скина: {str(e)}\n"
            "Пожалуйста, попробуйте еще раз."
        )
        user_states[user_id] = UserState.IDLE
        user_data[user_id] = {}

async def say(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Секретная команда для рассылки сообщений"""
    # Проверяем username пользователя
    if update.message.from_user.username != "fylhtq7779":
        await update.message.reply_text("У вас нет прав для использования этой команды.")
        return
    
    # Получаем текст сообщения
    if not context.args:
        await update.message.reply_text("Использование: /say <текст сообщения>")
        return
    
    message = " ".join(context.args)
    sent_count = 0
    failed_count = 0
    
    # Отправляем сообщение всем пользователям
    for user_id in bot_users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 Сообщение от администратора:\n\n{message}"
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
            failed_count += 1
    
    # Отправляем отчет о рассылке
    await update.message.reply_text(
        f"Рассылка завершена:\n"
        f"✅ Успешно отправлено: {sent_count}\n"
        f"❌ Ошибок отправки: {failed_count}"
    )

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("say", say))
    application.add_handler(CallbackQueryHandler(handle_car_selection, pattern="^car_"))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main() 