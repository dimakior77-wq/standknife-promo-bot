import os
import re
from telethon import TelegramClient, events
from google import genai
from google.genai import types
from PIL import Image

# Получаем настройки из переменных окружения Render
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "anon")
TARGET_CHANNEL = int(os.getenv("TARGET_CHANNEL", "0"))  # ID твоего канала
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Инициализация Gemini API
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Инициализация Telethon клиента
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    try:
        text_to_check = event.message.message or ""
        image_path = None

        # Если есть картинка, скачиваем её для OCR
        if event.message.photo:
            image_path = await event.message.download_media(file="temp_promo.jpg")

        extracted_promo = None

        # Проверяем текст через Gemini или ищем промокод
        if image_path:
            pil_image = Image.open(image_path)
            response = ai_client.models.generate_content(
                model='gemini-3.8-flash',
                contents=[
                    pil_image,
                    "Найди на этой картинке промокод для игры Standoff 2. Верни ТОЛЬКО сам промокод без лишних слов. Если его нет, напиши NONE."
                ]
            )
            os.remove(image_path)
            if response.text:
                cleaned = response.text.strip()
                if cleaned != "NONE" and len(cleaned) < 30:
                    extracted_promo = cleaned

        if not extracted_promo and text_to_check:
            # Простейший поиск по ключевым словам или шаблонам
            pass # Здесь можно добавить регулярки при необходимости

        if extracted_promo:
            # Получаем ссылку на источник (если сообщение из канала/чата)
            chat = await event.get_chat()
            source_link = "ЛС"
            if hasattr(chat, 'username') and chat.username:
                source_link = f"https://t.me/{chat.username}/{event.message.id}"
            else:
                source_link = f"https://t.me/c/{chat.id}/{event.message.id}"

            # Формируем пост по строгому шаблону с кликабельным автокопированием
            post_text = (
                f"НОВЫЙ ПРОМОКОД\n\n"
                f"🎁 Промокод: {extracted_promo}\n\n"
                f"🔗 СЛИЛ: [Кликни сюда]({source_link})"
            )

            # Публикуем в целевой канал с картинкой из репозитория
            local_img = "IMG_20261026_143610_107.jpg"
            if os.path.exists(local_img):
                await client.send_file(TARGET_CHANNEL, local_img, caption=post_text, parse_mode='md')
            else:
                await client.send_message(TARGET_CHANNEL, post_text, parse_mode='md')

    except Exception as e:
        print(f"Ошибка: {e}")

def main():
    client.start()
    print("Бот успешно запущен и слушает сообщения 24/7!")
    client.run_until_disconnected()

if name == 'main':
    main()
