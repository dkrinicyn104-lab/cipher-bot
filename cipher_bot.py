import os
import re
import base64
import hashlib
import logging
import asyncio
from typing import Tuple, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.helpers import escape_markdown

# ТВОЙ ТОКЕН
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ЯДРО ШИФРОВАНИЯ ---

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
            shift = ord(key[ki % len(key)]) - ord('a')
            if decode: shift = -shift
            res.append(caesar(c, shift))
            ki += 1
        else:
            res.append(c)
    return "".join(res)

def b64_process(text: str, encode: bool) -> str:
    try:
        if encode: return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        return base64.b64decode(text).decode('utf-8')
    except: return "⚠️ Ошибка: неверный формат Base64"

def hex_process(text: str, encode: bool) -> str:
    try:
        if encode: return text.encode('utf-8').hex()
        return bytes.fromhex(text).decode('utf-8')
    except: return "⚠️ Ошибка: неверный формат HEX"

# --- ИНТЕРФЕЙС ---

def get_main_kb(user_data: dict) -> InlineKeyboardMarkup:
    auto_btn = "🧠 Авто-Детект: " + ("🟢 ВКЛ" if user_data.get("auto") else "🔴 ВЫКЛ")
    mode_btn = "⚙️ Режим: " + ("🔐 Шифр" if user_data.get("mode") == "encode" else "🔓 Дешифр")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(mode_btn, callback_data="toggle_mode")],
        [InlineKeyboardButton(auto_btn, callback_data="toggle_auto")],
        [InlineKeyboardButton("🔤 Алгоритм", callback_data="ciphers"), InlineKeyboardButton("🔑 Ключ", callback_data="set_key")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ])

def get_cipher_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Base64", callback_data="c_base64"), InlineKeyboardButton("HEX", callback_data="c_hex")],
        [InlineKeyboardButton("Цезарь", callback_data="c_caesar"), InlineKeyboardButton("Виженер", callback_data="c_vigenere")],
        [InlineKeyboardButton("ROT13", callback_data="c_rot13"), InlineKeyboardButton("Реверс", callback_data="c_reverse")],
        [InlineKeyboardButton("MD5", callback_data="c_md5"), InlineKeyboardButton("SHA256", callback_data="c_sha256")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu")]
    ])

# --- ОБРАБОТКА ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("cipher", "base64")
    context.user_data.setdefault("mode", "encode")
    context.user_data.setdefault("key", "secret")
    context.user_data.setdefault("auto", False)
    
    await update.message.reply_text(
        r"🛡 *Cipher Bot PRO запущен\!*" + "\n\n" + r"Отправь текст для обработки\.",
        parse_mode="MarkdownV2",
        reply_markup=get_main_kb(context.user_data)
    )

async def process_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    text = update.message.text

    if ud.get("state") == "waiting_key":
        ud["key"], ud["state"] = text, "idle"
        await update.message.reply_text(f"✅ Ключ: `{escape_markdown(text, 2)}`", parse_mode="MarkdownV2", reply_markup=get_main_kb(ud))
        return

    if ud.get("auto"):
        res_list = []
        if re.fullmatch(r'[0-9a-fA-F]+', text):
            r = hex_process(text, False)
            if "⚠️" not in r: res_list.append(("HEX", r))
        if re.fullmatch(r'[A-Za-z0-9+/=]+', text):
            r = b64_process(text, False)
            if "⚠️" not in r: res_list.append(("Base64", r))
        
        if not res_list:
            await update.message.reply_text("❌ Формат не распознан.")
            return
        
        out = r"🔍 *Результат:* " + "\n\n"
        for n, t in res_list: out += f"🔹 *{n}*: `{escape_markdown(t, 2)}`\n"
        await update.message.reply_text(out, parse_mode="MarkdownV2")
        return

    c, m = ud.get("cipher", "base64"), ud.get("mode", "encode")
    try:
        if c == "base64": res = b64_process(text, m == "encode")
        elif c == "hex": res = hex_process(text, m == "encode")
        elif c == "caesar": res = caesar(text, 3 if m == "encode" else -3)
        elif c == "vigenere": res = vigenere(text, ud.get("key", "secret"), m == "decode")
        elif c == "rot13": res = text.translate(str.maketrans("ABCDEFGHIJKLMnopqrstuvwxyz", "NOPQRSTUVWXYZAbcdefghijklm"))
        elif c == "reverse": res = text[::-1]
        elif c == "md5": res = hashlib.md5(text.encode()).hexdigest()
        elif c == "sha256": res = hashlib.sha256(text.encode()).hexdigest()
        
        await update.message.reply_text(
            fr"✅ *Результат \({escape_markdown(c.upper(), 2)}\):*" + "\n\n" + f"`{escape_markdown(res, 2)}`",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ud = context.user_data
    d = q.data

    if d == "toggle_mode": ud["mode"] = "decode" if ud.get("mode") == "encode" else "encode"
    elif d == "toggle_auto": ud["auto"] = not ud.get("auto")
    elif d == "ciphers":
        await q.edit_message_text("🔤 Выберите алгоритм:", reply_markup=get_cipher_kb())
        return
    elif d.startswith("c_"): ud["cipher"] = d.split("_")[1]
    elif d == "set_key":
        ud["state"] = "waiting_key"
        await q.edit_message_text("⌨️ Введи новый ключ:")
        return

    await q.edit_message_text(
        f"⚙️ *Настройки*:\nАлгоритм: `{ud.get('cipher')}`\nРежим: `{'Шифр' if ud.get('mode')=='encode' else 'Дешифр'}`",
        reply_markup=get_main_kb(ud), parse_mode="MarkdownV2"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(btn))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))
    app.run_polling()

if __name__ == "__main__":
    main()
