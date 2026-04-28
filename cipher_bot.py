import os
import re
import base64
import hashlib
import logging
from typing import Tuple, List, Optional

# Библиотеки для Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.helpers import escape_markdown

# ТВОЙ ТОКЕН (Вставлен напрямую)
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ╔══════════════════════════════════╗
#    КРИПТОГРАФИЧЕСКОЕ ЯДРО
# ╚══════════════════════════════════╝

def caesar(text: str, shift: int) -> str:
    res = []
    for c in text:
        if 'a' <= c.lower() <= 'z':
            base = ord('a') if c.islower() else ord('A')
            res.append(chr((ord(c) - base + shift) % 26 + base))
        elif 'а' <= c.lower() <= 'я':
            base = ord('а') if c.islower() else ord('А')
            res.append(chr((ord(c) - base + shift) % 32 + base))
        else:
            res.append(c)
    return "".join(res)

def vigenere(text: str, key: str, decode: bool = False) -> str:
    key = key.lower() if key else "secret"
    res = []
    ki = 0
    for c in text:
        if c.isalpha():
            # Базовое смещение по латинице
            shift = ord(key[ki % len(key)]) - ord('a')
            if decode:
                shift = -shift
            res.append(caesar(c, shift))
            ki += 1
        else:
            res.append(c)
    return "".join(res)

def b64_process(text: str, encode: bool) -> str:
    try:
        if encode:
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        return base64.b64decode(text).decode('utf-8')
    except Exception:
        return "⚠️ Ошибка: неверный формат Base64"

def hex_process(text: str, encode: bool) -> str:
    try:
        if encode:
            return text.encode('utf-8').hex()
        return bytes.fromhex(text).decode('utf-8')
    except Exception:
        return "⚠️ Ошибка: неверный формат HEX"

def rot13(text: str) -> str:
    return text.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
    ))

# ╔══════════════════════════════════╗
#    UI: КЛАВИАТУРЫ
# ╚══════════════════════════════════╝

def get_main_kb(user_data: dict) -> InlineKeyboardMarkup:
    auto_btn = "🧠 Авто-Детект: " + ("🟢 ВКЛ" if user_data.get("auto") else "🔴 ВЫКЛ")
    mode_btn = "⚙️ Режим: " + ("🔐 Шифрование" if user_data.get("mode") == "encode" else "🔓 Дешифровка")
    
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(mode_btn, callback_data="toggle_mode")],
        [InlineKeyboardButton(auto_btn, callback_data="toggle_auto")],
        [
            InlineKeyboardButton("🔤 Выбрать шифр", callback_data="ciphers"),
            InlineKeyboardButton("🔑 Задать ключ", callback_data="set_key")
        ],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])

def get_cipher_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Base64", callback_data="c_base64"), InlineKeyboardButton("🟩 HEX", callback_data="c_hex")],
        [InlineKeyboardButton("🔤 Цезарь", callback_data="c_caesar"), InlineKeyboardButton("🔑 Виженер", callback_data="c_vigenere")],
        [InlineKeyboardButton("🔄 ROT13", callback_data="c_rot13"), InlineKeyboardButton("↩️ Реверс", callback_data="c_reverse")],
        [InlineKeyboardButton("🔐 MD5", callback_data="c_md5"), InlineKeyboardButton("🛡 SHA256", callback_data="c_sha256")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu")]
    ])

# ╔══════════════════════════════════╗
#    ХЭНДЛЕРЫ
# ╚══════════════════════════════════╝

def init_user(context: ContextTypes.DEFAULT_TYPE) -> None:
    if "cipher" not in context.user_data:
        context.user_data.update({
            "cipher": "base64", "mode": "encode", "key": "secret", 
            "auto": False, "state": "idle"
        })

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_user(context)
    # Используем r"" для корректного MarkdownV2
    text = (
        r"🛡 *Cipher Bot PRO запущен\!*" + "\n\n" +
        r"Отправь любой текст, и я обработаю его согласно настройкам\."
    )
    await update.message.reply_text(
        text, 
        parse_mode="MarkdownV2", 
        reply_markup=get_main_kb(context.user_data)
    )

async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    init_user(context)
    ud = context.user_data
    text = update.message.text

    if ud.get("state") == "waiting_key":
        ud["key"] = text
        ud["state"] = "idle"
        await update.message.reply_text(
            f"✅ Ключ установлен: `{escape_markdown(text, version=2)}`", 
            parse_mode="MarkdownV2", 
            reply_markup=get_main_kb(ud)
        )
        return

    if ud.get("auto"):
        results = []
        if re.fullmatch(r'[0-9a-fA-F]+', text):
            res = hex_process(text, encode=False)
            if not res.startswith("⚠️"): results.append(("HEX", res))
        if re.fullmatch(r'[A-Za-z0-9+/=]+', text):
            res = b64_process(text, encode=False)
            if not res.startswith("⚠️"): results.append(("Base64", res))
        
        if not results:
            await update.message.reply_text("❌ Авто-детект не узнал формат текста.")
            return
            
        reply = r"🔍 *Результаты распознавания:*" + "\n\n"
        for name, r_text in results:
            reply += f"🔹 *{name}*: `{escape_markdown(r_text[:500], version=2)}`\n"
        await update.message.reply_text(reply, parse_mode="MarkdownV2")
        return

    c, m = ud["cipher"], ud["mode"]
    res = ""
    
    try:
        if c == "base64": res = b64_process(text, m == "encode")
        elif c == "hex": res = hex_process(text, m == "encode")
        elif c == "caesar": res = caesar(text, 3 if m == "encode" else -3)
        elif c == "vigenere": res = vigenere(text, ud["key"], m == "decode")
        elif c == "rot13": res = rot13(text)
        elif c == "reverse": res = text[::-1]
        elif c == "md5": res = hashlib.md5(text.encode()).hexdigest()
        elif c == "sha256": res = hashlib.sha256(text.encode()).hexdigest()
        
        safe_res = escape_markdown(res[:4000], version=2)
        c_name = escape_markdown(c.upper(), version=2)
        
        await update.message.reply_text(
            fr"✅ *Результат \({c_name}\):*" + "\n\n" + f"`{safe_res}`", 
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    init_user(context)
    ud = context.user_data
    data = query.data

    if data == "toggle_mode":
        ud["mode"] = "decode" if ud["mode"] == "encode" else "encode"
    elif data == "toggle_auto":
        ud["auto"] = not ud["auto"]
    elif data == "ciphers":
        await query.edit_message_text("🔤 Выберите алгоритм:", reply_markup=get_cipher_kb())
        return
    elif data.startswith("c_"):
        ud["cipher"] = data.split("_")[1]
    elif data == "set_key":
        ud["state"] = "waiting_key"
        await query.edit_message_text("⌨️ Введи слово-ключ (для Виженера):")
        return
    elif data == "about":
        await query.answer("Шифратор PRO v2.0", show_alert=True)
        return

    mode_txt = "Шифрование" if ud["mode"] == "encode" else "Дешифровка"
    await query.edit_message_text(
        f"⚙️ *Настройки*:\n"
        f"Алгоритм: `{ud['cipher']}`\n"
        f"Режим: `{mode_txt}`\n"
        f"Ключ: `{escape_markdown(ud['key'], version=2)}`",
        reply_markup=get_main_kb(ud),
        parse_mode="MarkdownV2"
    )

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))
    
    print("Бот успешно запущен на сервере!")
    app.run_polling()

if __name__ == "__main__":
    main()
