from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

BACK_BTN = "⬅️ Ortga"


def join_channels_kb(channels):
    rows = []
    for ch in channels:
        link = ch["invite_link"] or (f"https://t.me/{ch['username']}" if ch["username"] else None)
        if link:
            rows.append([InlineKeyboardButton(text=f"📢 {ch['title']}", url=link)])
    rows.append([InlineKeyboardButton(text="✅ A'zo bo'ldim, tekshir", callback_data="check_join")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔗 Mening linkım"), KeyboardButton(text="📊 Statistikam")],
        [KeyboardButton(text="🏆 Top 10 reyting")],
        [KeyboardButton(text="📜 Shartlar"), KeyboardButton(text="🎁 Sovg'alar")],
    ], resize_keyboard=True)


ADMIN_BTN_START_CONTEST = "▶️ Konkursni boshlash"
ADMIN_BTN_WINNERS = "🏆 G'oliblarni ko'rish"
ADMIN_BTN_STATS = "📊 Umumiy statistika"
ADMIN_BTN_BROADCAST = "📣 Hammaga xabar"
ADMIN_BTN_CHANNELS = "🔒 Majburiy kanallar"
ADMIN_BTN_ADD_ADMIN = "⚙️ Admin qo'shish"
ADMIN_BTN_EXIT = "🚪 Admin paneldan chiqish"


def admin_main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=ADMIN_BTN_START_CONTEST)],
        [KeyboardButton(text=ADMIN_BTN_WINNERS), KeyboardButton(text=ADMIN_BTN_STATS)],
        [KeyboardButton(text=ADMIN_BTN_BROADCAST), KeyboardButton(text=ADMIN_BTN_CHANNELS)],
        [KeyboardButton(text=ADMIN_BTN_ADD_ADMIN)],
        [KeyboardButton(text=ADMIN_BTN_EXIT)],
    ], resize_keyboard=True)


CHANNELS_BTN_ADD = "➕ Kanal qo'shish"
CHANNELS_BTN_REMOVE = "➖ Kanalni o'chirish"


def channels_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=CHANNELS_BTN_ADD)],
        [KeyboardButton(text=CHANNELS_BTN_REMOVE)],
        [KeyboardButton(text=BACK_BTN)],
    ], resize_keyboard=True)


def channels_remove_kb(channels):
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(text=f"❌ {ch['title']}", callback_data=f"ch_remove:{ch['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
