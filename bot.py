import os
import re
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from aiohttp import web

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение данных из .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')  # @Garden_Horizons_Sad или ID
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')  # @gardenhorizons_z или ID

# Проверка наличии всех необходимых данных
if not all([BOT_TOKEN, SOURCE_CHANNEL, TARGET_CHANNEL]):
    raise ValueError("Не все переменные окружения установлены! Проверьте файл .env")

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def check_message_pattern(text: str) -> bool:
    """
    Проверяет, соответствует ли сообщение нужному паттерну.
    
    Паттерны:
    - Время и дата: 🕒 HH:MM (МСК) | 🗓️ DD.MM.YYYY
    - Маркер: 🚨 РЕДКИЙ ТОВАР! 👀
    - Категория: ⚙️ ИНСТРУМЕНТЫ или 🌱 СЕМЕНА (и другие)
    - Товар с количеством: [N шт.]
    """
    if not text:
        return False
    
    # Проверяем наличие времени в формате 🕒 HH:MM (МСК)
    has_time = bool(re.search(r'🕒\s*\d{1,2}:\d{2}\s*\(МСК\)', text))
    
    # Проверяем наличие даты в формате 🗓️ DD.MM.YYYY
    has_date = bool(re.search(r'🗓️\s*\d{2}\.\d{2}\.\d{4}', text))
    
    # Проверяем наличие маркера "РЕДКИЙ ТОВАР"
    has_rare_marker = '🚨 РЕДКИЙ ТОВАР!' in text or 'РЕДКИЙ ТОВАР' in text
    
    # Проверяем наличие товара с количеством в формате [N шт.]
    has_item_count = bool(re.search(r'\[\d+\s+шт\.\]', text))
    
    # Сообщение должно содержать все ключевые элементы
    return has_time and has_date and has_rare_marker and has_item_count


@dp.channel_post()
async def handle_channel_post(message: Message):
    """
    Обработчик сообщений из каналов.
    """
    try:
        # Получаем информацию о канале
        channel_id = message.chat.id
        channel_username = f"@{message.chat.username}" if message.chat.username else None
        channel_title = message.chat.title or "Unknown"
        
        logger.info(f"📨 Новое сообщение!")
        logger.info(f"   ID канала: {channel_id}")
        logger.info(f"   Username: {channel_username}")
        logger.info(f"   Название: {channel_title}")
        
        # Проверяем, это нужный канал?
        source_channel_clean = SOURCE_CHANNEL.strip().lower()
        
        # Варианты проверки
        is_match = False
        if channel_username:
            is_match = channel_username.lower() == source_channel_clean
        
        # Проверка по ID (если SOURCE_CHANNEL это ID)
        if not is_match and SOURCE_CHANNEL.lstrip('-').isdigit():
            is_match = str(channel_id) == SOURCE_CHANNEL or str(channel_id) == SOURCE_CHANNEL.replace('-100', '')
        
        logger.info(f"   Это исходный канал? {'✅ ДА' if is_match else '❌ НЕТ'}")
        logger.info(f"   Ожидается: {SOURCE_CHANNEL}")
        
        if not is_match:
            logger.info("   ⏭️ Пропускаем (не тот канал)")
            return
        
        # Получаем текст сообщения
        text = message.text or message.caption or ""
        
        if not text:
            logger.info("   ⏭️ Пропускаем (нет текста)")
            return
        
        logger.info(f"   📝 Текст сообщения:\n{text[:200]}...")
        
        # Проверяем паттерн
        has_time = bool(re.search(r'🕒\s*\d{1,2}:\d{2}\s*\(МСК\)', text))
        has_date = bool(re.search(r'🗓️\s*\d{2}\.\d{2}\.\d{4}', text))
        has_rare = '🚨 РЕДКИЙ ТОВАР!' in text or 'РЕДКИЙ ТОВАР' in text
        has_count = bool(re.search(r'\[\d+\s+шт\.\]', text))
        
        logger.info(f"   Проверка паттерна:")
        logger.info(f"      ⏰ Время: {has_time}")
        logger.info(f"      📅 Дата: {has_date}")
        logger.info(f"      🚨 Редкий товар: {has_rare}")
        logger.info(f"      📦 Количество: {has_count}")
        
        if check_message_pattern(text):
            logger.info("   ✅ Сообщение подходит! Отправляем...")
            
            try:
                # Отправляем сообщение в целевой канал
                sent_message = await bot.send_message(
                    chat_id=TARGET_CHANNEL,
                    text=text
                )
                logger.info(f"   ✅ Успешно отправлено в {TARGET_CHANNEL}")
                logger.info(f"   ID отправленного сообщения: {sent_message.message_id}")
            except Exception as send_error:
                logger.error(f"   ❌ Ошибка отправки: {send_error}")
                logger.error(f"   Проверьте права бота в канале {TARGET_CHANNEL}")
        else:
            logger.info("   ❌ Сообщение не подходит по паттерну, пропускаем")
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при обработке: {e}", exc_info=True)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Обработчик команды /start
    """
    await message.answer(
        "🤖 Бот для копирования сообщений запущен!\n\n"
        f"📥 Отслеживается канал: {SOURCE_CHANNEL}\n"
        f"📤 Отправка в канал: {TARGET_CHANNEL}\n\n"
        "Бот автоматически копирует сообщения со стоком товаров."
    )


async def health_check(request):
    """Эндпоинт для health check"""
    return web.Response(text="Bot is running!")


async def main():
    """
    Основная функция запуска бота.
    """
    logger.info("Запуск бота...")
    logger.info(f"Отслеживание канала: {SOURCE_CHANNEL}")
    logger.info(f"Отправка в канал: {TARGET_CHANNEL}")
    
    # Создаем веб-приложение для health check (требуется для Render.com)
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    # Получаем порт из переменной окружения (Render.com предоставляет PORT)
    port = int(os.getenv('PORT', 8080))
    
    # Запускаем веб-сервер в фоне
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Веб-сервер запущен на порту {port}")
    
    # Запуск бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        
