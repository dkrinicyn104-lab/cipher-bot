import os
import re
import base64
import hashlib
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton, constants
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.helpers import escape_markdown

# ТВОЙ ТОКЕН
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"

logging.basicConfig(level=logging.INFO)

# --- ГРАФИКА И СТИЛЬ ---
DIVIDER = "────────────────────────"
HACKER_HEADER = "📟 **CRYPTO TERMINAL v4.0**"

# --- ЛОГИКА ШИФРОВ ---
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

# --- КЛАВИАТУРЫ ---

def get_main_reply():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⚙️ ПАНЕЛЬ УПРАВЛЕНИЯ")],
        [KeyboardButton("👤 МОЙ ПРОФИЛЬ"), KeyboardButton("🆘 ПОМОЩЬ")]
    ], resize_keyboard=True)

def get_settings_inline(ud):
    m_icon = "🔐" if ud.get("mode") == "encode" else "🔓"
    m_text = "ШИФРОВАНИЕ" if ud.get("mode") == "encode" else "ДЕШИФРОВКА"
    a_icon = "🔵" if ud.get("auto") else "⚪"
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📡 АЛГОРИТМ: {ud.get('cipher').upper()}", callback_data="list_ciphers")],
        [InlineKeyboardButton(f"{m_icon} РЕЖИМ: {m_text}", callback_data="toggle_mode")],
        [InlineKeyboardButton(f"{a_icon} АВТО-ДЕТЕКТ", callback_data="toggle_auto"), 
         InlineKeyboardButton("🔑 КЛЮЧ", callback_data="set_key")],
        [InlineKeyboardButton("💎 ЗАКРЫТЬ ПАНЕЛЬ", callback_data="close_panel")]
    ])

def get_ciphers_inline():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Base64", callback_data="sc_base64"), InlineKeyboardButton("📟 HEX", callback_data="sc_hex")],
        [InlineKeyboardButton("🏛 Caesar", callback_data="sc_caesar"), InlineKeyboardButton("🔑 Vigenere", callback_data="sc_vigenere")],
        [InlineKeyboardButton("🔄 ROT13", callback_data="sc_rot13"), InlineKeyboardButton("◀️ REVERSE", callback_data="sc_reverse")],
        [InlineKeyboardButton("🔒 MD5", callback_data="sc_md5"), InlineKeyboardButton("🛡 SHA256", callback_data="sc_sha256")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back_to_settings")]
    ])

# --- ХЭНДЛЕРЫ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    for k, v in {"cipher": "base64", "mode": "encode", "key": "secret", "auto": False}.items():
        ud.setdefault(k, v)
    
    msg = (
        f"{HACKER_HEADER}\n{DIVIDER}\n"
        "Система готова к работе. Введите текст для мгновенной обработки или используйте панель управления для настройки протоколов."
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_reply())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    text = update.message.text

    if text == "⚙️ ПАНЕЛЬ УПРАВЛЕНИЯ":
        await update.message.reply_text(f"🛠 **НАСТРОЙКИ ПРОТОКОЛОВ:**\n{DIVIDER}", 
            reply_markup=get_settings_inline(ud), parse_mode="Markdown")
        return

    if ud.get("state") == "waiting_key":
        ud["key"], ud["state"] = text, "idle"
        await update.message.reply_text(f"✅ **КЛЮЧ ПРИНЯТ:** `{text}`", parse_mode="Markdown")
        return

    # Процесс обработки
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
        
        # Визуал ответа
        response = (
            f"✅ **ОБРАБОТКА ЗАВЕРШЕНА**\n{DIVIDER}\n"
            f"🔹 **Метод:** `{c.upper()}`\n"
            f"🔹 **Режим:** `{'ШИФРОВКА' if m == 'encode' else 'ДЕШИФРОВКА'}`\n\n"
            f"📝 **РЕЗУЛЬТАТ:**\n`{res}`"
        )
        await update.message.reply_text(response, parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ **ОШИБКА ПРОТОКОЛА:** Проверьте корректность входных данных.")

async def on_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # МОМЕНТАЛЬНЫЙ ОТКЛИК (Убирает лаг кнопки)
    ud = context.user_data
    data = query.data

    if data == "back_to_settings":
        await query.edit_message_text(f"🛠 **НАСТРОЙКИ ПРОТОКОЛОВ:**\n{DIVIDER}", 
            reply_markup=get_settings_inline(ud), parse_mode="Markdown")
    elif data == "toggle_mode":
        ud["mode"] = "decode" if ud["mode"] == "encode" else "encode"
        await query.edit_message_reply_markup(reply_markup=get_settings_inline(ud))
    elif data == "toggle_auto":
        ud["auto"] = not ud["auto"]
        await query.edit_message_reply_markup(reply_markup=get_settings_inline(ud))
    elif data == "list_ciphers":
        await query.edit_message_text(f"📡 **ВЫБОР АЛГОРИТМА:**\n{DIVIDER}", 
            reply_markup=get_ciphers_inline(), parse_mode="Markdown")
    elif data.startswith("sc_"):
        ud["cipher"] = data.replace("sc_", "")
        await query.edit_message_text(f"✅ **ПРОТОКОЛ {ud['cipher'].upper()} АКТИВИРОВАН**", 
            reply_markup=get_settings_inline(ud), parse_mode="Markdown")
    elif data == "set_key":
        ud["state"] = "waiting_key"
        await query.edit_message_text("⌨️ **ВВЕДИТЕ НОВЫЙ КЛЮЧ:**", parse_mode="Markdown")
    elif data == "close_panel":
        await query.delete_message()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
