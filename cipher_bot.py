import logging
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ВСТРОЕННЫЕ ШИФРЫ (Работают молниеносно, не требуют ключей) ---
MORSE_DICT = { 'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 'F':'..-.', 'G':'--.', 'H':'....', 'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 'P':'.--.', 'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-', 'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-', 'Y':'-.--', 'Z':'--..', '1':'.----', '2':'..---', '3':'...--', '4':'....-', '5':'.....', '6':'-....', '7':'--...', '8':'---..', '9':'----.', '0':'-----', ' ':'/'}

def atbash(text):
    res = ""
    for c in text:
        if 'A' <= c <= 'Z': res += chr(155 - ord(c))
        elif 'a' <= c <= 'z': res += chr(219 - ord(c))
        elif 'А' <= c <= 'Я': res += chr(1071 - (ord(c) - 1040))
        elif 'а' <= c <= 'я': res += chr(1103 - (ord(c) - 1072))
        else: res += c
    return res

def process_text(text, cipher, mode):
    try:
        if cipher == 'base64':
            return base64.b64encode(text.encode()).decode() if mode == 'encode' else base64.b64decode(text.encode()).decode()
        elif cipher == 'hex':
            return text.encode().hex() if mode == 'encode' else bytes.fromhex(text).decode()
        elif cipher == 'atbash':
            return atbash(text) # Атбаш сам себя расшифровывает
        elif cipher == 'morse':
            if mode == 'encode':
                return ' '.join(MORSE_DICT.get(i.upper(), i) for i in text)
            else:
                inv_morse = {v: k for k, v in MORSE_DICT.items()}
                return ''.join(inv_morse.get(i, i) for i in text.split(' '))
        elif cipher == 'reverse':
            return text[::-1]
    except Exception:
        return "❌ Ошибка: проверьте текст или выбранный режим дешифровки."

# --- ИНТЕРФЕЙС (Максимально чистый) ---
def get_main_keyboard(ud):
    # Кнопки динамически меняют текст в зависимости от настроек
    mode_text = "🔓 Режим: ДЕШИФРОВАТЬ" if ud.get('mode') == 'decode' else "🔒 Режим: ЗАШИФРОВАТЬ"
    cipher_text = f"⚙️ Шифр: {ud.get('cipher', 'base64').upper()}"
    
    return ReplyKeyboardMarkup([
        [KeyboardButton(mode_text), KeyboardButton(cipher_text)]
    ], resize_keyboard=True)

# --- ЛОГИКА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    ud.update({'mode': 'encode', 'cipher': 'base64'})
    
    welcome_text = (
        "👋 **Привет! Это простой и быстрый шифратор.**\n\n"
        "Просто отправь мне любой текст, и я его обработаю.\n"
        "👇 Управляй настройками с помощью кнопок ниже."
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(ud), parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if 'mode' not in ud: ud.update({'mode': 'encode', 'cipher': 'base64'})
    text = update.message.text

    # Обработка кнопок
    if "Режим:" in text:
        ud['mode'] = 'decode' if ud['mode'] == 'encode' else 'encode'
        action = "расшифровки 🔓" if ud['mode'] == 'decode' else "шифрования 🔒"
        await update.message.reply_text(f"Включен режим {action}", reply_markup=get_main_keyboard(ud))
        return
        
    if "Шифр:" in text:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Base64", callback_data="b64"), InlineKeyboardButton("📟 HEX", callback_data="hex")],
            [InlineKeyboardButton("📜 Atbash", callback_data="atbash"), InlineKeyboardButton("📡 Morse", callback_data="morse")],
            [InlineKeyboardButton("🔄 Reverse (Задом наперед)", callback_data="reverse")]
        ])
        await update.message.reply_text("Выберите алгоритм:", reply_markup=kb)
        return

    # Шифрование / Дешифрование
    result = process_text(text, ud['cipher'], ud['mode'])
    icon = "🔓" if ud['mode'] == 'decode' else "🔒"
    
    # Красивый вывод с моноширинным шрифтом для копирования
    reply_text = f"{icon} **{ud['cipher'].upper()}**:\n\n`{result}`"
    await update.message.reply_text(reply_text, parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Убирает часики с кнопки моментально
    
    ud = context.user_data
    ud['cipher'] = query.data
    
    await query.edit_message_text(f"✅ Установлен шифр: **{ud['cipher'].upper()}**", parse_mode="Markdown")
    # Обновляем текст на нижней кнопке
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="👇 Настройки обновлены.", 
        reply_markup=get_main_keyboard(ud)
    )

def main():
    # Application.builder() гарантирует стабильность на Railway
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # drop_pending_updates=True очистит спам, накопившийся пока бот лежал
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
