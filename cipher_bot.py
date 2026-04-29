import logging
import base64
import binascii
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- АЛГОРИТМЫ ШИФРОВАНИЯ ---
MORSE_DICT = { 'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 'F':'..-.', 'G':'--.', 'H':'....', 'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 'P':'.--.', 'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-', 'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-', 'Y':'-.--', 'Z':'--..', '1':'.----', '2':'..---', '3':'...--', '4':'....-', '5':'.....', '6':'-....', '7':'--...', '8':'---..', '9':'----.', '0':'-----', ' ':'/'}
INV_MORSE = {v: k for k, v in MORSE_DICT.items()}

def atbash(text: str) -> str:
    res = ""
    for c in text:
        if 'A' <= c <= 'Z': res += chr(155 - ord(c))
        elif 'a' <= c <= 'z': res += chr(219 - ord(c))
        elif 'А' <= c <= 'Я': res += chr(1071 - (ord(c) - 1040))
        elif 'а' <= c <= 'я': res += chr(1103 - (ord(c) - 1072))
        else: res += c
    return res

def process_text(text: str, cipher: str, mode: str) -> tuple[bool, str]:
    """Возвращает кортеж (Успех_ли, Результат_или_Ошибка)"""
    try:
        if cipher == 'base64':
            if mode == 'encode':
                return True, base64.b64encode(text.encode('utf-8')).decode('utf-8')
            else:
                return True, base64.b64decode(text.encode('utf-8')).decode('utf-8')
                
        elif cipher == 'hex':
            if mode == 'encode':
                return True, text.encode('utf-8').hex().upper()
            else:
                return True, bytes.fromhex(text).decode('utf-8')
                
        elif cipher == 'atbash':
            return True, atbash(text) # Атбаш симметричен
            
        elif cipher == 'morse':
            if mode == 'encode':
                return True, ' '.join(MORSE_DICT.get(i.upper(), i) for i in text)
            else:
                return True, ''.join(INV_MORSE.get(i, i) for i in text.split(' '))
                
        elif cipher == 'reverse':
            return True, text[::-1]
            
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return False, "Текст не соответствует формату выбранного шифра."
    except Exception as e:
        return False, f"Неизвестная ошибка: {e}"

# --- ИНТЕРФЕЙС И КЛАВИАТУРЫ ---
CIPHER_NAMES = {
    'base64': '📦 Base64',
    'hex': '📟 HEX',
    'atbash': '📜 Atbash',
    'morse': '📡 Morse',
    'reverse': '🔄 Reverse'
}

def get_main_keyboard(user_data: dict) -> ReplyKeyboardMarkup:
    mode_text = "🔓 Режим: ДЕШИФРОВАТЬ" if user_data.get('mode') == 'decode' else "🔒 Режим: ЗАШИФРОВАТЬ"
    cipher_id = user_data.get('cipher', 'base64')
    cipher_text = f"⚙️ Шифр: {CIPHER_NAMES.get(cipher_id, 'Base64')}"
    
    return ReplyKeyboardMarkup([
        [KeyboardButton(mode_text), KeyboardButton(cipher_text)]
    ], resize_keyboard=True)

def get_cipher_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Base64", callback_data="set_base64"), InlineKeyboardButton("📟 HEX", callback_data="set_hex")],
        [InlineKeyboardButton("📜 Atbash", callback_data="set_atbash"), InlineKeyboardButton("📡 Morse", callback_data="set_morse")],
        [InlineKeyboardButton("🔄 Задом наперед (Reverse)", callback_data="set_reverse")]
    ])

# --- ЛОГИКА БОТА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if 'mode' not in ud: ud['mode'] = 'encode'
    if 'cipher' not in ud: ud['cipher'] = 'base64'
    
    welcome_text = (
        "👋 <b>Добро пожаловать в MASTER CIPHER!</b>\n\n"
        "Я — ваш надежный инструмент для быстрого преобразования текста.\n"
        "Просто отправьте мне сообщение, и я обработаю его согласно текущим настройкам.\n\n"
        "👇 <i>Используйте кнопки меню для управления.</i>"
    )
    await update.message.reply_text(
        welcome_text, 
        reply_markup=get_main_keyboard(ud), 
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if 'mode' not in ud: ud['mode'] = 'encode'
    if 'cipher' not in ud: ud['cipher'] = 'base64'
    
    text = update.message.text

    # Обработка кнопок нижнего меню
    if text.startswith("🔓 Режим:") or text.startswith("🔒 Режим:"):
        ud['mode'] = 'decode' if ud['mode'] == 'encode' else 'encode'
        action_text = "<b>расшифровки</b> 🔓" if ud['mode'] == 'decode' else "<b>шифрования</b> 🔒"
        await update.message.reply_text(
            f"✅ Установлен режим {action_text}.\nОтправьте текст.", 
            reply_markup=get_main_keyboard(ud),
            parse_mode=ParseMode.HTML
        )
        return
        
    if text.startswith("⚙️ Шифр:"):
        await update.message.reply_text(
            "<b>Выберите алгоритм:</b>", 
            reply_markup=get_cipher_inline_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return

    # Обработка самого текста (Шифрование / Дешифрование)
    success, result = process_text(text, ud['cipher'], ud['mode'])
    
    cipher_name = CIPHER_NAMES.get(ud['cipher'], ud['cipher'].upper())
    action_icon = "🔓" if ud['mode'] == 'decode' else "🔒"
    
    if success:
        # Тег <code> делает текст моноширинным и позволяет скопировать его одним тапом
        reply_text = f"{action_icon} <b>Результат ({cipher_name}):</b>\n\n<code>{result}</code>"
    else:
        reply_text = f"❌ <b>Ошибка!</b>\n\n<i>{result}</i>"
        
    await update.message.reply_text(reply_text, parse_mode=ParseMode.HTML)

async def inline_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Моментально убираем "часики" загрузки с кнопки
    
    ud = context.user_data
    # Получаем название шифра из callback_data (например, set_base64 -> base64)
    selected_cipher = query.data.split('_')[1]
    ud['cipher'] = selected_cipher
    
    cipher_name = CIPHER_NAMES.get(selected_cipher, selected_cipher.upper())
    
    # Обновляем сообщение с инлайн-клавиатурой
    await query.edit_message_text(
        f"✅ Установлен алгоритм: <b>{cipher_name}</b>", 
        parse_mode=ParseMode.HTML
    )
    
    # Тихо обновляем нижнюю клавиатуру, чтобы она соответствовала выбору
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Настройки обновлены. Жду ваш текст 📝", 
        reply_markup=get_main_keyboard(ud)
    )

def main():
    # Используем Application Builder для версии 20+ (идеально для Railway)
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(inline_callback, pattern="^set_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # drop_pending_updates=True очистит спам, пока бот был оффлайн
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
