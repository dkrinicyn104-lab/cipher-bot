import logging
import base64
import hashlib
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.helpers import escape_markdown

# --- КОНФИГУРАЦИЯ ---
BOT_TOKEN = "7649500751:AAGUWL2O2epfFFvdO6mjHZX3ZelEBCwuJTQ"

logging.basicConfig(level=logging.INFO)

# --- ДИЗАЙН ---
UI_SEP = "────────────────────"
THEME_TITLE = "🔓 **CIPHER TERMINAL v5.0**"

# --- ЯДРО АЛГОРИТМОВ ---

MORSE_DICT = {'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 'F':'..-.', 'G':'--.', 'H':'....', 'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 'P':'.--.', 'Q':'--.-', 'R':'.-.', 'S':'...', 'T':'-', 'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-', 'Y':'-.--', 'Z':'--..', '1':'.----', '2':'..---', '3':'...--', '4':'....-', '5':'.....', '6':'-....', '7':'--...', '8':'---..', '9':'----.', '0':'-----', ' ': '/'}

def caesar_pro(text, shift):
    res = ""
    for char in text:
        if char.isalpha():
            start = ord('A') if char.isupper() else ord('a')
            alphabet_size = 32 if 'а' <= char.lower() <= 'я' else 26
            if 'а' <= char.lower() <= 'я': start = ord('А') if char.isupper() else ord('а')
            res += chr((ord(char) - start + shift) % alphabet_size + start)
        else: res += char
    return res

def text_to_bits(text):
    return ' '.join(format(ord(x), '08b') for x in text)

def bits_to_text(bits):
    try: return "".join([chr(int(b, 2)) for b in bits.split()])
    except: return "⚠️ Ошибка декодирования Binary"

# --- КЛАВИАТУРЫ ---

def main_menu_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⚙️ ТЕРМИНАЛ"), KeyboardButton("👤 ПРОФИЛЬ")],
        [KeyboardButton("🆘 ИНФО / ПОМОЩЬ")]
    ], resize_keyboard=True)

def settings_kb(ud):
    mode = "ШИФРОВКА 🔐" if ud['mode'] == 'encode' else "ДЕШИФРОВКА 🔓"
    auto = "ВКЛ 🔵" if ud['auto'] else "ВЫКЛ ⚪"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📡 АЛГОРИТМ: {ud['cipher'].upper()}", callback_data="list")],
        [InlineKeyboardButton(f"🔄 РЕЖИМ: {mode}", callback_data="t_mode")],
        [InlineKeyboardButton(f"🤖 АВТО: {auto}", callback_data="t_auto"), InlineKeyboardButton("🔑 КЛЮЧ", callback_data="s_key")],
        [InlineKeyboardButton("❌ ЗАКРЫТЬ", callback_data="close")]
    ])

def algorithms_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("BASE64", callback_data="set_base64"), InlineKeyboardButton("HEX", callback_data="set_hex")],
        [InlineKeyboardButton("CAESAR", callback_data="set_caesar"), InlineKeyboardButton("VIGENERE", callback_data="set_vigenere")],
        [InlineKeyboardButton("BINARY", callback_data="set_binary"), InlineKeyboardButton("MORSE", callback_data="set_morse")],
        [InlineKeyboardButton("SHA256", callback_data="set_sha256"), InlineKeyboardButton("REVERSE", callback_data="set_reverse")],
        [InlineKeyboardButton("⬅️ НАЗАД", callback_data="back")]
    ])

# --- ЛОГИКА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    for k, v in {"cipher": "base64", "mode": "encode", "key": "secret", "auto": False, "state": "idle"}.items():
        ud.setdefault(k, v)
    
    await update.message.reply_text(
        f"{THEME_TITLE}\n{UI_SEP}\nСистема инициализирована. Ожидаю данные...",
        reply_markup=main_menu_kb(), parse_mode="Markdown"
    )

async def handle_ui(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    text = update.message.text

    if text == "⚙️ ТЕРМИНАЛ":
        await update.message.reply_text(f"🛰 **УПРАВЛЕНИЕ ПРОТОКОЛАМИ:**\n{UI_SEP}", 
                                       reply_markup=settings_kb(ud), parse_mode="Markdown")
    elif text == "👤 ПРОФИЛЬ":
        p = (f"👤 **ВАШ ПРОФИЛЬ:**\n{UI_SEP}\n"
             f"● Шифр: `{ud['cipher'].upper()}`\n"
             f"● Режим: `{ud['mode'].upper()}`\n"
             f"● Ключ: `{ud['key']}`\n"
             f"● Авто-детект: `{'АКТИВЕН' if ud['auto'] else 'ВЫКЛЮЧЕН'}`")
        await update.message.reply_text(p, parse_mode="Markdown")
    elif text == "🆘 ИНФО / ПОМОЩЬ":
        await update.message.reply_text("📖 **ИНСТРУКЦИЯ:**\n1. Настрой шифр в 'ТЕРМИНАЛЕ'\n2. Отправь текст в чат\n3. Получи мгновенный результат.", parse_mode="Markdown")
    
    elif ud.get("state") == "waiting_key":
        ud["key"], ud["state"] = text, "idle"
        await update.message.reply_text(f"🔑 **КЛЮЧ УСТАНОВЛЕН:** `{text}`", parse_mode="Markdown")
    
    else:
        # ОБРАБОТКА ТЕКСТА
        c, m = ud['cipher'], ud['mode']
        res = ""
        try:
            if c == "base64":
                res = base64.b64encode(text.encode()).decode() if m == "encode" else base64.b64decode(text).decode()
            elif c == "hex":
                res = text.encode().hex() if m == "encode" else bytes.fromhex(text).decode()
            elif c == "binary":
                res = text_to_bits(text) if m == "encode" else bits_to_text(text)
            elif c == "caesar":
                res = caesar_pro(text, 3 if m == "encode" else -3)
            elif c == "reverse":
                res = text[::-1]
            elif c == "sha256":
                res = hashlib.sha256(text.encode()).hexdigest()
            elif c == "morse":
                if m == "encode": res = " ".join(MORSE_DICT.get(c.upper(), '') for c in text)
                else:
                    inv_morse = {v: k for k, v in MORSE_DICT.items()}
                    res = "".join(inv_morse.get(b, '') for b in text.split())
            else: res = "Алгортим в разработке..."

            await update.message.reply_text(f"📥 **INPUT:** `{text}`\n📤 **OUTPUT:**\n`{res}`", parse_mode="Markdown")
        except:
            await update.message.reply_text("⚠️ **ERROR:** Ошибка обработки. Проверьте формат.")

async def button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Убирает задержку
    ud = context.user_data
    data = query.data

    if data == "back":
        await query.edit_message_text(f"🛰 **УПРАВЛЕНИЕ ПРОТОКОЛАМИ:**\n{UI_SEP}", reply_markup=settings_kb(ud), parse_mode="Markdown")
    elif data == "t_mode":
        ud["mode"] = "decode" if ud["mode"] == "encode" else "encode"
        await query.edit_message_reply_markup(reply_markup=settings_kb(ud))
    elif data == "t_auto":
        ud["auto"] = not ud["auto"]
        await query.edit_message_reply_markup(reply_markup=settings_kb(ud))
    elif data == "list":
        await query.edit_message_text(f"📡 **ВЫБОР АЛГОРИТМА:**\n{UI_SEP}", reply_markup=algorithms_kb(), parse_mode="Markdown")
    elif data.startswith("set_"):
        ud["cipher"] = data.replace("set_", "")
        await query.edit_message_text(f"✅ **АКТИВИРОВАН:** `{ud['cipher'].upper()}`", reply_markup=settings_kb(ud), parse_mode="Markdown")
    elif data == "s_key":
        ud["state"] = "waiting_key"
        await query.edit_message_text("⌨️ **ВВЕДИТЕ НОВЫЙ КЛЮЧ:**", parse_mode="Markdown")
    elif data == "close":
        await query.delete_message()

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_tap))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ui))
    app.run_polling()

if __name__ == "__main__":
    main()
