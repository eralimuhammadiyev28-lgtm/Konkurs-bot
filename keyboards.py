from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def join_channels_kb(channels):
    """channels: db.get_mandatory_channels() natijasi (Row obyektlar ro'yxati)."""
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


def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Konkursni boshlash", callback_data="admin_start_contest")],
        [InlineKeyboardButton(text="🏆 G'oliblarni ko'rish", callback_data="admin_winners")],
        [InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📣 Hammaga xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔒 Majburiy kanallar", callback_data="admin_channels")],
        [InlineKeyboardButton(text="⚙️ Admin qo'shish", callback_data="admin_add_admin")],
    ])


def channels_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="ch_add")],
        [InlineKeyboardButton(text="➖ Kanalni o'chirish", callback_data="ch_remove_menu")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_back")],
    ])


def channels_remove_kb(channels):
    rows = []
    for ch in channels:
        rows.append([InlineKeyboardButton(text=f"❌ {ch['title']}", callback_data=f"ch_remove:{ch['id']}")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin_channels")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
