import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantCreator
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins
import os
from dotenv import load_dotenv

load_dotenv()

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
TARGET_BOT = os.getenv('TARGET_BOT', 'GardenHorizonsBot')
ALLOWED_CREATOR = os.getenv('ALLOWED_CREATOR', 'mellfreezy').lower().replace('@', '')

# Клиент
client = TelegramClient('session', API_ID, API_HASH)

# Состояние
pending_response = None
stock_received = False


async def get_valid_channels():
    """Получение каналов где создатель - разрешенный пользователь"""
    valid_channels = []
    
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            try:
                participants = await client(GetParticipantsRequest(
                    channel=dialog.entity,
                    filter=ChannelParticipantsAdmins(),
                    offset=0,
                    limit=100,
                    hash=0
                ))
                
                for user, participant in zip(participants.users, participants.participants):
                    if isinstance(participant, ChannelParticipantCreator):
                        username = user.username
                        if username and username.lower() == ALLOWED_CREATOR:
                            valid_channels.append(dialog.entity)
                            logger.info(f"✅ Канал: {dialog.name}")
                        break
                        
            except Exception as e:
                logger.debug(f"Пропуск {dialog.name}: {e}")
    
    return valid_channels


async def send_to_channels(text: str):
    """Отправка в каналы"""
    if not text:
        return
        
    channels = await get_valid_channels()
    
    if not channels:
        logger.warning("Нет каналов для отправки")
        return
    
    for channel in channels:
        try:
            await client.send_message(channel, text)
            logger.info(f"📤 Отправлено в: {channel.title}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка: {e}")


async def interact_with_bot():
    """Взаимодействие с ботом"""
    global pending_response, stock_received
    
    try:
        logger.info(f"🤖 Начинаем взаимодействие с @{TARGET_BOT}")
        
        # Отправляем /start
        await client.send_message(TARGET_BOT, '/start')
        pending_response = "menu"
        stock_received = False
        
        logger.info("📤 Отправлен /start")
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")


@client.on(events.NewMessage(from_users=TARGET_BOT))
async def handle_response(event):
    """Обработка ответов от бота"""
    global pending_response, stock_received
    
    message = event.message
    text = message.text or message.raw_text or ""
    
    logger.info(f"📨 Ответ от бота: {text[:50]}...")
    
    # Проверяем наличие кнопок
    if message.buttons:
        logger.info(f"🔘 Найдено кнопок: {len(message.buttons)}")
        
        for row in message.buttons:
            for button in row:
                btn_text = button.text.lower()
                logger.info(f"   Кнопка: {button.text}")
                
                # Этап 1: Ищем кнопку "Просмотреть сток"
                if pending_response == "menu":
                    if "сток" in btn_text or "stock" in btn_text or "просмотр" in btn_text:
                        logger.info(f"🔘 Нажимаем: {button.text}")
                        await asyncio.sleep(1)
                        await button.click()
                        pending_response = "stock"
                        return
                
                # Этап 2: Получили сток, ищем Gear
                if pending_response == "stock" and not stock_received:
                    # Сначала отправляем текст стока в каналы
                    if text:
                        logger.info("📦 Отправляем сток в каналы")
                        await send_to_channels(text)
                        stock_received = True
                    
                    # Ищем кнопку Gear
                    if "gear" in btn_text:
                        logger.info(f"🔘 Нажимаем: {button.text}")
                        await asyncio.sleep(1)
                        await button.click()
                        pending_response = "gear"
                        return
        
        # Если получили сток но не нашли Gear
        if pending_response == "stock" and not stock_received and text:
            logger.info("📦 Отправляем сток в каналы (без Gear)")
            await send_to_channels(text)
            stock_received = True
            pending_response = None
    
    else:
        # Сообщение без кнопок
        if pending_response == "stock" and not stock_received:
            logger.info("📦 Сток без кнопок, отправляем")
            await send_to_channels(text)
            stock_received = True
            pending_response = None
            
        elif pending_response == "gear":
            logger.info("⚙️ Gear получен, отправляем")
            await send_to_channels(text)
            pending_response = None


async def wait_for_next_interval():
    """Ожидание до следующего 5-минутного интервала"""
    now = datetime.now()
    
    # Вычисляем секунды до следующего интервала
    minutes_passed = now.minute % 5
    seconds_passed = minutes_passed * 60 + now.second
    seconds_to_wait = 300 - seconds_passed  # 5 минут = 300 секунд
    
    if seconds_to_wait <= 0:
        seconds_to_wait = 300
    
    next_minute = ((now.minute // 5) + 1) * 5 % 60
    logger.info(f"⏰ Следующий запуск в XX:{next_minute:02d}:00 (через {seconds_to_wait} сек)")
    
    await asyncio.sleep(seconds_to_wait)


async def auto_loop():
    """Основной цикл"""
    logger.info("🚀 Автопостинг запущен!")
    
    # Ждем первый интервал
    await wait_for_next_interval()
    
    while True:
        try:
            logger.info(f"{'='*40}")
            logger.info(f"🔄 Цикл: {datetime.now().strftime('%H:%M:%S')}")
            
            await interact_with_bot()
            
            # Даем время на получение ответов
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Ошибка в цикле: {e}")
        
        # Ждем до следующего интервала
        await wait_for_next_interval()


async def main():
    """Главная функция"""
    # Подключаемся
    await client.start(phone=PHONE)
    
    me = await client.get_me()
    logger.info(f"✅ Вошли как: @{me.username} ({me.first_name})")
    
    # Запускаем автопостинг
    asyncio.create_task(auto_loop())
    
    # Работаем бесконечно
    await client.run_until_disconnected()


if __name__ == '__main__':
    client.loop.run_until_complete(main())
