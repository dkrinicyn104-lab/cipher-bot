"""
🔐 ШИФР PRO — Telegram Bot
"""

import base64
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
logging.basicConfig(level=logging.INFO)

# ══════════════════════════════════════════
#  ШИФРЫ
# ══════════════════════════════════════════

def caesar_encode(text, shift):
    result = []
    for ch in text:
        if ch.isalpha():
            if ch.isascii():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                base = 1040 if ch.isupper() else 1072
                result.append(chr((ord(ch) - base + shift) % 32 + base))
        else:
            result.append(ch)
    return ''.join(result)

def vigenere_encode(text, key):
    key = ''.join(c for c in key.upper() if c.isalpha()) or 'KEY'
    result, ki = [], 0
    for ch in text:
        if ch.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            shift = ord(key[ki % len(key)]) - ord('A')
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return ''.join(result)

def vigenere_decode(text, key):
    key = ''.join(c for c in key.upper() if c.isalpha()) or 'KEY'
    result, ki = [], 0
    for ch in text:
        if ch.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            shift = ord(key[ki % len(key)]) - ord('A')
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base - shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return ''.join(result)

def base64_encode(text):
    return base64.b64encode(text.encode('utf-8')).decode()

def base64_decode(text):
    try:
        return base64.b64decode(text.strip()).decode('utf-8')
    except:
        return None

MORSE_MAP = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
    'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
    'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.','.'  :'.-.-.-',','  :'--..--','?':'..--..'
}
MORSE_REV = {v: k for k, v in MORSE_MAP.items()}

def morse_encode(text):
    words = []
    for word in text.upper().split():
        codes = [MORSE_MAP.get(c, '') for c in word if c in MORSE_MAP]
        if codes:
            words.append(' '.join(filter(None, codes)))
    return ' / '.join(words)

def morse_decode(text):
    words = []
    for word in text.split('/'):
        chars = [MORSE_REV.get(c.strip(), '?') for c in word.strip().split() if c.strip()]
        words.append(''.join(chars))
    return ' '.join(w for w in words if w)

def atbash(text):
    result = []
    for ch in text:
        if ch.isalpha() and ch.isascii():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr(base + 25 - (ord(ch) - base)))
        else:
            result.append(ch)
    return ''.join(result)

def rot47(text):
    return ''.join(chr(33 + (ord(c) - 33 + 47) % 94) if 33 <= ord(c) <= 126 else c for c in text)

def hex_encode(text):
    return ' '.join(f'{b:02x}' for b in text.encode('utf-8'))

def hex_decode(text):
    try:
        return bytes.fromhex(text.replace(' ', '')).decode('utf-8')
    except:
        return None

def binary_encode(text):
    return ' '.join(f'{b:08b}' for b in text.encode('utf-8'))

def binary_decode(text):
    try:
        return bytes([int(b, 2) for b in text.strip().split()]).decode('utf-8')
    except:
        return None

def apply_cipher(cipher, mode, text, key=''):
    enc = mode == 'encode'
    try:
        if cipher == 'caesar':
            shift = int(key) if key.lstrip('-').isdigit() else 13
            return caesar_encode(text, shift if enc else -shift)
        elif cipher == 'vigenere':
            return vigenere_encode(text, key or 'KEY') if enc else vigenere_decode(text, key or 'KEY')
        elif cipher == 'base64':
            r = base64_encode(text) if enc else base64_decode(text)
            return r if r else '⚠️ Не удалось декодировать'
        elif cipher == 'morse':
            return morse_encode(text) if enc else morse_decode(text)
        elif cipher == 'atbash':
            return atbash(text)
        elif cipher == 'rot47':
            return rot47(text)
        elif cipher == 'hex':
            r = hex_encode(text) if enc else hex_decode(text)
            return r if r else '⚠️ Не удалось декодировать'
        elif cipher == 'binary':
            r = binary_encode(text) if enc else binary_decode(text)
            return r if r else '⚠️ Не удалось декодировать'
    except Exception as e:
        return f'⚠️ Ошибка: {e}'
    return '⚠️ Неизвестный шифр'

# ══════════════════════════════════════════
#  ДАННЫЕ
# ══════════════════════════════════════════

user_data: dict = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {'cipher': 'base64', 'key': ''}
    return user_data[uid]

CIPHERS = [
    ('base64',  '📦 Base64',   'Любой язык ✓'),
    ('hex',     '🟩 HEX',      'Любой язык ✓'),
    ('binary',  '💻 Бинарный', 'Любой язык ✓'),
    ('caesar',  '🔤 Цезарь',   'Латиница'),
    ('vigenere','🔑 Виженер',  'Латиница'),
    ('morse',   '📡 Морзе',    'Латиница'),
    ('atbash',  '🔁 Атбаш',    'Латиница'),
    ('rot47',   '⚙️ ROT47',    'ASCII'),
]

CIPHER_INFO = {
    'base64':  ('📦', 'Base64',    'Кодирует любой текст и любой язык в безопасную ASCII строку.'),
    'hex':     ('🟩', 'HEX',       'Переводит каждый байт в шестнадцатеричное число.'),
    'binary':  ('💻', 'Бинарный',  'Переводит каждый символ в 8-битный двоичный код.'),
    'caesar':  ('🔤', 'Цезарь',    'Сдвигает каждую букву на N позиций в алфавите.'),
    'vigenere':('🔑', 'Виженер',   'Шифрует текст с помощью ключевого слова.'),
    'morse':   ('📡', 'Морзе',     'Кодирует буквы в точки и тире.'),
    'atbash':  ('🔁', 'Атбаш',     'Зеркалит алфавит: A↔Z, B↔Y...'),
    'rot47':   ('⚙️', 'ROT47',     'Сдвигает все ASCII-символы на 47 позиций.'),
}

def cipher_name(cid):
    info = CIPHER_INFO.get(cid, {})
    if info:
        return f"{info[0]} {info[1]}"
    return cid

DIVIDER = "─────────────────────"

# ══════════════════════════════════════════
#  КЛАВИАТУРЫ
# ══════════════════════════════════════════

def main_keyboard(cid):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Сменить шифр", callback_data='choose_cipher'),
            InlineKeyboardButton("ℹ️ О шифре", callback_data='cipher_info'),
        ],
    ])

def cipher_keyboard():
    kb = []
    for cid, name, note in CIPHERS:
        kb.append([InlineKeyboardButton(f"{name}  {note}", callback_data=f'set_{cid}')])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data='back_main')])
    return InlineKeyboardMarkup(kb)

# ══════════════════════════════════════════
#  ХЕНДЛЕРЫ
# ══════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "друг"
    st = get_user(uid)
    cid = st['cipher']
    emoji, title, _ = CIPHER_INFO[cid].values() if isinstance(CIPHER_INFO[cid], dict) else (CIPHER_INFO[cid][0], CIPHER_INFO[cid][1], '')
    info = CIPHER_INFO[cid]

    text = (
        f"🔐 *ШИФР PRO* — твой личный шифратор\n"
        f"{DIVIDER}\n\n"
        f"Привет, *{name}*! 👋\n\n"
        f"Просто напиши любой текст — и я мгновенно покажу:\n"
        f"  🔒 Зашифрованный вариант\n"
        f"  🔓 Расшифрованный вариант\n\n"
        f"{DIVIDER}\n"
        f"Текущий шифр: *{info[0]} {info[1]}*\n"
        f"{DIVIDER}\n\n"
        f"✏️ *Напиши текст прямо сейчас:*"
    )
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard(cid))


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)
    text = update.message.text
    st['last_text'] = text
    cid = st['cipher']
    key = st.get('key', '')
    info = CIPHER_INFO[cid]

    encoded = apply_cipher(cid, 'encode', text, key)
    decoded = apply_cipher(cid, 'decode', text, key)

    key_line = ''
    if cid == 'caesar':
        key_line = f"\n🔑 Ключ (сдвиг): *{key or '13'}*"
    elif cid == 'vigenere':
        key_line = f"\n🔑 Ключ: *{key or 'KEY'}*"

    msg = (
        f"*{info[0]} {info[1]}*{key_line}\n"
        f"{DIVIDER}\n\n"
        f"📝 *Исходный текст:*\n"
        f"`{text}`\n\n"
        f"🔒 *Зашифрованный:*\n"
        f"`{encoded}`\n\n"
        f"🔓 *Расшифрованный:*\n"
        f"`{decoded}`\n\n"
        f"{DIVIDER}\n"
        f"✏️ Напиши ещё текст или смени шифр:"
    )

    await update.message.reply_text(
        msg,
        parse_mode='Markdown',
        reply_markup=main_keyboard(cid)
    )


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    st = get_user(uid)
    data = query.data

    if data == 'choose_cipher':
        await query.edit_message_text(
            f"🔄 *Выбери шифр*\n"
            f"{DIVIDER}\n\n"
            f"Шифры с ✓ работают с русским языком:",
            parse_mode='Markdown',
            reply_markup=cipher_keyboard()
        )

    elif data.startswith('set_'):
        cid = data[4:]
        st['cipher'] = cid
        info = CIPHER_INFO[cid]

        if cid == 'caesar':
            st['key'] = '13'
            key_tip = "\n\n💡 Сдвиг по умолчанию: *13*\nИзменить: `/key 5`"
        elif cid == 'vigenere':
            st['key'] = 'KEY'
            key_tip = "\n\n💡 Ключ по умолчанию: *KEY*\nИзменить: `/key ПАРОЛЬ`"
        else:
            st['key'] = ''
            key_tip = ""

        await query.edit_message_text(
            f"✅ *Шифр выбран!*\n"
            f"{DIVIDER}\n\n"
            f"*{info[0]} {info[1]}*\n"
            f"_{info[2]}_"
            f"{key_tip}\n\n"
            f"{DIVIDER}\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(cid)
        )

    elif data == 'cipher_info':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        key_info = ''
        if cid == 'caesar':
            key_info = f"\n🔑 Текущий сдвиг: *{st.get('key','13')}*\nИзменить: `/key 7`"
        elif cid == 'vigenere':
            key_info = f"\n🔑 Текущий ключ: *{st.get('key','KEY')}*\nИзменить: `/key СЛОВО`"

        await query.edit_message_text(
            f"*{info[0]} {info[1]}*\n"
            f"{DIVIDER}\n\n"
            f"📖 *Описание:*\n_{info[2]}_"
            f"{key_info}\n\n"
            f"{DIVIDER}\n"
            f"✏️ Напиши текст для шифрования:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Сменить шифр", callback_data='choose_cipher')],
                [InlineKeyboardButton("◀️ Назад", callback_data='back_main')],
            ])
        )

    elif data == 'back_main':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        await query.edit_message_text(
            f"🔐 *ШИФР PRO*\n"
            f"{DIVIDER}\n\n"
            f"Текущий шифр: *{info[0]} {info[1]}*\n\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(cid)
        )


async def set_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)
    args = ctx.args
    if not args:
        await update.message.reply_text(
            f"💡 *Использование:*\n`/key значение`\n\nПримеры:\n`/key 7` — для Цезаря\n`/key SECRET` — для Виженера",
            parse_mode='Markdown'
        )
        return
    st['key'] = ' '.join(args)
    cid = st['cipher']
    info = CIPHER_INFO[cid]
    await update.message.reply_text(
        f"✅ *Ключ установлен!*\n"
        f"{DIVIDER}\n\n"
        f"Шифр: *{info[0]} {info[1]}*\n"
        f"Ключ: `{st['key']}`\n\n"
        f"✏️ Напиши текст:",
        parse_mode='Markdown',
        reply_markup=main_keyboard(cid)
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", set_key))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🤖 ШИФР PRO запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
