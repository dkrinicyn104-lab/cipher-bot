import logging
import base64
import hashlib
from cryptography.fernet import Fernet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ТВОЙ ТОКЕН
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"

logging.basicConfig(level=logging.INFO)

# --- МОЩНОЕ ЯДРО ---
def aes_engine(text, key, mode='encode'):
    # Превращаем ключ в 32-байтный формат для AES
    k = hashlib.sha256(key.encode()).digest()
    f = Fernet(base64.urlsafe_b64encode(k))
    if mode == 'encode':
        return f.encrypt(text.encode()).decode()
    return f.decrypt(text.encode()).decode()

def get_main_kb(ud):
    m_text = "🔐 РЕЖИМ: ШИФР" if ud.get('mode') == 'encode' else "🔓 РЕЖИМ: ДЕШИФР"
    c_text = ud.get('cipher', 'AES').upper()
    return ReplyKeyboardMarkup([
        [KeyboardButton(f"⚙️ МЕТОД: {c_text}"), KeyboardButton(m_text)],
        [KeyboardButton("📜 ИСТОРИЯ"), KeyboardButton("🧹 СБРОС")]
    ], resize_keyboard=True)

# --- ЛОГИКА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.update({"cipher": "aes", "mode": "encode", "key": "DEFAULT_KEY", "history": []})
    await update.message.reply_text(
        "💎 **CIPHER MASTER PRO**\n\nПришли текст — я его обработаю. Ключ по умолчанию уже стоит.",
        reply_markup=get_main_kb(ud), parse_mode="Markdown"
    )

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if "history" not in ud: ud["history"] = [] # Защита от потери данных
    text = update.message.text

    # Обработка кнопок меню
    if "⚙️ МЕТОД:" in text:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("AES-256 (Максимум)", callback_data="s_aes")],
            [InlineKeyboardButton("Base64 (Обычный)", callback_data="s_b64")]
        ])
        await update.message.reply_text("Выбери алгоритм защиты:", reply_markup=kb)
        return
    elif "РЕЖИМ:" in text:
        ud["mode"] = "decode" if ud.get("mode", "encode") == "encode" else "encode"
        await update.message.reply_text(f"Режим изменен!", reply_markup=get_main_kb(ud))
        return
    elif text == "📜 ИСТОРИЯ":
        res = "\n".join(ud["history"][-5:]) if ud["history"] else "История пуста."
        await update.message.reply_text(f"Последние действия:\n{res}")
        return
    elif text == "🧹 СБРОС":
        ud.update({"cipher": "aes", "mode": "encode", "history": []})
        await update.message.reply_text("Всё очищено.", reply_markup=get_main_kb(ud))
        return

    # САМ ПРОЦЕСС
    c, m, k = ud.get("cipher", "aes"), ud.get("mode", "encode"), ud.get("key", "DEFAULT_KEY")
    try:
        if c == "aes": res = aes_engine(text, k, m)
        else: res = base64.b64encode(text.encode()).decode() if m == 'encode' else base64.b64decode(text).decode()
        
        ud["history"].append(f"{c.upper()} -> `{res[:15]}...`")
        await update.message.reply_text(f"✅ **РЕЗУЛЬТАТ:**\n`{res}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Ошибка! Проверь режим (возможно, ты пытаешься расшифровать обычный текст).")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ud = context.user_data
    ud["cipher"] = query.data.replace("s_", "")
    await query.edit_message_text(f"Выбран метод: {ud['cipher'].upper()}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Меню обновлено", reply_markup=get_main_kb(ud))

def main():
    # Используем Application вместо Updater (фикс ошибки с твоего скриншота)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.run_polling()

if __name__ == "__main__":
    main()
