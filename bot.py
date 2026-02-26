import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events, Button
from telethon.tl.types import Channel
from telethon.tl.functions.channels import GetFullChannelRequest

# Загрузка переменных окружения
load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
PHONE = os.getenv('PHONE')
TARGET_BOT = os.getenv('TARGET_BOT', '@GardenHorizonsBot')
OWNER_USERNAME = os.getenv('OWNER_USERNAME', 'mellfreezy')

# Создание клиента
client = TelegramClient('session_name', API_ID, API_HASH)

# Глобальные переменные для хранения каналов
channels_to_forward = []


async def get_channels_by_owner():
    """Получить список каналов, где создатель - OWNER_USERNAME"""
    valid_channels = []
    
    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, Channel):
            try:
                # Получаем полную информацию о канале
                full_channel = await client(GetFullChannelRequest(channel=dialog.entity))
                
                # Проверяем права администратора
                if dialog.entity.admin_rights:
                    # Получаем информацию о создателе
                    participants = await client.get_participants(
                        dialog.entity, 
                        filter='administrators'
                    )
                    
                    for participant in participants:
                        if hasattr(participant.participant, 'is_creator') and participant.participant.is_creator:
                            if participant.username and participant.username.lower() == OWNER_USERNAME.lower():
                                valid_channels.append(dialog.entity)
                                print(f"✓ Найден канал: {dialog.name} (ID: {dialog.entity.id})")
                                break
            except Exception as e:
                print(f"Ошибка при проверке канала {dialog.name}: {e}")
                continue
    
    return valid_channels


async def interact_with_bot():
    """Взаимодействие с TARGET_BOT и пересылка в каналы"""
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Начало процесса взаимодействия...")
        
        # Отправляем /start боту
        await client.send_message(TARGET_BOT, '/start')
        await asyncio.sleep(2)
        
        # Получаем последнее сообщение от бота
        messages = await client.get_messages(TARGET_BOT, limit=1)
        
        if not messages:
            print("Не получено сообщений от бота")
            return
        
        last_message = messages[0]
        print(f"Получено сообщение от бота: {last_message.text[:50] if last_message.text else 'Без текста'}...")
        
        # Находим кнопку "Просмотреть сток" или похожую
        stock_button_found = False
        if last_message.buttons:
            for row in last_message.buttons:
                for button in row:
                    if button.text and ('сток' in button.text.lower() or 'stock' in button.text.lower() or 'просмотр' in button.text.lower()):
                        print(f"Нажимаем кнопку: {button.text}")
                        await button.click()
                        stock_button_found = True
                        break
                if stock_button_found:
                    break
        
        if not stock_button_found:
            print("Кнопка 'Просмотреть сток' не найдена, пробуем взять первую кнопку")
            if last_message.buttons and last_message.buttons[0]:
                await last_message.buttons[0][0].click()
        
        # Ждем ответ после нажатия кнопки
        await asyncio.sleep(3)
        
        # Получаем новое сообщение (ответ на нажатие кнопки)
        stock_messages = await client.get_messages(TARGET_BOT, limit=1)
        
        if not stock_messages:
            print("Не получен ответ после нажатия кнопки")
            return
        
        stock_message = stock_messages[0]
        print(f"Получен сток: {stock_message.text[:50] if stock_message.text else 'Без текста'}...")
        
        # Пересылаем сообщение в каналы (без кнопок)
        for channel in channels_to_forward:
            try:
                # Отправляем текст и медиа без кнопок
                if stock_message.text:
                    await client.send_message(
                        channel,
                        stock_message.text,
                        file=stock_message.media if stock_message.media else None
                    )
                    print(f"✓ Отправлено в канал: {channel.title}")
            except Exception as e:
                print(f"Ошибка при отправке в канал {channel.title}: {e}")
        
        # Теперь ищем и нажимаем кнопку "Gear"
        gear_button_found = False
        if stock_message.buttons:
            for row in stock_message.buttons:
                for button in row:
                    if button.text and ('gear' in button.text.lower() or 'шестер' in button.text.lower()):
                        print(f"Нажимаем кнопку: {button.text}")
                        await button.click()
                        gear_button_found = True
                        break
                if gear_button_found:
                    break
        
        if not gear_button_found:
            print("Кнопка 'Gear' не найдена")
            return
        
        # Ждем ответ после нажатия Gear
        await asyncio.sleep(3)
        
        # Получаем ответ после нажатия Gear
        gear_messages = await client.get_messages(TARGET_BOT, limit=1)
        
        if not gear_messages:
            print("Не получен ответ после нажатия Gear")
            return
        
        gear_message = gear_messages[0]
        print(f"Получен ответ Gear: {gear_message.text[:50] if gear_message.text else 'Без текста'}...")
        
        # Пересылаем Gear сообщение в каналы (без кнопок)
        for channel in channels_to_forward:
            try:
                if gear_message.text:
                    await client.send_message(
                        channel,
                        gear_message.text,
                        file=gear_message.media if gear_message.media else None
                    )
                    print(f"✓ Gear отправлен в канал: {channel.title}")
            except Exception as e:
                print(f"Ошибка при отправке Gear в канал {channel.title}: {e}")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Процесс завершен успешно!\n")
        
    except Exception as e:
        print(f"Ошибка в процессе взаимодействия: {e}")


async def wait_for_next_interval():
    """Ждать до следующего интервала (когда минуты делятся на 5)"""
    now = datetime.now()
    current_minute = now.minute
    
    # Вычисляем следующую минуту, кратную 5
    next_minute = ((current_minute // 5) + 1) * 5
    
    if next_minute >= 60:
        next_minute = 0
        next_run = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
    else:
        next_run = now.replace(minute=next_minute, second=0, microsecond=0)
    
    wait_seconds = (next_run - now).total_seconds()
    
    print(f"Следующий запуск в {next_run.strftime('%H:%M')}")
    print(f"Ожидание {wait_seconds:.0f} секунд...\n")
    
    await asyncio.sleep(wait_seconds)


async def scheduler():
    """Планировщик задач - запускает каждые 5 минут"""
    global channels_to_forward
    
    # Получаем список каналов при старте
    print("Поиск каналов для пересылки...")
    channels_to_forward = await get_channels_by_owner()
    
    if not channels_to_forward:
        print(f"⚠️ Не найдено каналов, где создатель @{OWNER_USERNAME}")
        print("Убедитесь, что бот добавлен в каналы как администратор")
    else:
        print(f"\n✓ Найдено каналов: {len(channels_to_forward)}")
        for ch in channels_to_forward:
            print(f"  - {ch.title}")
    
    print("\n" + "="*50)
    print("БОТ ЗАПУЩЕН!")
    print("="*50 + "\n")
    
    # Ждем до первого интервала
    await wait_for_next_interval()
    
    # Бесконечный цикл
    while True:
        await interact_with_bot()
        await wait_for_next_interval()


async def main():
    """Главная функция"""
    await client.start(phone=PHONE)
    print("Клиент успешно авторизован!")
    
    # Запускаем планировщик
    await scheduler()


if __name__ == '__main__':
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n\nБот остановлен пользователем")
    finally:
        client.disconnect()
