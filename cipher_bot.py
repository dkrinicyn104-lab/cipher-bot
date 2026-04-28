import logging
import base64
import hashlib
import os
from cryptography.fernet import Fernet
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Конфигурация
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ЯДРО ШИФРОВАНИЯ ---
def crypt_engine(text, mode='encode', cipher_type='aes', key='MASTER_KEY'):
    try:
        if cipher_type == 'aes':
            # Генерация ключа из строки
            k = hashlib.sha256(key.encode()).digest()
            f = Fernet(base64.urlsafe_b64encode(k))
            if mode == 'encode':
                return f.encrypt(text.encode()).decode()
            return f.decrypt(text.encode()).decode()
        
        elif cipher_type == 'b64':
            if mode == 'encode':
                return base64.b64encode(text.encode()).decode()
            return base64.b64decode(text.encode()).decode()
    except Exception as e:
        return f"Ошибка: {str(e)}"

# --- КЛАВИАТУРЫ ---
def get_main_menu(ud):
    mode_label = "🔐 ШИФРОВКА" if ud.get('mode') == 'encode' else "🔓 ДЕШИФРОВКА"
    algo_label = ud.get('cipher', 'AES').upper()
    return ReplyKeyboardMarkup([
        [KeyboardButton(f"⚙️ МЕТОД: {algo_label}"), KeyboardButton(f"🔄 {mode_label}")],
        [KeyboardButton("📜 ИСТОРИЯ"), KeyboardButton("🧹 СБРОС")]
    ], resize_keyboard=True)

# --- ОБРАБОТКА КОМАНД ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.update({"cipher": "aes", "mode": "encode", "history": []})
    await update.message.reply_text(
        "💎 **CIPHER MASTER PRO**\n\nПришли текст, и я обработаю его мгновенно.",
        reply_markup=get_main_menu(ud), parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if "history" not in ud: ud["history"] = []
    text = update.message.text

    # Обработка кнопок меню
    if "⚙️ МЕТОД:" in text:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("AES-256", callback_data="set_aes"), 
             InlineKeyboardButton("Base64", callback_data="set_b64")]
        ])
        await update.message.reply_text("Выбери алгоритм:", reply_markup=kb)
        return

    if "🔄" in text:
        ud["mode"] = "decode" if ud.get("mode") == "encode" else "encode"
        await update.message.reply_text(f"Режим изменен!", reply_markup=get_main_menu(ud))
        return

    if text == "📜 ИСТОРИЯ":
        h = ud["history"][-5:]
        await update.message.reply_text("📜 **Последние 5 действий:**\n" + ("\n".join(h) if h else "Пусто"))
        return

    if text == "🧹 СБРОС":
        ud.update({"cipher": "aes", "mode": "encode", "history": []})
        await update.message.reply_text("Настройки сброшены.", reply_markup=get_main_menu(ud))
        return

    # Процесс шифрования
    res = crypt_engine(text, ud.get('mode'), ud.get('cipher'))
    ud["history"].append(f"{ud.get('mode')}: {text[:10]}... -> {res[:10]}...")
    await update.message.reply_text(f"**РЕЗУЛЬТАТ:**\n`{res}`", parse_mode="Markdown")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ud = context.user_data
    ud["cipher"] = query.data.replace("set_", "")
    await query.edit_message_text(f"✅ Установлен метод: {ud['cipher'].upper()}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Меню обновлено", reply_markup=get_main_menu(ud))

def main():
    # Application builder — единственный верный способ для v21.10
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Бот запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
