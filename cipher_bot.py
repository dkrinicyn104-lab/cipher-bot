import logging
import base64
import hashlib
from cryptography.fernet import Fernet
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# --- НАСТРОЙКИ ---
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"
logging.basicConfig(level=logging.INFO)

# --- ВСЕ ШИФРЫ МИРА В ОДНОМ МЕСТЕ ---

def aes_process(text, key, mode='encode'):
    # Генерируем валидный Fernet ключ из обычного текста (ключа пользователя)
    k = hashlib.sha256(key.encode()).digest()
    f_key = base64.urlsafe_b64encode(k)
    f = Fernet(f_key)
    if mode == 'encode':
        return f.encrypt(text.encode()).decode()
    else:
        return f.decrypt(text.encode()).decode()

def atbash(text):
    res = ""
    for char in text:
        if 'a' <= char <= 'z': res += chr(ord('z') - (ord(char) - ord('a')))
        elif 'A' <= char <= 'Z': res += chr(ord('Z') - (ord(char) - ord('A')))
        elif 'а' <= char <= 'я': res += chr(ord('я') - (ord(char) - ord('а')))
        elif 'А' <= char <= 'Я': res += chr(ord('Я') - (ord(char) - ord('А')))
        else: res += char
    return res

def vigenere(text, key, decode=False):
    key = key.lower() if key else "key"
    res = []
    ki = 0
    for char in text:
        if char.isalpha():
            shift = ord(key[ki % len(key)]) - ord('a')
            if decode: shift = -shift
            # Используем Цезаря внутри для сдвига
            start = ord('A') if char.isupper() else ord('a')
            alphabet_size = 32 if 'а' <= char.lower() <= 'я' else 26
            if 'а' <= char.lower() <= 'я': start = ord('А') if char.isupper() else ord('а')
            res.append(chr((ord(char) - start + shift) % alphabet_size + start))
            ki += 1
        else: res.append(char)
    return "".join(res)

# --- ИНТЕРФЕЙС ---

def get_main_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🛠 ВЫБРАТЬ ШИФР"), KeyboardButton("🔄 СМЕНИТЬ РЕЖИМ")],
        [KeyboardButton("🔑 УСТАНОВИТЬ КЛЮЧ"), KeyboardButton("🧹 СБРОС")]
    ], resize_keyboard=True)

def get_cipher_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 AES-256 (Secret)", callback_data="set_aes"), InlineKeyboardButton("📦 Base64", callback_data="set_b64")],
        [InlineKeyboardButton("🏛 Vigenere", callback_data="set_vig"), InlineKeyboardButton("📜 Atbash", callback_data="set_atb")],
        [InlineKeyboardButton("🔢 Morse", callback_data="set_mor"), InlineKeyboardButton("🔄 Reverse", callback_data="set_rev")],
        [InlineKeyboardButton("🔐 SHA-256 (Hash)", callback_data="set_sha")]
    ])

# --- ЛОГИКА БОТА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.update({"cipher": "b64", "mode": "encode", "key": "secret", "state": "idle"})
    
    await update.message.reply_text(
        "👋 **Добро пожаловать в MASTER CIPHER!**\n\nЯ — твой персональный инструмент для защиты информации. Выбирай алгоритм и присылай текст.",
        reply_markup=get_main_kb(), parse_mode="Markdown"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    text = update.message.text

    # Обработка кнопок меню
    if text == "🛠 ВЫБРАТЬ ШИФР":
        await update.message.reply_text("Выберите нужный алгоритм:", reply_markup=get_cipher_inline())
        return
    elif text == "🔄 СМЕНИТЬ РЕЖИМ":
        ud["mode"] = "decode" if ud.get("mode") == "encode" else "encode"
        m_name = "ДЕШИФРОВКА 🔓" if ud["mode"] == "decode" else "ШИФРОВКА 🔐"
        await update.message.reply_text(f"Режим изменен на: **{m_name}**", parse_mode="Markdown")
        return
    elif text == "🔑 УСТАНОВИТЬ КЛЮЧ":
        ud["state"] = "wait_key"
        await update.message.reply_text("Введите секретное слово (ключ):")
        return
    elif text == "🧹 СБРОС":
        ud.update({"cipher": "b64", "mode": "encode", "key": "secret"})
        await update.message.reply_text("Настройки сброшены до базовых.")
        return

    if ud.get("state") == "wait_key":
        ud["key"], ud["state"] = text, "idle"
        await update.message.reply_text(f"✅ Ключ установлен: `{text}`", parse_mode="Markdown")
        return

    # ПРОЦЕСС ШИФРОВАНИЯ
    c, m, k = ud.get("cipher"), ud.get("mode"), ud.get("key")
    try:
        if c == "aes": res = aes_process(text, k, m)
        elif c == "b64": res = base64.b64encode(text.encode()).decode() if m == "encode" else base64.b64decode(text).decode()
        elif c == "atb": res = atbash(text)
        elif c == "vig": res = vigenere(text, k, m == "decode")
        elif c == "rev": res = text[::-1]
        elif c == "sha": res = hashlib.sha256(text.encode()).hexdigest()
        else: res = "Неизвестный шифр"

        response = (
            f"📡 **Алгоритм:** `{c.upper()}`\n"
            f"⚙️ **Режим:** `{'Шифровка' if m == 'encode' else 'Дешифровка'}`\n"
            f"───\n`{res}`"
        )
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text("❌ Ошибка: Данные не соответствуют формату или неверный ключ.")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ud = context.user_data
    
    cipher_code = query.data.replace("set_", "")
    ud["cipher"] = cipher_code
    await query.edit_message_text(f"✅ Выбран шифр: **{cipher_code.upper()}**", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
