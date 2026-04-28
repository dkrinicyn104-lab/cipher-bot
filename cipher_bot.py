"""
🔐 ШИФР ULTIMATE — Telegram Bot
"""

import base64
import logging
import os
import re
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
        result = base64.b64decode(text.strip() + '==').decode('utf-8')
        return result if result.isprintable() else None
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
        if chars:
            words.append(''.join(chars))
    result = ' '.join(w for w in words if w)
    return result if '?' not in result else None

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
        result = bytes.fromhex(text.replace(' ', '')).decode('utf-8')
        return result if result.isprintable() else None
    except:
        return None

def binary_encode(text):
    return ' '.join(f'{b:08b}' for b in text.encode('utf-8'))

def binary_decode(text):
    try:
        parts = text.strip().split()
        if not all(set(p) <= {'0','1'} for p in parts):
            return None
        result = bytes([int(b, 2) for b in parts]).decode('utf-8')
        return result if result.isprintable() else None
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
            return base64_encode(text) if enc else (base64_decode(text) or '⚠️ Не Base64')
        elif cipher == 'morse':
            return morse_encode(text) if enc else (morse_decode(text) or '⚠️ Неверный Морзе')
        elif cipher == 'atbash':
            return atbash(text)
        elif cipher == 'rot47':
            return rot47(text)
        elif cipher == 'hex':
            return hex_encode(text) if enc else (hex_decode(text) or '⚠️ Неверный HEX')
        elif cipher == 'binary':
            return binary_encode(text) if enc else (binary_decode(text) or '⚠️ Неверный Binary')
    except Exception as e:
        return f'⚠️ Ошибка: {e}'
    return '⚠️ Неизвестный шифр'

# ══════════════════════════════════════════
#  АВТООПРЕДЕЛЕНИЕ ШИФРА
# ══════════════════════════════════════════

def auto_detect(text):
    """Пробует все шифры и возвращает список результатов"""
    results = []

    # Base64
    r = base64_decode(text)
    if r and r != text and len(r) > 0:
        results.append(('📦 Base64', r))

    # HEX
    r = hex_decode(text)
    if r and r != text:
        results.append(('🟩 HEX', r))

    # Binary
    r = binary_decode(text)
    if r and r != text:
        results.append(('💻 Binary', r))

    # Морзе
    r = morse_decode(text)
    if r and r != text and '?' not in r:
        results.append(('📡 Морзе', r))

    # Атбаш
    r = atbash(text)
    if r and r != text:
        results.append(('🔁 Атбаш', r))

    # ROT47
    r = rot47(text)
    if r and r != text:
        results.append(('⚙️ ROT47', r))

    # Цезарь (перебираем популярные сдвиги)
    for shift in [3, 7, 13, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12]:
        r = caesar_encode(text, -shift)
        if r != text and r.isprintable():
            results.append((f'🔤 Цезарь (сдвиг -{shift})', r))
            break

    return results

# ══════════════════════════════════════════
#  ДАННЫЕ
# ══════════════════════════════════════════

user_data: dict = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {'cipher': 'base64', 'key': '', 'mode': 'both', 'history': []}
    return user_data[uid]

CIPHERS = [
    ('base64',  '📦 Base64',    '🌍 Любой язык'),
    ('hex',     '🟩 HEX',       '🌍 Любой язык'),
    ('binary',  '💻 Binary',    '🌍 Любой язык'),
    ('caesar',  '🔤 Цезарь',    '🔡 Латиница'),
    ('vigenere','🔑 Виженер',   '🔡 Латиница'),
    ('morse',   '📡 Морзе',     '🔡 Латиница'),
    ('atbash',  '🔁 Атбаш',     '🔡 Латиница'),
    ('rot47',   '⚙️ ROT47',     '🔣 ASCII'),
]

CIPHER_INFO = {
    'base64':   ('📦', 'Base64',   'Кодирует любой текст в безопасную строку. Работает с любым языком включая русский.'),
    'hex':      ('🟩', 'HEX',      'Переводит каждый байт в шестнадцатеричное число. Работает с любым языком.'),
    'binary':   ('💻', 'Binary',   'Переводит каждый символ в 8-битный двоичный код. Работает с любым языком.'),
    'caesar':   ('🔤', 'Цезарь',   'Сдвигает каждую букву на N позиций в алфавите. Только латиница.'),
    'vigenere': ('🔑', 'Виженер',  'Шифрует с помощью ключевого слова. Только латиница.'),
    'morse':    ('📡', 'Морзе',    'Кодирует буквы в точки и тире. Только латиница.'),
    'atbash':   ('🔁', 'Атбаш',    'Зеркалит алфавит: A↔Z, B↔Y. Симметричный — шифр = дешифр.'),
    'rot47':    ('⚙️', 'ROT47',    'Сдвигает все ASCII-символы на 47. Симметричный.'),
}

D = "━━━━━━━━━━━━━━━━━━━━"

def cipher_label(cid):
    i = CIPHER_INFO[cid]
    return f"{i[0]} {i[1]}"

# ══════════════════════════════════════════
#  КЛАВИАТУРЫ
# ══════════════════════════════════════════

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Шифр", callback_data='choose_cipher'),
            InlineKeyboardButton("🔍 Авто", callback_data='auto_mode'),
            InlineKeyboardButton("ℹ️ Инфо", callback_data='cipher_info'),
        ],
        [
            InlineKeyboardButton("📜 История", callback_data='history'),
            InlineKeyboardButton("🗑 Очистить", callback_data='clear_history'),
        ],
    ])

def cipher_keyboard():
    kb = []
    for cid, name, note in CIPHERS:
        kb.append([InlineKeyboardButton(f"{name}  {note}", callback_data=f'set_{cid}')])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data='back_main')])
    return InlineKeyboardMarkup(kb)

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='back_main')]])

# ══════════════════════════════════════════
#  ХЕНДЛЕРЫ
# ══════════════════════════════════════════

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "друг"
    st = get_user(uid)
    cid = st['cipher']
    info = CIPHER_INFO[cid]

    text = (
        f"🔐 *ШИФР ULTIMATE*\n"
        f"{D}\n\n"
        f"Привет, *{name}*! 👋\n\n"
        f"Я умею:\n"
        f"  🔒 Зашифровывать любой текст\n"
        f"  🔓 Расшифровывать шифры\n"
        f"  🔍 *Автоматически определять шифр*\n\n"
        f"{D}\n"
        f"Текущий шифр: *{info[0]} {info[1]}*\n"
        f"{D}\n\n"
        f"✏️ *Просто напиши текст — и я всё сделаю!*"
    )
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard())


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)
    text = update.message.text
    cid = st['cipher']
    key = st.get('key', '')
    info = CIPHER_INFO[cid]

    # Сохраняем в историю
    if 'history' not in st:
        st['history'] = []

    encoded = apply_cipher(cid, 'encode', text, key)
    decoded = apply_cipher(cid, 'decode', text, key)

    # Определяем успешность расшифровки
    decode_ok = decoded and not decoded.startswith('⚠️')
    encode_ok = encoded and not encoded.startswith('⚠️')

    # Сохраняем в историю
    st['history'].append({'text': text, 'encoded': encoded, 'cipher': cid})
    if len(st['history']) > 10:
        st['history'] = st['history'][-10:]

    key_line = ''
    if cid == 'caesar':
        key_line = f"  🔑 Сдвиг: `{key or '13'}`\n"
    elif cid == 'vigenere':
        key_line = f"  🔑 Ключ: `{key or 'KEY'}`\n"

    decode_line = f"`{decoded}`" if decode_ok else f"_Введи зашифрованный текст для расшифровки_"

    msg = (
        f"*{info[0]} {info[1]}*\n"
        f"{key_line}"
        f"{D}\n\n"
        f"📝 *Исходный:*\n`{text}`\n\n"
        f"🔒 *Зашифрованный:*\n`{encoded}`\n\n"
        f"🔓 *Расшифрованный:*\n{decode_line}\n\n"
        f"{D}\n"
        f"💡 _Отправь зашифрованный текст чтобы его расшифровать_\n"
        f"💡 _Нажми 🔍 Авто чтобы определить шифр автоматически_"
    )

    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=main_keyboard())


async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    st = get_user(uid)
    data = query.data

    if data == 'choose_cipher':
        await query.edit_message_text(
            f"🔄 *Выбери шифр*\n{D}\n\n"
            f"🌍 — работает с русским языком\n"
            f"🔡 — только латиница\n"
            f"🔣 — только ASCII символы",
            parse_mode='Markdown',
            reply_markup=cipher_keyboard()
        )

    elif data.startswith('set_'):
        cid = data[4:]
        st['cipher'] = cid
        info = CIPHER_INFO[cid]

        if cid == 'caesar':
            st['key'] = '13'
            key_tip = f"\n\n🔑 Сдвиг: *13*\nИзменить: `/key 5`"
        elif cid == 'vigenere':
            st['key'] = 'KEY'
            key_tip = f"\n\n🔑 Ключ: *KEY*\nИзменить: `/key ПАРОЛЬ`"
        else:
            st['key'] = ''
            key_tip = ""

        await query.edit_message_text(
            f"✅ *Шифр выбран!*\n{D}\n\n"
            f"*{info[0]} {info[1]}*\n"
            f"_{info[2]}_"
            f"{key_tip}\n\n"
            f"{D}\n✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )

    elif data == 'auto_mode':
        await query.edit_message_text(
            f"🔍 *Авто-определение шифра*\n{D}\n\n"
            f"Отправь зашифрованный текст — и я попробую\n"
            f"автоматически определить его тип!\n\n"
            f"Поддерживаю: Base64, HEX, Binary,\nМорзе, Атбаш, ROT47, Цезарь\n\n"
            f"{D}\n✏️ *Напиши зашифрованный текст:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 Включить авто-режим", callback_data='enable_auto')],
                [InlineKeyboardButton("◀️ Назад", callback_data='back_main')],
            ])
        )

    elif data == 'enable_auto':
        st['auto_mode'] = True
        await query.edit_message_text(
            f"🔍 *Авто-режим включён!*\n{D}\n\n"
            f"Теперь отправь зашифрованный текст —\n"
            f"я сам определю шифр и расшифрую!\n\n"
            f"{D}\n✏️ *Напиши зашифрованный текст:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Выключить авто", callback_data='disable_auto')],
                [InlineKeyboardButton("◀️ Назад", callback_data='back_main')],
            ])
        )

    elif data == 'disable_auto':
        st['auto_mode'] = False
        await query.edit_message_text(
            f"✅ *Авто-режим выключен*\n{D}\n\n"
            f"Текущий шифр: *{cipher_label(st['cipher'])}*\n\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )

    elif data == 'cipher_info':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        key_info = ''
        if cid == 'caesar':
            key_info = f"\n🔑 Текущий сдвиг: *{st.get('key','13')}*\nИзменить: `/key 7`"
        elif cid == 'vigenere':
            key_info = f"\n🔑 Текущий ключ: *{st.get('key','KEY')}*\nИзменить: `/key СЛОВО`"

        auto_status = "🟢 Включён" if st.get('auto_mode') else "🔴 Выключен"

        await query.edit_message_text(
            f"*{info[0]} {info[1]}*\n{D}\n\n"
            f"📖 *Описание:*\n_{info[2]}_"
            f"{key_info}\n\n"
            f"{D}\n"
            f"🔍 Авто-режим: {auto_status}\n"
            f"📊 Записей в истории: *{len(st.get('history', []))}*\n"
            f"{D}\n\n"
            f"*Все шифры:*\n"
            + '\n'.join([f"  {CIPHER_INFO[c[0]][0]} {CIPHER_INFO[c[0]][1]} — {c[2]}" for c in CIPHERS]),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data='back_main')],
            ])
        )

    elif data == 'history':
        history = st.get('history', [])
        if not history:
            await query.edit_message_text(
                f"📜 *История пуста*\n{D}\n\n"
                f"Отправь текст чтобы начать!",
                parse_mode='Markdown',
                reply_markup=back_keyboard()
            )
            return

        lines = [f"📜 *Последние {len(history)} записей:*\n{D}\n"]
        for i, h in enumerate(reversed(history[-5:]), 1):
            lines.append(f"*{i}.* `{h['text'][:20]}{'...' if len(h['text'])>20 else ''}`")
            lines.append(f"   → `{h['encoded'][:25]}{'...' if len(h['encoded'])>25 else ''}`")
            lines.append(f"   _шифр: {cipher_label(h['cipher'])}_\n")

        await query.edit_message_text(
            '\n'.join(lines),
            parse_mode='Markdown',
            reply_markup=back_keyboard()
        )

    elif data == 'clear_history':
        st['history'] = []
        await query.edit_message_text(
            f"🗑 *История очищена!*\n{D}\n\n"
            f"✏️ Напиши текст:",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )

    elif data == 'back_main':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        auto = " 🔍" if st.get('auto_mode') else ""
        await query.edit_message_text(
            f"🔐 *ШИФР ULTIMATE*{auto}\n{D}\n\n"
            f"Шифр: *{info[0]} {info[1]}*\n\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard()
        )


async def handle_text_with_auto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)

    if st.get('auto_mode'):
        text = update.message.text
        results = auto_detect(text)

        if not results:
            await update.message.reply_text(
                f"🔍 *Авто-определение*\n{D}\n\n"
                f"📝 Текст: `{text}`\n\n"
                f"❌ *Не удалось определить шифр*\n\n"
                f"Попробуй выбрать шифр вручную:\n"
                f"📦 Base64, 🟩 HEX, 💻 Binary, 📡 Морзе...",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Выбрать шифр", callback_data='choose_cipher')],
                    [InlineKeyboardButton("❌ Выключить авто", callback_data='disable_auto')],
                ])
            )
            return

        lines = [f"🔍 *Авто-определение*\n{D}\n\n📝 Текст: `{text}`\n\n*Найденные варианты:*\n"]
        for cipher_name_str, result in results[:5]:
            lines.append(f"*{cipher_name_str}*\n`{result}`\n")

        await update.message.reply_text(
            '\n'.join(lines),
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Выключить авто", callback_data='disable_auto')],
                [InlineKeyboardButton("◀️ Главное меню", callback_data='back_main')],
            ])
        )
    else:
        await handle_text(update, ctx)


async def set_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)
    args = ctx.args
    if not args:
        await update.message.reply_text(
            f"💡 *Использование:* `/key значение`\n\n"
            f"Примеры:\n`/key 7` — сдвиг для Цезаря\n`/key SECRET` — ключ для Виженера",
            parse_mode='Markdown'
        )
        return
    st['key'] = ' '.join(args)
    cid = st['cipher']
    info = CIPHER_INFO[cid]
    await update.message.reply_text(
        f"✅ *Ключ установлен!*\n{D}\n\n"
        f"Шифр: *{info[0]} {info[1]}*\n"
        f"Ключ: `{st['key']}`\n\n"
        f"✏️ Напиши текст:",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📖 *СПРАВКА*\n{D}\n\n"
        f"*Как пользоваться:*\n"
        f"  1. Напиши любой текст\n"
        f"  2. Получи зашифрованный вариант\n"
        f"  3. Отправь шифр другу\n"
        f"  4. Друг вставляет шифр в бота\n"
        f"  5. Получает оригинал!\n\n"
        f"{D}\n"
        f"*Кнопки:*\n"
        f"  🔄 Шифр — выбрать метод шифрования\n"
        f"  🔍 Авто — автоматически определить шифр\n"
        f"  ℹ️ Инфо — информация о текущем шифре\n"
        f"  📜 История — последние 10 шифрований\n"
        f"  🗑 Очистить — очистить историю\n\n"
        f"{D}\n"
        f"*Команды:*\n"
        f"  `/start` — начать заново\n"
        f"  `/key значение` — установить ключ\n"
        f"  `/help` — эта справка\n\n"
        f"{D}\n"
        f"*Шифры для русского языка:*\n"
        f"  📦 Base64, 🟩 HEX, 💻 Binary\n\n"
        f"*Шифры для латиницы:*\n"
        f"  🔤 Цезарь, 🔑 Виженер, 📡 Морзе, 🔁 Атбаш, ⚙️ ROT47",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", set_key))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_with_auto))
    print("🔐 ШИФР ULTIMATE запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
