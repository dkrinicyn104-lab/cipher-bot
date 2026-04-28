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

BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"
logging.basicConfig(level=logging.INFO)

# --- МОЩНЫЙ ФУНКЦИОНАЛ ---

def aes_crypt(text, key, mode='encode'):
    # Превращаем любой ключ пользователя в 32-байтный формат для AES
    k = hashlib.sha256(key.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(k))
    return f.encrypt(text.encode()).decode() if mode == 'encode' else f.decrypt(text.encode()).decode()

def get_main_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔐 ВЫБРАТЬ ШИФР"), KeyboardButton("🔄 РЕЖИМ: ШИФРОВКА")],
        [KeyboardButton("🔑 КЛЮЧ"), KeyboardButton("📜 ИСТОРИЯ")],
        [KeyboardButton("⚙️ АВТО-РЕЖИМ: ВЫКЛ")]
    ], resize_keyboard=True)

# --- ОБРАБОТКА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.update({
        "cipher": "aes", "mode": "encode", "key": "secret", 
        "auto": False, "history": [], "state": "idle"
    })
    await update.message.reply_text(
        "**PROFESSIONAL ENCODER v1.0**\n\nПришлите текст для мгновенной обработки.",
        reply_markup=get_main_kb(), parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    text = update.message.text

    # Навигация по кнопкам
    if text == "🔐 ВЫБРАТЬ ШИФР":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("AES-256 (Strong)", callback_data="set_aes"), InlineKeyboardButton("Base64", callback_data="set_b64")],
            [InlineKeyboardButton("Vigenere", callback_data="set_vig"), InlineKeyboardButton("Atbash", callback_data="set_atb")]
        ])
        await update.message.reply_text("Выберите алгоритм:", reply_markup=kb)
        return

    elif "🔄 РЕЖИМ:" in text:
        ud["mode"] = "decode" if ud["mode"] == "encode" else "encode"
        m_label = "ДЕШИФРОВКА" if ud["mode"] == "decode" else "ШИФРОВКА"
        # Обновляем клавиатуру с новым названием кнопки
        new_kb = get_main_kb().keyboard
        new_kb[0][1] = KeyboardButton(f"🔄 РЕЖИМ: {m_label}")
        await update.message.reply_text(f"Установлен режим: {m_label}", reply_markup=ReplyKeyboardMarkup(new_kb, resize_keyboard=True))
        return

    elif text == "📜 ИСТОРИЯ":
        hist = ud.get("history", [])
        res = "\n".join(hist[-5:]) if hist else "История пуста"
        await update.message.reply_text(f"**Последние 5 операций:**\n\n{res}", parse_mode="Markdown")
        return

    elif "⚙️ АВТО-РЕЖИМ:" in text:
        ud["auto"] = not ud["auto"]
        status = "ВКЛ" if ud["auto"] else "ВЫКЛ"
        new_kb = get_main_kb().keyboard
        new_kb[2][0] = KeyboardButton(f"⚙️ АВТО-РЕЖИМ: {status}")
        await update.message.reply_text(f"Авто-детект: {status}", reply_markup=ReplyKeyboardMarkup(new_kb, resize_keyboard=True))
        return

    elif text == "🔑 КЛЮЧ":
        ud["state"] = "wait_key"
        await update.message.reply_text("Введите новый секретный ключ:")
        return

    if ud.get("state") == "wait_key":
        ud["key"], ud["state"] = text, "idle"
        await update.message.reply_text(f"✅ Ключ обновлен: `{text}`", parse_mode="Markdown")
        return

    # САМА ШИФРОВКА
    c, m, k = ud["cipher"], ud["mode"], ud["key"]
    
    # Логика Авто-режима: если текст похож на шифр, переключаем на дешифровку
    if ud["auto"] and m == "encode" and (text.endswith("=") or len(text) > 20):
        m = "decode"

    try:
        if c == "aes": res = aes_crypt(text, k, m)
        elif c == "b64": res = base64.b64encode(text.encode()).decode() if m == "encode" else base64.b64decode(text).decode()
        else: res = "Метод не выбран"

        # Сохраняем в историю
        ud["history"].append(f"{c.upper()} ({m}): `{res[:20]}...`" )
        
        await update.message.reply_text(f"📊 **Результат ({c.upper()}):**\n\n`{res}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Ошибка! Проверьте ключ или формат текста.")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ud = context.user_data
    ud["cipher"] = query.data.replace("set_", "")
    await query.edit_message_text(f"✅ Активен шифр: {ud['cipher'].upper()}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
