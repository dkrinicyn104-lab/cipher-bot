import os
import re
import base64
import hashlib
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.helpers import escape_markdown

# ТВОЙ ТОКЕН
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- КРИПТО-ЯДРО (Без изменений, всё работает) ---
def caesar(text: str, shift: int) -> str:
    res = []
    for c in text:
        if 'a' <= c.lower() <= 'z':
            base = ord('a') if c.islower() else ord('A')
            res.append(chr((ord(c) - base + shift) % 26 + base))
        elif 'а' <= c.lower() <= 'я':
            base = ord('а') if c.islower() else ord('А')
            res.append(chr((ord(c) - base + shift) % 32 + base))
        else: res.append(c)
    return "".join(res)

def vigenere(text: str, key: str, decode: bool = False) -> str:
    key = key.lower() if key else "secret"
    res, ki = [], 0
    for c in text:
        if c.isalpha():
            shift = ord(key[ki % len(key)]) - ord('a')
            if decode: shift = -shift
            res.append(caesar(c, shift))
            ki += 1
        else: res.append(c)
    return "".join(res)

# --- ИНТЕРФЕЙС (Переработан на 100%) ---

# Постоянное нижнее меню
def main_reply_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⚙️ Настройки")],
        [KeyboardButton("ℹ️ О боте"), KeyboardButton("❓ Помощь")]
    ], resize_keyboard=True)

# Инлайн-меню настроек
def settings_inline_kb(ud):
    mode_str = "🔐 Шифрование" if ud.get("mode") == "encode" else "🔓 Дешифровка"
    auto_str = "🟢 Авто: ВКЛ" if ud.get("auto") else "🔴 Авто: ВЫКЛ"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Текущий шифр: {ud.get('cipher').upper()}", callback_data="ciphers_list")],
        [InlineKeyboardButton(mode_str, callback_data="toggle_mode"), InlineKeyboardButton(auto_str, callback_data="toggle_auto")],
        [InlineKeyboardButton("🔑 Изменить ключ", callback_data="set_key")],
        [InlineKeyboardButton("🏠 В главное меню", callback_data="to_main")]
    ])

# Список всех шифров
def ciphers_list_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Base64", callback_data="set_c_base64"), InlineKeyboardButton("HEX", callback_data="set_c_hex")],
        [InlineKeyboardButton("Цезарь", callback_data="set_c_caesar"), InlineKeyboardButton("Виженер", callback_data="set_c_vigenere")],
        [InlineKeyboardButton("ROT13", callback_data="set_c_rot13"), InlineKeyboardButton("Реверс", callback_data="set_c_reverse")],
        [InlineKeyboardButton("MD5", callback_data="set_c_md5"), InlineKeyboardButton("SHA256", callback_data="set_c_sha256")],
        [InlineKeyboardButton("⬅️ Назад к настройкам", callback_data="to_settings")]
    ])

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.setdefault("cipher", "base64"); ud.setdefault("mode", "encode")
    ud.setdefault("key", "secret"); ud.setdefault("auto", False)
    
    await update.message.reply_text(
        r"🛡 *Cipher Bot PRO* — Твой личный криптограф\." + "\n\n" +
        r"Просто отправь мне текст, и я обработаю его\." + "\n" +
        r"Нажми кнопку *Настройки* внизу, чтобы сменить шифр\.",
        parse_mode="MarkdownV2", reply_markup=main_reply_kb()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    text = update.message.text

    # Обработка кнопок нижнего меню
    if text == "⚙️ Настройки":
        await update.message.reply_text("🛠 *Управление ботом:*", 
            reply_markup=settings_inline_kb(ud), parse_mode="MarkdownV2")
        return
    if text == "ℹ️ О боте":
        await update.message.reply_text("🦾 *Cipher Bot v3.0*\nСоздано для максимальной приватности.", parse_mode="MarkdownV2")
        return
    if text == "❓ Помощь":
        await update.message.reply_text("1. Выбери шифр в Настройках.\n2. Пришли текст.\n3. Получи результат!", reply_markup=main_reply_kb())
        return

    # Логика ввода ключа
    if ud.get("state") == "waiting_key":
        ud["key"] = text; ud["state"] = "idle"
        await update.message.reply_text(f"✅ Ключ обновлен на: `{escape_markdown(text, 2)}`", 
            parse_mode="MarkdownV2", reply_markup=main_reply_kb())
        return

    # Основная обработка текста
    c, m = ud.get("cipher"), ud.get("mode")
    try:
        if c == "base64":
            res = base64.b64encode(text.encode()).decode() if m == "encode" else base64.b64decode(text).decode()
        elif c == "hex":
            res = text.encode().hex() if m == "encode" else bytes.fromhex(text).decode()
        elif c == "caesar":
            res = caesar(text, 3 if m == "encode" else -3)
        elif c == "vigenere":
            res = vigenere(text, ud.get("key"), m == "decode")
        elif c == "rot13":
            res = text.translate(str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))
        elif c == "reverse":
            res = text[::-1]
        elif c == "md5":
            res = hashlib.md5(text.encode()).hexdigest()
        elif c == "sha256":
            res = hashlib.sha256(text.encode()).hexdigest()
        else: res = "Ошибка выбора"

        await update.message.reply_text(
            fr"✅ *Результат \({c.upper()}\):*" + "\n\n" + f"`{escape_markdown(res, 2)}`",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка данных для шифра {c.upper()}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ud = context.user_data; data = q.data

    if data == "to_settings" or data == "to_main":
        await q.edit_message_text("🛠 *Управление ботом:*", reply_markup=settings_inline_kb(ud), parse_mode="MarkdownV2")
    elif data == "toggle_mode":
        ud["mode"] = "decode" if ud["mode"] == "encode" else "encode"
        await q.edit_message_reply_markup(reply_markup=settings_inline_kb(ud))
    elif data == "toggle_auto":
        ud["auto"] = not ud["auto"]
        await q.edit_message_reply_markup(reply_markup=settings_inline_kb(ud))
    elif data == "ciphers_list":
        await q.edit_message_text("🔤 *Выбери алгоритм:*", reply_markup=ciphers_list_kb(), parse_mode="MarkdownV2")
    elif data.startswith("set_c_"):
        ud["cipher"] = data.replace("set_c_", "")
        await q.edit_message_text(f"✅ Выбран шифр: *{ud['cipher'].upper()}*", 
            reply_markup=settings_inline_kb(ud), parse_mode="MarkdownV2")
    elif data == "set_key":
        ud["state"] = "waiting_key"
        await q.edit_message_text("⌨️ *Отправь мне новое кодовое слово (ключ):*", parse_mode="MarkdownV2")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
    
