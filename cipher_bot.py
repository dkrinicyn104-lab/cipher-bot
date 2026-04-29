import logging
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# --- КОНФИГУРАЦИЯ ---
# Твой новый токен уже здесь
BOT_TOKEN = "7649500751:AAE49CGOTKq5F4067GZXcACAbxdD-On149Y"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- АЛГОРИТМЫ ---
def atbash(text):
    res = ""
    for c in text:
        if 'A' <= c <= 'Z': res += chr(155 - ord(c))
        elif 'a' <= c <= 'z': res += chr(219 - ord(c))
        elif 'А' <= c <= 'Я': res += chr(1071 - (ord(c) - 1040))
        elif 'а' <= c <= 'я': res += chr(1103 - (ord(c) - 1072))
        else: res += c
    return res

def process_logic(text, cipher, mode):
    try:
        if cipher == 'base64':
            if mode == 'encode': return base64.b64encode(text.encode()).decode()
            return base64.b64decode(text).decode()
        elif cipher == 'hex':
            if mode == 'encode': return text.encode().hex().upper()
            return bytes.fromhex(text).decode()
        elif cipher == 'atbash': return atbash(text)
        elif cipher == 'reverse': return text[::-1]
    except:
        return "❌ Ошибка! Проверь, соответствует ли текст выбранному шифру."

# --- ИНТЕРФЕЙС ---
def get_kb(ud):
    m = "🔒 ШИФРОВАТЬ" if ud.get('mode') == 'encode' else "🔓 ДЕШИФРОВАТЬ"
    c = ud.get('cipher', 'base64').upper()
    return ReplyKeyboardMarkup([
        [KeyboardButton(f"🔄 {m}"), KeyboardButton(f"⚙️ ТИП: {c}")]
    ], resize_keyboard=True)

# --- ФУНКЦИИ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.update({'mode': 'encode', 'cipher': 'base64'})
    await update.message.reply_text(
        "💎 **MASTER CIPHER v2.0**\n\nПришли любой текст, и я мгновенно его преобразую. "
        "Результат можно скопировать одним нажатием на него!",
        reply_markup=get_kb(ud), parse_mode=ParseMode.MARKDOWN
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if 'mode' not in ud: ud.update({'mode': 'encode', 'cipher': 'base64'})
    text = update.message.text

    # Кнопки управления
    if "🔄" in text:
        ud['mode'] = 'decode' if ud['mode'] == 'encode' else 'encode'
        await update.message.reply_text(f"✅ Режим изменен!", reply_markup=get_kb(ud))
        return

    if "⚙️ ТИП:" in text:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Base64", callback_data="c_base64"), InlineKeyboardButton("📟 HEX", callback_data="c_hex")],
            [InlineKeyboardButton("📜 Atbash", callback_data="c_atbash"), InlineKeyboardButton("🔄 Reverse", callback_data="c_reverse")]
        ])
        await update.message.reply_text("Выбери алгоритм:", reply_markup=kb)
        return

    # Выполнение преобразования
    res = process_logic(text, ud['cipher'], ud['mode'])
    icon = "🔒" if ud['mode'] == 'encode' else "🔓"
    
    # HTML формат позволяет копировать текст по нажатию (тег <code>)
    response = (
        f"<b>{icon} РЕЗУЛЬТАТ ({ud['cipher'].upper()}):</b>\n\n"
        f"<code>{res}</code>"
    )
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ud = context.user_data
    ud['cipher'] = query.data.replace("c_", "")
    await query.edit_message_text(f"✅ Выбран алгоритм: <b>{ud['cipher'].upper()}</b>", parse_mode=ParseMode.HTML)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Настройки применены!", reply_markup=get_kb(ud))

def main():
    # Создаем приложение с автоматической очисткой старых обновлений
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(inline_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # drop_pending_updates=True очень важен, чтобы бот не "захлебнулся" старыми запросами при старте
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
