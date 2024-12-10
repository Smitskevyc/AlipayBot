from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram import F
from aiogram.types.input_file import FSInputFile
from datetime import datetime, timedelta



import sqlite3
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
cancel_button = KeyboardButton(text="Отменить заполнение ❌")
# Ваш Telegram токен и ID каналов
TOKEN = "7650910241:AAGWjzv020ohKhiE2pIaPRLiu1Pw6_ydS2k"
LOG_ID = "-1002420300805"  # Лог-канал для всех аккаунтов
RG_ID = "-1002359652943"  # Канал для другого региона
RB_ID = "-1002468155515"  # Канал для Беларуси
UA_ID = "-1002487887581"  # Канал для Украины
PAY_ID = "-1002425628898" # Канал выплат

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния FSM
class RegisterAccount(StatesGroup):
    region = State()  # Состояние для выбора региона
    email = State()
    email_password = State()
    alipay_password = State()
    payment_pin = State()
    documents = State()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER,
        username TEXT,
        region TEXT, 
        email TEXT,
        email_password TEXT,
        alipay_password TEXT,
        payment_pin TEXT,
        documents TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


# Сохранение данных в базу
def save_user_data(data):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (telegram_id, username, region, email, email_password, alipay_password, payment_pin, documents)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
        data["telegram_id"], data["username"], data["region"], data["email"],
        data["email_password"], data["alipay_password"], data["payment_pin"],
        data["documents"]
    ))
    conn.commit()
    conn.close()


def generate_stats():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Запросы статистики
    stats = {
        "total": cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "today": cursor.execute(
            "SELECT region, COUNT(*) FROM users WHERE DATE(created_at) = ? GROUP BY region", (today,)
        ).fetchall(),
        "week": cursor.execute(
            "SELECT region, COUNT(*) FROM users WHERE DATE(created_at) BETWEEN ? AND ? GROUP BY region",
            (start_of_week, today)
        ).fetchall(),
        "month": cursor.execute(
            "SELECT region, COUNT(*) FROM users WHERE DATE(created_at) BETWEEN ? AND ? GROUP BY region",
            (start_of_month, today)
        ).fetchall(),
    }
    conn.close()

    # Форматирование статистики
    stats_text = f"📊 Статистика:\n\n"
    stats_text += f"Всего зарегистрированных пользователей: {stats['total']}\n\n"

    stats_text += f"За сегодня ({today.strftime('%d.%m.%Y')}):\n"
    total_today = 0
    for region, count in stats["today"]:
        stats_text += f"-🌍 {region}: {count} пользователей\n"
        total_today += count
    stats_text += f"- Общее количество за сегодня: {total_today}\n\n"

    stats_text += f"За неделю ({start_of_week.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}):\n"
    total_week = 0
    for region, count in stats["week"]:
        stats_text += f"-🌍 {region}: {count} пользователей\n"
        total_week += count
    stats_text += f"- Общее количество за неделю: {total_week}\n\n"

    stats_text += f"За месяц ({start_of_month.strftime('%d.%m.%Y')} - {today.strftime('%d.%m.%Y')}):\n"
    total_month = 0
    for region, count in stats["month"]:
        stats_text += f"-🌍 {region}: {count} пользователей\n"
        total_month += count
    stats_text += f"- Общее количество за месяц: {total_month}"

    return stats_text


# Инструкции по отправке аккаунта
async def send_instructions(message: types.Message):
    instructions = """
Отправка аккаунта в таком формате:

1. Регион (Выберите из предложенных вариантов)

2. Почта (Желательно Gmail)

3. Пароль от почты

4. Пароль от Alipay

5. Платежный PIN (Если ставили)

6. Три фотографии (Пример снизу)
    """
    await message.answer(instructions)

    # Абсолютные пути к фотографиям
    photo_paths = [
        "/home/ubuntu/AlipayBot/photo1.png",
        "/home/ubuntu/AlipayBot/photo2.png",
        "/home/ubuntu/AlipayBot/photo3.png"
    ]

    # Отправка фотографий через FSInputFile
    for photo_path in photo_paths:
        input_file = FSInputFile(photo_path)  # Используем FSInputFile для локальных файлов
        await bot.send_photo(chat_id=message.chat.id, photo=input_file)

    # Пустое сообщение с кнопкой
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить аккаунт")]],
        resize_keyboard=True
    )
    await message.answer("Нажимай кнопку!", reply_markup=keyboard)

# Обработка команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    # Отправка инструкций при первом запуске
    await send_instructions(message)

# ID пользователей, которые могут вызывать статистику
AUTHORIZED_USERS = [5185559474, 5371530911]  # Укажите ваши реальные ID

@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id not in AUTHORIZED_USERS:
        await message.answer("У вас нет доступа к этой команде.")
        return

    stats_text = generate_stats()
    await message.answer(stats_text)


# Начало процесса регистрации, если это не закончено
@dp.message(F.text == "Отправить аккаунт")
async def start_registration(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer("Вы уже начали процесс регистрации.")
        return

    if not message.from_user.username:
        await message.answer("У вас отсутствует username в Telegram. Установите его в настройках, чтобы продолжить.")
        return

    await state.update_data(username=message.from_user.username)
    
    # Запрос региона
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Беларусь")],
            [KeyboardButton(text="Украина")],
            [KeyboardButton(text="Другой регион")],
            [cancel_button]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите ваш регион:", reply_markup=keyboard)
    await state.set_state(RegisterAccount.region)

# Обработка выбора региона
@dp.message(RegisterAccount.region)
async def process_region(message: types.Message, state: FSMContext):
    if message.text == "Отменить заполнение ❌":
        # Обработка отмены
        await cancel_registration(message, state)
        return

    region = message.text
    if region not in ["Беларусь", "Украина", "Другой регион"]:
        await message.answer("Пожалуйста, выберите один из предложенных регионов: Беларусь, Украина или Другой регион.")
        return

    await state.update_data(region=region)
    await message.answer("Введите почту Gmail:")
    await state.set_state(RegisterAccount.email)


# Обработка ввода почты
@dp.message(RegisterAccount.email)
async def process_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Введите пароль от почты:")
    await state.set_state(RegisterAccount.email_password)

# Обработка ввода пароля от почты
@dp.message(RegisterAccount.email_password)
async def process_email_password(message: types.Message, state: FSMContext):
    await state.update_data(email_password=message.text)
    await message.answer("Введите пароль от AliPay:")
    await state.set_state(RegisterAccount.alipay_password)

# Обработка ввода пароля от AliPay
@dp.message(RegisterAccount.alipay_password)
async def process_alipay_password(message: types.Message, state: FSMContext):
    await state.update_data(alipay_password=message.text)
    await message.answer("Есть ли у вас платежный PIN? Выберите один из вариантов:")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ЕСТЬ")],
            [KeyboardButton(text="НЕТУ")],
            [cancel_button]
        ],
        resize_keyboard=True
    )
    
    await message.answer("Выберите:", reply_markup=keyboard)
    await state.set_state(RegisterAccount.payment_pin)


# Обработка отмены заполнения
@dp.message(F.text == "Отменить заполнение ❌")
async def cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вы отменили заполнение аккаунта. Если захотите начать снова, нажмите 'Отправить аккаунт'.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отправить аккаунт")]],
            resize_keyboard=True
        )
    )

@dp.message(RegisterAccount.documents, F.content_type == "photo")
async def process_documents(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    documents = user_data.get("documents", [])
    
    # Проверяем, не превышено ли количество фото
    if len(documents) >= 5:
        await message.answer("Максимальное количество добавленных фото - 5. Удалите лишние фотографии, если нужно.")
        return

    # Сохраняем ID фото
    documents.append(message.photo[-1].file_id)
    await state.update_data(documents=documents)

    await message.answer(
        f"Фото принято ({len(documents)}/5). Если у вас есть ещё документы, отправьте их. Когда закончите, напишите 'Готово'."
    )


# Обработка выбора, если у пользователя нет PIN
@dp.message(RegisterAccount.payment_pin, F.text == "НЕТУ")
async def process_no_payment_pin(message: types.Message, state: FSMContext):
    # Сохраняем, что PIN нет
    await state.update_data(payment_pin="НЕТУ")
    # Просим пользователя отправить документы
    await message.answer(
        "Введите фотографии документов. Когда закончите, напишите 'Готово'.",
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    # Переход к следующему состоянию для ввода документов
    await state.set_state(RegisterAccount.documents)


@dp.message(RegisterAccount.payment_pin, F.text == "ЕСТЬ")
async def process_has_payment_pin(message: types.Message, state: FSMContext):
    # Просим пользователя ввести PIN
    await message.answer(
        "Введите ваш платежный PIN:",
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    # Переходим в то же состояние для ожидания ввода PIN
    await state.set_state(RegisterAccount.payment_pin)


# Обработка ввода платежного PIN, если выбран "ЕСТЬ"
@dp.message(RegisterAccount.payment_pin)
async def process_enter_payment_pin(message: types.Message, state: FSMContext):
    await state.update_data(payment_pin=message.text)
    await message.answer(
        "Отправьте фотографии документов. Когда закончите, напишите 'Готово'.",
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    await state.set_state(RegisterAccount.documents)

# Команда для отмены на любом этапе регистрации
@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    await state.clear()  # Очищаем текущее состояние FSM
    await message.answer(
        "Вы отменили заполнение аккаунта. Если захотите начать снова, нажмите 'Отправить аккаунт'.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отправить аккаунт")]],
            resize_keyboard=True
        )
    )


# Обработка фотографий (могут быть несколько)
@dp.message(RegisterAccount.documents, F.content_type == "photo")
async def process_documents(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    documents = user_data.get("documents", [])
    documents.append(message.photo[-1].file_id)
    await state.update_data(documents=documents)
    await message.answer("Фото принято. Если у вас есть ещё документы, отправьте их. Когда закончите, напишите 'Готово'.")

# Завершение процесса после отправки всех фотографий
@dp.message(RegisterAccount.documents, F.text.casefold() == "готово")
async def finish_registration(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    documents = user_data.get("documents", [])

    # Проверяем минимальное количество фотографий
    if len(documents) < 3:
        await message.answer(
            "Минимальное количество фотографий для сдачи аккаунта - 3. Посмотрите инструкцию и добавьте недостающие фотографии."
        )
        return
    
    save_user_data({
        "telegram_id": message.from_user.id,
        "username": user_data["username"],
        "region": user_data["region"],
        "email": user_data["email"],
        "email_password": user_data["email_password"],
        "alipay_password": user_data["alipay_password"],
        "payment_pin": user_data["payment_pin"],
        "documents": ", ".join(user_data["documents"]),
    })

    await bot.send_message(PAY_ID, f"""
🆔 Пользователь: @{user_data["username"]}
📦 Регион: {user_data['region']}
📧 Почта: {user_data['email']}
    """)

    form_text = f"""
👤 Новый аккаунт:
🆔 Пользователь: @{user_data["username"]}
📦 Регион: {user_data['region']}
📧 Почта: {user_data['email']}
🔑 Пароль почты: {user_data['email_password']}
💳 Пароль AliPay: {user_data['alipay_password']}
🏦 Платежный PIN: {user_data['payment_pin'] if user_data['payment_pin'] != 'НЕТУ' else 'Нет'}
"""

    media_group = [
    types.InputMediaPhoto(media=photo_id) for photo_id in user_data["documents"]
    ]

    media_group[0].caption = form_text

    await bot.send_media_group(chat_id=LOG_ID, media=media_group)

    form_text = f"""
{user_data['email']}
{user_data['email_password']}
{user_data['alipay_password']}
{user_data['payment_pin'] if user_data['payment_pin'] != 'НЕТУ' else ''}
"""

    media_group[0].caption = form_text

    # Отправка в соответствующий региональный канал
    target_channel = None
    if user_data['region'] == "Украина":
        target_channel = UA_ID
    elif user_data['region'] == "Беларусь":
        target_channel = RB_ID
    else:
        target_channel = RG_ID

    await bot.send_media_group(chat_id=target_channel, media=media_group)

    await message.answer("Регистрация завершена! Ваши данные отправлены.")

    # Сброс состояния
    await state.clear()

# Основная точка входа
async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
