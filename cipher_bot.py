"""
🔐 ШИФР — Telegram Bot
Установка: pip install python-telegram-bot
Запуск:    python cipher_bot.py
"""

import base64
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ================== ВСТАВЬ СВОЙ ТОКЕН ==================
BOT_TOKEN = "7649500751:AAGiUlZrXEb9IHlkfpx2KJPNB2PVcuYDeN8"
# =======================================================

logging.basicConfig(level=logging.INFO)

# ============================================================
#  ШИФРЫ
# ============================================================

def caesar_encode(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            if ch.isascii():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                # Кириллица
                base = 1040 if ch.isupper() else 1072
                idx = ord(ch) - base
                result.append(chr((idx + shift) % 32 + base))
        else:
            result.append(ch)
    return ''.join(result)

def caesar_decode(text: str, shift: int) -> str:
    return caesar_encode(text, -shift)


VIGENERE_ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def vigenere_encode(text: str, key: str) -> str:
    key = ''.join(c for c in key.upper() if c.isalpha()) or 'KEY'
    result, ki = [], 0
    for ch in text:
        if ch.upper() in VIGENERE_ALPHA:
            shift = ord(key[ki % len(key)]) - ord('A')
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return ''.join(result)

def vigenere_decode(text: str, key: str) -> str:
    key = ''.join(c for c in key.upper() if c.isalpha()) or 'KEY'
    result, ki = [], 0
    for ch in text:
        if ch.upper() in VIGENERE_ALPHA:
            shift = ord(key[ki % len(key)]) - ord('A')
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base - shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return ''.join(result)


def base64_encode(text: str) -> str:
    return base64.b64encode(text.encode('utf-8')).decode()

def base64_decode(text: str) -> str:
    try:
        return base64.b64decode(text.strip()).decode('utf-8')
    except Exception:
        return '❌ Ошибка: неверный Base64'


MORSE_MAP = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
    'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
    'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.','.'  :'.-.-.-',','  :'--..--','?':'..--..'
}
MORSE_REVERSE = {v: k for k, v in MORSE_MAP.items()}

def morse_encode(text: str) -> str:
    words = []
    for word in text.upper().split():
        codes = [MORSE_MAP.get(c, '?') for c in word if c in MORSE_MAP or c.isalpha()]
        if codes:
            words.append(' '.join(codes))
    return ' // '.join(words)

def morse_decode(text: str) -> str:
    words = []
    for word in text.split('//'):
        chars = [MORSE_REVERSE.get(c.strip(), '?') for c in word.strip().split()]
        words.append(''.join(chars))
    return ' '.join(words)


def atbash_encode(text: str) -> str:
    result = []
    for ch in text:
        if ch.isalpha() and ch.isascii():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr(base + 25 - (ord(ch) - base)))
        else:
            result.append(ch)
    return ''.join(result)


def rot47_encode(text: str) -> str:
    return ''.join(
        chr(33 + (ord(c) - 33 + 47) % 94) if 33 <= ord(c) <= 126 else c
        for c in text
    )


def hex_encode(text: str) -> str:
    return ' '.join(f'{b:02x}' for b in text.encode('utf-8'))

def hex_decode(text: str) -> str:
    try:
        return bytes.fromhex(text.replace(' ', '')).decode('utf-8')
    except Exception:
        return '❌ Ошибка: неверный HEX'


def binary_encode(text: str) -> str:
    return ' '.join(f'{b:08b}' for b in text.encode('utf-8'))

def binary_decode(text: str) -> str:
    try:
        parts = text.strip().split()
        return bytes([int(b, 2) for b in parts]).decode('utf-8')
    except Exception:
        return '❌ Ошибка: неверный бинарный код'


# ============================================================
#  СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
# user_state[user_id] = {'cipher': 'caesar', 'mode': 'encode', 'key': '13'}
user_state: dict[int, dict] = {}

CIPHER_LIST = [
    ('caesar',   '🔤 Цезарь',   'Сдвиг букв'),
    ('vigenere', '🔑 Виженер',  'Ключевое слово'),
    ('base64',   '📦 Base64',   'Кодирование'),
    ('morse',    '📡 Морзе',    'Точки и тире'),
    ('atbash',   '🔁 Атбаш',    'Зеркальный'),
    ('rot47',    '⚙️ ROT47',    'ASCII сдвиг'),
    ('hex',      '🟩 HEX',      '16-ричный'),
    ('binary',   '💻 BINARY',   'Двоичный код'),
]

NEEDS_KEY = {'caesar', 'vigenere'}

# ============================================================
#  КЛАВИАТУРЫ
# ============================================================

def main_keyboard():
    kb = [
        [InlineKeyboardButton("⬆ Зашифровать", callback_data='mode_encode'),
         InlineKeyboardButton("⬇ Расшифровать", callback_data='mode_decode')],
        [InlineKeyboardButton("🔐 Выбрать шифр", callback_data='choose_cipher')],
        [InlineKeyboardButton("ℹ️ Справка", callback_data='help')],
    ]
    return InlineKeyboardMarkup(kb)

def cipher_keyboard():
    kb = []
    row = []
    for i, (cid, name, desc) in enumerate(CIPHER_LIST):
        row.append(InlineKeyboardButton(name, callback_data=f'cipher_{cid}'))
        if len(row) == 2:
            kb.append(row); row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("◀ Назад", callback_data='back')])
    return InlineKeyboardMarkup(kb)

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀ Главное меню", callback_data='back')]])

# ============================================================
#  ОБРАБОТЧИКИ
# ============================================================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = {'cipher': 'caesar', 'mode': 'encode', 'key': '13'}
    await update.message.reply_text(
        "🔐 *ШИФР — Бот*\n\n"
        "Привет! Я умею шифровать и расшифровывать текст разными методами.\n\n"
        "Выбери режим и шифр, затем просто отправь текст — я его обработаю!",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if uid not in user_state:
        user_state[uid] = {'cipher': 'caesar', 'mode': 'encode', 'key': '13'}

    st = user_state[uid]

    if data == 'mode_encode':
        st['mode'] = 'encode'
        await query.edit_message_text(
            f"✅ Режим: *Шифрование*\nШифр: *{get_cipher_name(st['cipher'])}*\n\nОтправь текст для шифрования:",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )

    elif data == 'mode_decode':
        st['mode'] = 'decode'
        await query.edit_message_text(
            f"✅ Режим: *Дешифрование*\nШифр: *{get_cipher_name(st['cipher'])}*\n\nОтправь зашифрованный текст:",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )

    elif data == 'choose_cipher':
        await query.edit_message_text(
            "🔐 Выбери шифр:", reply_markup=cipher_keyboard()
        )

    elif data.startswith('cipher_'):
        cid = data[7:]
        st['cipher'] = cid
        name = get_cipher_name(cid)

        if cid == 'caesar':
            st['key'] = '13'
            msg = (f"✅ Шифр: *{name}*\n\n"
                   f"Текущий сдвиг: *{st['key']}*\n"
                   f"Чтобы изменить — напиши: `/key 7` (число 1-25)\n\n"
                   f"Теперь отправь текст!")
        elif cid == 'vigenere':
            st['key'] = 'KEY'
            msg = (f"✅ Шифр: *{name}*\n\n"
                   f"Текущий ключ: *{st['key']}*\n"
                   f"Чтобы изменить — напиши: `/key SECRET`\n\n"
                   f"Теперь отправь текст!")
        else:
            msg = f"✅ Шифр: *{name}*\n\nКлюч не нужен. Отправь текст!"

        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=main_keyboard())

    elif data == 'help':
        help_text = (
            "📖 *Справка*\n\n"
            "🔤 *Цезарь* — сдвиг букв на N позиций\n"
            "🔑 *Виженер* — шифр с ключевым словом\n"
            "📦 *Base64* — стандартное кодирование\n"
            "📡 *Морзе* — точки и тире\n"
            "🔁 *Атбаш* — зеркальный алфавит\n"
            "⚙️ *ROT47* — сдвиг ASCII символов\n"
            "🟩 *HEX* — шестнадцатеричный код\n"
            "💻 *BINARY* — двоичный код\n\n"
            "*/key значение* — установить ключ\n"
            "*/status* — текущие настройки\n"
            "*/start* — главное меню"
        )
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=back_keyboard())

    elif data == 'back':
        st = user_state.get(uid, {})
        await query.edit_message_text(
            f"🔐 *ШИФР — Бот*\n\nРежим: *{'Шифрование ⬆' if st.get('mode','encode')=='encode' else 'Дешифрование ⬇'}*\n"
            f"Шифр: *{get_cipher_name(st.get('cipher','caesar'))}*\n\nОтправь текст!",
            parse_mode='Markdown', reply_markup=main_keyboard()
        )


async def set_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_state:
        user_state[uid] = {'cipher': 'caesar', 'mode': 'encode', 'key': '13'}

    args = ctx.args
    if not args:
        await update.message.reply_text("Использование: `/key значение`\nПример: `/key 7` или `/key SECRET`", parse_mode='Markdown')
        return

    key = ' '.join(args)
    user_state[uid]['key'] = key
    await update.message.reply_text(f"✅ Ключ установлен: `{key}`", parse_mode='Markdown', reply_markup=main_keyboard())


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = user_state.get(uid, {'cipher': 'caesar', 'mode': 'encode', 'key': '13'})
    mode = "Шифрование ⬆" if st['mode'] == 'encode' else "Дешифрование ⬇"
    key_info = f"\nКлюч: `{st.get('key', '—')}`" if st['cipher'] in NEEDS_KEY else ""
    await update.message.reply_text(
        f"⚙️ *Текущие настройки*\n\nРежим: *{mode}*\nШифр: *{get_cipher_name(st['cipher'])}*{key_info}",
        parse_mode='Markdown', reply_markup=main_keyboard()
    )


async def process_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_state:
        user_state[uid] = {'cipher': 'caesar', 'mode': 'encode', 'key': '13'}

    st = user_state[uid]
    text = update.message.text
    cipher = st['cipher']
    mode = st['mode']
    key = st.get('key', '')

    try:
        result = apply_cipher(cipher, mode, text, key)
    except Exception as e:
        result = f"❌ Ошибка: {e}"

    mode_icon = "⬆" if mode == 'encode' else "⬇"
    reply = (
        f"{mode_icon} *{get_cipher_name(cipher)}*\n\n"
        f"```\n{result}\n```"
    )
    await update.message.reply_text(reply, parse_mode='Markdown', reply_markup=main_keyboard())


# ============================================================
#  ЛОГИКА ШИФРОВ
# ============================================================

def get_cipher_name(cid: str) -> str:
    return next((name for c, name, _ in CIPHER_LIST if c == cid), cid)

def apply_cipher(cipher: str, mode: str, text: str, key: str) -> str:
    enc = mode == 'encode'

    if cipher == 'caesar':
        shift = int(key) if key.lstrip('-').isdigit() else 13
        return caesar_encode(text, shift) if enc else caesar_decode(text, shift)

    elif cipher == 'vigenere':
        return vigenere_encode(text, key or 'KEY') if enc else vigenere_decode(text, key or 'KEY')

    elif cipher == 'base64':
        return base64_encode(text) if enc else base64_decode(text)

    elif cipher == 'morse':
        return morse_encode(text) if enc else morse_decode(text)

    elif cipher == 'atbash':
        return atbash_encode(text)  # симметричный

    elif cipher == 'rot47':
        return rot47_encode(text)  # симметричный

    elif cipher == 'hex':
        return hex_encode(text) if enc else hex_decode(text)

    elif cipher == 'binary':
        return binary_encode(text) if enc else binary_decode(text)

    return '❌ Неизвестный шифр'


# ============================================================
#  ЗАПУСК
# ============================================================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", set_key))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_text))

    print("🤖 Бот запущен! Нажми Ctrl+C для остановки.")
    app.run_polling()

if __name__ == '__main__':
    main()
