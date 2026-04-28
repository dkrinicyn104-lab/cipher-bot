"""
🔐 ШИФР ULTRA PRO — Telegram Bot
Максимальная версия
"""

import base64
import hashlib
import logging
import os
import re
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
logging.basicConfig(level=logging.INFO)

# ╔══════════════════════════════════════════╗
#   ШИФРЫ
# ╚══════════════════════════════════════════╝

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
        pad = text.strip()
        pad += '=' * (4 - len(pad) % 4)
        r = base64.b64decode(pad).decode('utf-8')
        return r if r.isprintable() else None
    except:
        return None

def base32_encode(text):
    return base64.b32encode(text.encode('utf-8')).decode()

def base32_decode(text):
    try:
        pad = text.strip().upper()
        pad += '=' * (8 - len(pad) % 8) if len(pad) % 8 else ''
        r = base64.b32decode(pad).decode('utf-8')
        return r if r.isprintable() else None
    except:
        return None

MORSE_MAP = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
    'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
    'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.','.'  :'.-.-.-',','  :'--..--','?':'..--..',' ':'/'
}
MORSE_REV = {v: k for k, v in MORSE_MAP.items() if k != ' '}

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
    r = ' '.join(w for w in words if w)
    return r if r and '?' not in r else None

def atbash(text):
    result = []
    for ch in text:
        if ch.isalpha() and ch.isascii():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr(base + 25 - (ord(ch) - base)))
        else:
            result.append(ch)
    return ''.join(result)

def rot13(text):
    return text.translate(str.maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
        'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
    ))

def rot47(text):
    return ''.join(chr(33 + (ord(c) - 33 + 47) % 94) if 33 <= ord(c) <= 126 else c for c in text)

def hex_encode(text):
    return ' '.join(f'{b:02x}' for b in text.encode('utf-8'))

def hex_decode(text):
    try:
        r = bytes.fromhex(text.replace(' ', '').replace('\n', '')).decode('utf-8')
        return r if r.isprintable() else None
    except:
        return None

def binary_encode(text):
    return ' '.join(f'{b:08b}' for b in text.encode('utf-8'))

def binary_decode(text):
    try:
        parts = text.strip().split()
        if not all(set(p) <= {'0','1'} and len(p) == 8 for p in parts):
            return None
        r = bytes([int(b, 2) for b in parts]).decode('utf-8')
        return r if r.isprintable() else None
    except:
        return None

def octal_encode(text):
    return ' '.join(f'{b:03o}' for b in text.encode('utf-8'))

def octal_decode(text):
    try:
        parts = text.strip().split()
        r = bytes([int(p, 8) for p in parts]).decode('utf-8')
        return r if r.isprintable() else None
    except:
        return None

def url_encode(text):
    result = []
    for b in text.encode('utf-8'):
        if chr(b).isalnum() or chr(b) in '-_.~':
            result.append(chr(b))
        else:
            result.append(f'%{b:02X}')
    return ''.join(result)

def url_decode(text):
    try:
        result = []
        i = 0
        t = text.strip()
        while i < len(t):
            if t[i] == '%' and i + 2 < len(t):
                result.append(int(t[i+1:i+3], 16))
                i += 3
            elif t[i] == '+':
                result.append(32)
                i += 1
            else:
                result.extend(t[i].encode('utf-8'))
                i += 1
        r = bytes(result).decode('utf-8')
        return r if r.isprintable() else None
    except:
        return None

def reverse_text(text):
    return text[::-1]

def zalgo_encode(text):
    """Зальго - добавляет случетные диакритики"""
    import random
    zalgo_chars = [chr(i) for i in range(0x0300, 0x036F)]
    result = []
    for ch in text:
        result.append(ch)
        n = random.randint(1, 4)
        for _ in range(n):
            result.append(random.choice(zalgo_chars))
    return ''.join(result)

def pig_latin_encode(text):
    """Свиная латынь"""
    vowels = 'aeiouAEIOU'
    words = text.split()
    result = []
    for word in words:
        if not word.isalpha():
            result.append(word)
            continue
        if word[0] in vowels:
            result.append(word + 'yay')
        else:
            i = 0
            while i < len(word) and word[i] not in vowels:
                i += 1
            result.append(word[i:] + word[:i] + 'ay')
    return ' '.join(result)

def nato_encode(text):
    """NATO фонетический алфавит"""
    nato = {
        'A':'Alpha','B':'Bravo','C':'Charlie','D':'Delta','E':'Echo','F':'Foxtrot',
        'G':'Golf','H':'Hotel','I':'India','J':'Juliet','K':'Kilo','L':'Lima',
        'M':'Mike','N':'November','O':'Oscar','P':'Papa','Q':'Quebec','R':'Romeo',
        'S':'Sierra','T':'Tango','U':'Uniform','V':'Victor','W':'Whiskey',
        'X':'X-ray','Y':'Yankee','Z':'Zulu',
        '0':'Zero','1':'One','2':'Two','3':'Three','4':'Four',
        '5':'Five','6':'Six','7':'Seven','8':'Eight','9':'Nine'
    }
    result = []
    for ch in text.upper():
        if ch in nato:
            result.append(nato[ch])
        elif ch == ' ':
            result.append('|')
        else:
            result.append(ch)
    return ' '.join(result)

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def sha256_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def leet_encode(text):
    """Leet speak"""
    leet = {'a':'4','e':'3','i':'1','o':'0','s':'5','t':'7','b':'8','g':'9','l':'1'}
    return ''.join(leet.get(c.lower(), c) for c in text)

def mirror_encode(text):
    """Зеркальный текст (перевёрнутые символы)"""
    mirror = {'a':'ɐ','b':'q','c':'ɔ','d':'p','e':'ǝ','f':'ɟ','g':'ƃ','h':'ɥ',
              'i':'ᴉ','j':'ɾ','k':'ʞ','l':'l','m':'ɯ','n':'u','o':'o','p':'d',
              'q':'b','r':'ɹ','s':'s','t':'ʇ','u':'n','v':'ʌ','w':'ʍ','x':'x',
              'y':'ʎ','z':'z','A':'∀','B':'ᗺ','C':'Ɔ','D':'ᗡ','E':'Ǝ','F':'Ⅎ',
              'G':'פ','H':'H','I':'I','J':'ſ','K':'ʞ','L':'˥','M':'W','N':'N',
              'O':'O','P':'Ԁ','Q':'Q','R':'ᴚ','S':'S','T':'┴','U':'∩','V':'Λ',
              'W':'M','X':'X','Y':'⅄','Z':'Z','1':'Ɩ','2':'ᄅ','3':'Ɛ','4':'ᔭ',
              '5':'ϛ','6':'9','7':'ㄥ','8':'8','9':'6','0':'0',
              '?':'¿','!':'¡','.':'˙',',':'\'','\'':','}
    return ''.join(mirror.get(c, c) for c in reversed(text))

def apply_cipher(cipher, mode, text, key=''):
    enc = mode == 'encode'
    try:
        if cipher == 'caesar':
            shift = int(key) if key.lstrip('-').isdigit() else 13
            return caesar_encode(text, shift if enc else -shift)
        elif cipher == 'vigenere':
            return vigenere_encode(text, key or 'KEY') if enc else vigenere_decode(text, key or 'KEY')
        elif cipher == 'base64':
            return base64_encode(text) if enc else (base64_decode(text) or '⚠️ Неверный Base64')
        elif cipher == 'base32':
            return base32_encode(text) if enc else (base32_decode(text) or '⚠️ Неверный Base32')
        elif cipher == 'morse':
            return morse_encode(text) if enc else (morse_decode(text) or '⚠️ Неверный Морзе')
        elif cipher == 'atbash':
            return atbash(text)
        elif cipher == 'rot13':
            return rot13(text)
        elif cipher == 'rot47':
            return rot47(text)
        elif cipher == 'hex':
            return hex_encode(text) if enc else (hex_decode(text) or '⚠️ Неверный HEX')
        elif cipher == 'binary':
            return binary_encode(text) if enc else (binary_decode(text) or '⚠️ Неверный Binary')
        elif cipher == 'octal':
            return octal_encode(text) if enc else (octal_decode(text) or '⚠️ Неверный Octal')
        elif cipher == 'url':
            return url_encode(text) if enc else (url_decode(text) or '⚠️ Неверный URL')
        elif cipher == 'reverse':
            return reverse_text(text)
        elif cipher == 'leet':
            return leet_encode(text)
        elif cipher == 'mirror':
            return mirror_encode(text)
        elif cipher == 'pig':
            return pig_latin_encode(text) if enc else '⚠️ Pig Latin нельзя расшифровать автоматически'
        elif cipher == 'nato':
            return nato_encode(text) if enc else '⚠️ NATO — только шифрование'
        elif cipher == 'md5':
            return md5_hash(text) if enc else '⚠️ MD5 — необратимый хеш'
        elif cipher == 'sha256':
            return sha256_hash(text) if enc else '⚠️ SHA256 — необратимый хеш'
        elif cipher == 'zalgo':
            return zalgo_encode(text) if enc else '⚠️ Zalgo нельзя расшифровать'
    except Exception as e:
        return f'⚠️ Ошибка: {e}'
    return '⚠️ Неизвестный шифр'

# ╔══════════════════════════════════════════╗
#   АВТО-ОПРЕДЕЛЕНИЕ
# ╚══════════════════════════════════════════╝

def looks_like_text(s):
    if not s or not s.strip() or len(s.strip()) < 1:
        return False
    printable = sum(1 for c in s if c.isprintable())
    return printable / len(s) > 0.85

def is_hex_string(text):
    clean = text.replace(' ', '').replace('\n', '').lower()
    if len(clean) < 2 or len(clean) % 2 != 0:
        return False
    return all(c in '0123456789abcdef' for c in clean)

def is_binary_string(text):
    parts = text.strip().split()
    return len(parts) >= 1 and all(len(p) == 8 and set(p) <= {'0','1'} for p in parts)

def is_base64_string(text):
    t = text.strip().rstrip('=')
    return bool(re.match(r'^[A-Za-z0-9+/]+$', t)) and len(t) >= 4

def is_base32_string(text):
    t = text.strip().rstrip('=').upper()
    return bool(re.match(r'^[A-Z2-7]+$', t)) and len(t) >= 4

def is_morse_string(text):
    return all(c in '.-/ \t' for c in text.strip()) and ('.' in text or '-' in text)

def is_octal_string(text):
    parts = text.strip().split()
    return len(parts) >= 2 and all(re.match(r'^[0-7]{2,3}$', p) for p in parts)

def is_url_encoded(text):
    return '%' in text and bool(re.search(r'%[0-9A-Fa-f]{2}', text))

def auto_detect(text):
    results = []
    t = text.strip()

    if is_hex_string(t):
        r = hex_decode(t)
        if r and looks_like_text(r):
            results.append(('🟩 HEX', r))

    if is_binary_string(t):
        r = binary_decode(t)
        if r and looks_like_text(r):
            results.append(('💻 Binary', r))

    if is_octal_string(t):
        r = octal_decode(t)
        if r and looks_like_text(r):
            results.append(('🔢 Octal', r))

    if is_morse_string(t):
        r = morse_decode(t)
        if r and looks_like_text(r):
            results.append(('📡 Морзе', r))

    if is_base64_string(t):
        r = base64_decode(t)
        if r and looks_like_text(r):
            results.append(('📦 Base64', r))

    if is_base32_string(t):
        r = base32_decode(t)
        if r and looks_like_text(r):
            results.append(('📫 Base32', r))

    if is_url_encoded(t):
        r = url_decode(t)
        if r and looks_like_text(r):
            results.append(('🔗 URL', r))

    r = rot13(t)
    if r != t and looks_like_text(r):
        results.append(('🔄 ROT13', r))

    r = rot47(t)
    if r != t and looks_like_text(r) and r != t:
        results.append(('⚙️ ROT47', r))

    if any(c.isalpha() and c.isascii() for c in t):
        r = atbash(t)
        if r != t and looks_like_text(r):
            results.append(('🔁 Атбаш', r))

    if any(c.isalpha() and c.isascii() for c in t):
        for shift in range(1, 26):
            r = caesar_encode(t, -shift)
            if r != t and looks_like_text(r) and any(c.isalpha() for c in r):
                results.append((f'🔤 Цезарь сдвиг {shift}', r))
                if len(results) >= 6:
                    break

    r = reverse_text(t)
    if r != t:
        results.append(('↩️ Реверс', r))

    return results[:8]

# ╔══════════════════════════════════════════╗
#   ДАННЫЕ
# ╚══════════════════════════════════════════╝

user_data: dict = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {
            'cipher': 'base64', 'key': '',
            'auto_mode': False, 'history': [],
            'favorites': []
        }
    return user_data[uid]

# Группы шифров
CIPHER_GROUPS = {
    '🌍 Любой язык': [
        ('base64',  '📦 Base64'),
        ('base32',  '📫 Base32'),
        ('hex',     '🟩 HEX'),
        ('binary',  '💻 Binary'),
        ('octal',   '🔢 Octal'),
        ('url',     '🔗 URL'),
        ('reverse', '↩️ Реверс'),
    ],
    '🔡 Латиница': [
        ('caesar',  '🔤 Цезарь'),
        ('vigenere','🔑 Виженер'),
        ('morse',   '📡 Морзе'),
        ('atbash',  '🔁 Атбаш'),
        ('rot13',   '🔄 ROT13'),
        ('rot47',   '⚙️ ROT47'),
        ('pig',     '🐷 Pig Latin'),
        ('nato',    '🪖 NATO'),
        ('leet',    '👾 Leet'),
        ('mirror',  '🪞 Зеркало'),
    ],
    '🔒 Хеши': [
        ('md5',     '🔐 MD5'),
        ('sha256',  '🛡 SHA-256'),
    ],
    '🎨 Арт': [
        ('zalgo',   '👁 Zalgo'),
    ],
}

CIPHER_INFO = {
    'base64':  ('📦', 'Base64',   'Кодирует любой текст. Работает с русским.', True),
    'base32':  ('📫', 'Base32',   'Кодирование в алфавит A-Z и 2-7.', True),
    'hex':     ('🟩', 'HEX',      '16-ричный код. Работает с русским.', True),
    'binary':  ('💻', 'Binary',   '8-битный двоичный код. Работает с русским.', True),
    'octal':   ('🔢', 'Octal',    '8-ричный код байтов.', True),
    'url':     ('🔗', 'URL',      'URL-кодирование (%XX формат).', True),
    'reverse': ('↩️', 'Реверс',   'Переворачивает текст задом наперёд.', True),
    'caesar':  ('🔤', 'Цезарь',   'Сдвиг букв на N позиций.', True),
    'vigenere':('🔑', 'Виженер',  'Шифр с ключевым словом.', True),
    'morse':   ('📡', 'Морзе',    'Точки и тире.', True),
    'atbash':  ('🔁', 'Атбаш',    'Зеркальный алфавит A↔Z.', True),
    'rot13':   ('🔄', 'ROT13',    'Сдвиг на 13. Симметричный.', True),
    'rot47':   ('⚙️', 'ROT47',   'Сдвиг ASCII на 47. Симметричный.', True),
    'pig':     ('🐷', 'Pig Latin','Игровой язык на основе английского.', False),
    'nato':    ('🪖', 'NATO',     'Военный фонетический алфавит.', False),
    'leet':    ('👾', 'Leet',     'Замена букв на цифры (a→4, e→3...).', False),
    'mirror':  ('🪞', 'Зеркало',  'Переворачивает и зеркалит текст.', False),
    'md5':     ('🔐', 'MD5',      'Необратимый хеш. Нельзя расшифровать.', False),
    'sha256':  ('🛡', 'SHA-256',  'Криптографический хеш. Нельзя расшифровать.', False),
    'zalgo':   ('👁', 'Zalgo',    'Добавляет жуткие символы поверх текста.', False),
}

D  = "━━━━━━━━━━━━━━━━━━━━"
D2 = "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄"

def clabel(cid):
    i = CIPHER_INFO.get(cid, ('?','?','',True))
    return f"{i[0]} {i[1]}"

# ╔══════════════════════════════════════════╗
#   КЛАВИАТУРЫ
# ╚══════════════════════════════════════════╝

def main_keyboard(auto=False):
    auto_btn = "🔍 Авто: ВКЛ 🟢" if auto else "🔍 Авто: ВЫКЛ 🔴"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Шифр", callback_data='choose_cipher'),
            InlineKeyboardButton(auto_btn, callback_data='toggle_auto'),
        ],
        [
            InlineKeyboardButton("📜 История", callback_data='history'),
            InlineKeyboardButton("ℹ️ Инфо", callback_data='cipher_info'),
            InlineKeyboardButton("❓ Помощь", callback_data='help_btn'),
        ],
        [
            InlineKeyboardButton("🏠 В начало", callback_data='restart'),
            InlineKeyboardButton("🗑 Полный сброс", callback_data='reset_all'),
        ],
    ])

def group_keyboard():
    kb = []
    for group_name in CIPHER_GROUPS:
        kb.append([InlineKeyboardButton(group_name, callback_data=f'group_{group_name[:10]}')])
    kb.append([InlineKeyboardButton("◀️ Назад", callback_data='back_main')])
    return InlineKeyboardMarkup(kb)

def cipher_list_keyboard(group_name):
    ciphers = CIPHER_GROUPS.get(group_name, [])
    kb = []
    row = []
    for cid, name in ciphers:
        row.append(InlineKeyboardButton(name, callback_data=f'set_{cid}'))
        if len(row) == 2:
            kb.append(row); row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("◀️ К группам", callback_data='choose_cipher')])
    return InlineKeyboardMarkup(kb)

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data='back_main')]])

# ╔══════════════════════════════════════════╗
#   ХЕНДЛЕРЫ
# ╚══════════════════════════════════════════╝

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name or "друг"
    st = get_user(uid)
    cid = st['cipher']
    info = CIPHER_INFO[cid]
    total_ciphers = sum(len(v) for v in CIPHER_GROUPS.values())

    welcome = (
        f"👋 Привет, *{name}*!\n\n"
        f"Я — *ШИФР* 🔐\n"
        f"Твой личный бот-шифратор.\n\n"
        f"Умею шифровать и расшифровывать\n"
        f"текст *{total_ciphers} разными способами* — от\n"
        f"классики до продвинутых алгоритмов.\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📦 *Base64, HEX, Binary* — любой язык\n"
        f"🔤 *Цезарь, Виженер* — классика\n"
        f"📡 *Морзе, NATO* — легенды\n"
        f"🔍 *Авто-режим* — сам разгадаю шифр\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"Активный шифр: *{info[0]} {info[1]}*\n\n"
        f"✏️ *Напиши что-нибудь — попробуй!*"
    )

    await update.message.reply_text(
        welcome, parse_mode='Markdown',
        reply_markup=main_keyboard(st.get('auto_mode', False))
    )

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)
    text = update.message.text
    cid = st['cipher']
    key = st.get('key', '')
    info = CIPHER_INFO[cid]
    auto = st.get('auto_mode', False)

    # Авто-режим
    if auto:
        results = auto_detect(text)
        if results:
            lines = [
                f"🔍 *Авто-определение*\n{D}\n\n"
                f"📝 *Исходный:*\n`{text[:100]}{'...' if len(text)>100 else ''}`\n\n"
                f"*Найдено {len(results)} вариант(ов):*\n{D2}\n"
            ]
            for cname, result in results:
                lines.append(f"*{cname}*\n`{result[:150]}{'...' if len(result)>150 else ''}`\n")
            lines.append(f"{D}\n💡 _Нажми_ 🔍 _чтобы выключить авто_")
            await update.message.reply_text(
                '\n'.join(lines), parse_mode='Markdown',
                reply_markup=main_keyboard(True)
            )
        else:
            await update.message.reply_text(
                f"🔍 *Авто-определение*\n{D}\n\n"
                f"📝 Текст: `{text[:80]}`\n\n"
                f"❌ *Шифр не распознан*\n\n"
                f"Попробуй выбрать шифр вручную:\n"
                f"📦 Base64, 🟩 HEX, 💻 Binary...",
                parse_mode='Markdown',
                reply_markup=main_keyboard(True)
            )
        return

    # Обычный режим
    encoded = apply_cipher(cid, 'encode', text, key)
    decoded = apply_cipher(cid, 'decode', text, key)
    decode_ok = decoded and not str(decoded).startswith('⚠️')

    # История
    if 'history' not in st:
        st['history'] = []
    st['history'].append({'text': text[:50], 'encoded': encoded[:50], 'cipher': cid})
    if len(st['history']) > 20:
        st['history'] = st['history'][-20:]

    key_line = ''
    if cid == 'caesar':
        key_line = f"  🔑 Сдвиг: `{key or '13'}`\n"
    elif cid == 'vigenere':
        key_line = f"  🔑 Ключ: `{key or 'KEY'}`\n"

    decode_line = f"`{decoded}`" if decode_ok else f"_Отправь зашифрованный текст_"

    msg = (
        f"*{info[0]} {info[1]}*\n"
        f"{key_line}"
        f"{D}\n\n"
        f"📝 *Исходный:*\n`{text}`\n\n"
        f"🔒 *Зашифрованный:*\n`{encoded}`\n\n"
        f"🔓 *Расшифрованный:*\n{decode_line}\n\n"
        f"{D}\n"
        f"💡 _Включи_ 🔍 _Авто для автоопределения_"
    )

    await update.message.reply_text(
        msg, parse_mode='Markdown',
        reply_markup=main_keyboard(False)
    )

async def button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    st = get_user(uid)
    data = query.data

    if data == 'choose_cipher':
        total = sum(len(v) for v in CIPHER_GROUPS.values())
        await query.edit_message_text(
            f"🔄 *Выбери группу шифров*\n{D}\n\n"
            f"Всего доступно: *{total} шифров*\n\n"
            f"🌍 Любой язык — работают с русским\n"
            f"🔡 Латиница — только латинские буквы\n"
            f"🔒 Хеши — необратимые\n"
            f"🎨 Арт — визуальные эффекты",
            parse_mode='Markdown',
            reply_markup=group_keyboard()
        )

    elif data.startswith('group_'):
        prefix = data[6:]
        group_name = next((g for g in CIPHER_GROUPS if g[:10] == prefix), None)
        if not group_name:
            return
        ciphers = CIPHER_GROUPS[group_name]
        lines = [f"*{group_name}*\n{D}\n"]
        for cid, name in ciphers:
            info = CIPHER_INFO[cid]
            reversible = "↔️" if info[3] else "→"
            lines.append(f"{name} {reversible} _{info[2][:40]}_")
        await query.edit_message_text(
            '\n'.join(lines),
            parse_mode='Markdown',
            reply_markup=cipher_list_keyboard(group_name)
        )

    elif data.startswith('set_'):
        cid = data[4:]
        st['cipher'] = cid
        info = CIPHER_INFO[cid]
        reversible = "↔️ Двусторонний" if info[3] else "→ Только шифрование"

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
            f"_{info[2]}_\n\n"
            f"{reversible}"
            f"{key_tip}\n\n"
            f"{D}\n✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(st.get('auto_mode', False))
        )

    elif data == 'toggle_auto':
        st['auto_mode'] = not st.get('auto_mode', False)
        status = "🟢 ВКЛЮЧЁН" if st['auto_mode'] else "🔴 ВЫКЛЮЧЕН"
        tip = ("Теперь я автоматически определяю шифр!\nОтправь зашифрованный текст."
               if st['auto_mode'] else
               "Обычный режим. Выбери шифр и пиши текст.")
        await query.edit_message_text(
            f"🔍 *Авто-режим: {status}*\n{D}\n\n{tip}\n\n"
            f"Текущий шифр: *{clabel(st['cipher'])}*\n\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(st['auto_mode'])
        )

    elif data == 'cipher_info':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        key_info = ''
        if cid == 'caesar':
            key_info = f"\n🔑 Сдвиг: *{st.get('key','13')}*  →  `/key 7`"
        elif cid == 'vigenere':
            key_info = f"\n🔑 Ключ: *{st.get('key','KEY')}*  →  `/key СЛОВО`"

        total = sum(len(v) for v in CIPHER_GROUPS.values())
        await query.edit_message_text(
            f"*{info[0]} {info[1]}*\n{D}\n\n"
            f"📖 _{info[2]}_\n"
            f"{'↔️ Двусторонний' if info[3] else '→ Только шифрование'}"
            f"{key_info}\n\n"
            f"{D}\n"
            f"🔍 Авто-режим: {'🟢 Вкл' if st.get('auto_mode') else '🔴 Выкл'}\n"
            f"📊 История: *{len(st.get('history',[]))}* записей\n"
            f"⚡ Всего шифров: *{total}*",
            parse_mode='Markdown',
            reply_markup=back_keyboard()
        )

    elif data == 'history':
        history = st.get('history', [])
        if not history:
            await query.edit_message_text(
                f"📜 *История пуста*\n{D}\n\nОтправь текст чтобы начать!",
                parse_mode='Markdown', reply_markup=back_keyboard()
            )
            return
        lines = [f"📜 *История ({len(history)} записей)*\n{D}\n"]
        for h in reversed(history[-8:]):
            lines.append(f"🔒 {clabel(h['cipher'])}")
            lines.append(f"  `{h['text'][:25]}{'…' if len(h['text'])>25 else ''}`")
            lines.append(f"  → `{h['encoded'][:25]}{'…' if len(h['encoded'])>25 else ''}`\n")
        await query.edit_message_text(
            '\n'.join(lines), parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Очистить историю", callback_data='clear_history')],
                [InlineKeyboardButton("◀️ Назад", callback_data='back_main')],
            ])
        )

    elif data == 'clear_history':
        st['history'] = []
        await query.edit_message_text(
            f"🗑 *История очищена!*\n{D}\n\n✏️ Напиши текст:",
            parse_mode='Markdown', reply_markup=main_keyboard(st.get('auto_mode', False))
        )

    elif data == 'restart':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        auto = st.get('auto_mode', False)
        name = query.from_user.first_name or "друг"
        total_ciphers = sum(len(v) for v in CIPHER_GROUPS.values())
        await query.edit_message_text(
            f"🔐 *ШИФР ULTRA PRO*\n"
            f"{D}\n\n"
            f"Привет, *{name}*! 👋\n\n"
            f"⚡ *{total_ciphers} шифров* на выбор\n"
            f"🔍 *Авто-определение* любого шифра\n"
            f"📜 *История* последних шифрований\n"
            f"🌍 Поддержка *русского языка*\n\n"
            f"{D}\n"
            f"Текущий шифр: *{info[0]} {info[1]}*\n"
            f"{D}\n\n"
            f"✏️ *Просто напиши любой текст!*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(auto)
        )

    elif data == 'reset_all':
        await query.edit_message_text(
            f"⚠️ *Подтверди сброс*\n{D}\n\n"
            f"Это удалит:\n"
            f"• Всю историю ({len(st.get('history',[]))} записей)\n"
            f"• Настройки ключей\n"
            f"• Авто-режим\n\n"
            f"Шифр вернётся к Base64.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Да, сбросить", callback_data='confirm_reset')],
                [InlineKeyboardButton("❌ Отмена", callback_data='back_main')],
            ])
        )

    elif data == 'confirm_reset':
        user_data[uid] = {'cipher': 'base64', 'key': '', 'auto_mode': False, 'history': [], 'favorites': []}
        st = user_data[uid]
        await query.edit_message_text(
            f"✅ *Всё сброшено!*\n{D}\n\n"
            f"Шифр: *📦 Base64*\n"
            f"История: очищена\n"
            f"Авто-режим: выключен\n\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(False)
        )

    elif data == 'help_btn':
        await query.edit_message_text(
            f"❓ *СПРАВКА*\n{D}\n\n"
            f"*Как пользоваться:*\n"
            f"1. Напиши любой текст\n"
            f"2. Получи зашифрованный результат\n"
            f"3. Поделись с другом!\n\n"
            f"*Для расшифровки:*\n"
            f"Включи 🔍 *Авто* и отправь шифр\n\n"
            f"{D}\n"
            f"*Кнопки:*\n"
            f"🔄 — выбрать шифр\n"
            f"🔍 — авто-определение шифра\n"
            f"📜 — история последних операций\n"
            f"ℹ️ — инфо о текущем шифре\n\n"
            f"{D}\n"
            f"*Команды:*\n"
            f"`/start` — главное меню\n"
            f"`/key значение` — установить ключ\n"
            f"`/all` — список всех шифров\n"
            f"`/help` — эта справка",
            parse_mode='Markdown',
            reply_markup=back_keyboard()
        )

    elif data == 'back_main':
        cid = st['cipher']
        info = CIPHER_INFO[cid]
        auto = st.get('auto_mode', False)
        auto_line = "\n🔍 *Авто-режим активен!*" if auto else ""
        await query.edit_message_text(
            f"🔐 *ШИФР ULTRA PRO*{auto_line}\n{D}\n\n"
            f"Шифр: *{info[0]} {info[1]}*\n\n"
            f"✏️ *Напиши текст:*",
            parse_mode='Markdown',
            reply_markup=main_keyboard(auto)
        )

async def set_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = get_user(uid)
    args = ctx.args
    if not args:
        await update.message.reply_text(
            f"💡 *Команда:* `/key значение`\n\n"
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
        f"Ключ: `{st['key']}`\n\n✏️ Напиши текст:",
        parse_mode='Markdown',
        reply_markup=main_keyboard(st.get('auto_mode', False))
    )

async def all_ciphers(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total = sum(len(v) for v in CIPHER_GROUPS.values())
    lines = [f"⚡ *Все {total} шифров:*\n{D}\n"]
    for group, ciphers in CIPHER_GROUPS.items():
        lines.append(f"\n*{group}*")
        for cid, name in ciphers:
            info = CIPHER_INFO[cid]
            lines.append(f"  {name} — _{info[2][:35]}_")
    await update.message.reply_text(
        '\n'.join(lines), parse_mode='Markdown',
        reply_markup=main_keyboard(get_user(update.effective_user.id).get('auto_mode', False))
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"❓ *СПРАВКА — ШИФР ULTRA PRO*\n{D}\n\n"
        f"Напиши любой текст — и получи зашифрованный результат.\n\n"
        f"Для расшифровки неизвестного шифра включи 🔍 *Авто*.\n\n"
        f"{D}\n"
        f"*Команды:*\n"
        f"`/start` — главное меню\n"
        f"`/key значение` — установить ключ\n"
        f"`/all` — список всех шифров\n"
        f"`/help` — справка",
        parse_mode='Markdown',
        reply_markup=main_keyboard(get_user(uid).get('auto_mode', False))
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", set_key))
    app.add_handler(CommandHandler("all", all_ciphers))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("🔐 ШИФР ULTRA PRO запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
