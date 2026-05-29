from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import CHANNEL_LINK

def join_channel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ A'zo bo'ldim, tekshir", callback_data="check_join")]
    ])

def main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔗 Mening linkım"), KeyboardButton(text="📊 Statistikam")],
        [KeyboardButton(text="🏆 Top 10 reyting")]
    ], resize_keyboard=True)

def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Konkursni boshlash", callback_data="admin_start_contest")],
        [InlineKeyboardButton(text="⏹ Konkursni to'xtatish", callback_data="admin_stop_contest")],
        [InlineKeyboardButton(text="🏆 G'oliblarni ko'rish", callback_data="admin_winners")],
        [InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📣 Hammaga xabar", callback_data="admin_broadcast")]
    ])
