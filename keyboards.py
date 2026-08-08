from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

BACK_BTN = "⬅️ Ortga"


def _reply(*rows: list[str]) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for row in rows:
        for text in row:
            builder.button(text=text)
    builder.button(text=BACK_BTN)
    builder.adjust(*[len(r) for r in rows], 1)
    return builder.as_markup(resize_keyboard=True)


# ============================================================
# Oddiy foydalanuvchi menyusi
# ============================================================

def user_main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Testni ishlash")
    builder.button(text="📊 Umumiy natijalar")
    builder.button(text="🏆 Sertifikatlarim")
    builder.button(text="✉️ Adminga yozish")
    builder.adjust(3, 1)
    return builder.as_markup(resize_keyboard=True)


CHECK_ATT = "📋 Attestatsiya javoblarini tekshirish"
CHECK_MS = "🎓 Milliy sertifikat javoblarini tekshirish"


def test_type_choice_kb() -> ReplyKeyboardMarkup:
    return _reply([CHECK_MS], [CHECK_ATT])


def active_papers_kb(papers: list[dict], prefix: str) -> InlineKeyboardMarkup:
    """Testlar ro'yxati DINAMIK va nomlari takrorlanishi mumkin — ID xavfsizligi
    uchun bu ATAYLAB inline (callback_data bilan) qoldirilgan."""
    builder = InlineKeyboardBuilder()
    for p in papers:
        builder.button(text=f"📄 {p['title']}", callback_data=f"{prefix}:{p['id']}")
    builder.adjust(1)
    return builder.as_markup()


def abcd_kb() -> ReplyKeyboardMarkup:
    """A/B/C/D — ham admin javoblar kalitini kiritganda, ham foydalanuvchi
    javob yuborganda ishlatiladigan umumiy tugma (savol matni bot ichida
    saqlanmaydi, shuning uchun variant matni ham yo'q)."""
    return _reply(["A", "B", "C", "D"])


# ============================================================
# Admin menyusi — PASTKI DOIMIY MENYU
# ============================================================

ADMIN_BTN_NEW_TEST = "➕ Yangi test yaratish"
ADMIN_BTN_TEST_LIST = "🗂 Testlar ro'yxati"
ADMIN_BTN_RESULTS = "📊 Natijalar"
ADMIN_BTN_SEND_CERTS = "🎗 Sertifikat yuborish"
ADMIN_BTN_BROADCAST = "📢 Hammaga xabar"
ADMIN_BTN_ASSIGN_ROLE = "⚙️ Admin tayinlash"
ADMIN_BTN_CHANNELS = "🔒 Majburiy kanallar"
ADMIN_BTN_EXIT = "🚪 Admin paneldan chiqish"


def admin_main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=ADMIN_BTN_NEW_TEST)
    builder.button(text=ADMIN_BTN_TEST_LIST)
    builder.button(text=ADMIN_BTN_RESULTS)
    builder.button(text=ADMIN_BTN_SEND_CERTS)
    builder.button(text=ADMIN_BTN_BROADCAST)
    builder.button(text=ADMIN_BTN_ASSIGN_ROLE)
    builder.button(text=ADMIN_BTN_CHANNELS)
    builder.button(text=ADMIN_BTN_EXIT)
    builder.adjust(2, 2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


# --- Yangi test (javoblar kaliti) yaratish ---

ENTER_ATT = "📋 Attestatsiya javoblarini kiritish"
ENTER_MS = "🎓 Milliy sertifikat javoblarini kiritish"


def new_test_type_kb() -> ReplyKeyboardMarkup:
    return _reply([ENTER_MS], [ENTER_ATT])


QCOUNT_OPTIONS = ["10", "15", "20", "25", "30", "35", "40", "45", "50"]


def question_count_kb() -> ReplyKeyboardMarkup:
    return _reply(QCOUNT_OPTIONS[:5], QCOUNT_OPTIONS[5:])


# --- Milliy sertifikat: variantli va yopiq savollar sonini alohida tanlash ---

VARIANTLI_COUNT_OPTIONS = ["20", "25", "30", "35", "40", "45", "50"]
YOPIQ_COUNT_OPTIONS = ["10", "15", "20", "25", "30"]


def variantli_count_kb() -> ReplyKeyboardMarkup:
    return _reply(VARIANTLI_COUNT_OPTIONS[:4], VARIANTLI_COUNT_OPTIONS[4:])


def yopiq_count_kb() -> ReplyKeyboardMarkup:
    return _reply(YOPIQ_COUNT_OPTIONS)


# --- Test boshlanish vaqti: hozir yoki oldindan rejalashtirish ---

START_NOW = "▶️ Hozir boshlansin"
START_SCHEDULE = "🗓 Boshlanish vaqtini belgilayman"


def start_choice_kb() -> ReplyKeyboardMarkup:
    return _reply([START_NOW], [START_SCHEDULE])


DEADLINE_OPTIONS = [("1 soat", 1), ("3 soat", 3), ("6 soat", 6), ("12 soat", 12),
                     ("24 soat", 24), ("48 soat", 48), ("72 soat", 72)]


def deadline_preset_kb() -> ReplyKeyboardMarkup:
    labels = [label for label, _ in DEADLINE_OPTIONS]
    return _reply(labels[:3], labels[3:6], labels[6:])


TLIST_MS = "🎓 Milliy sertifikat testlari"
TLIST_ATT = "📋 Attestatsiya testlari"


def test_list_type_kb() -> ReplyKeyboardMarkup:
    return _reply([TLIST_MS], [TLIST_ATT])


STATUS_ACTIVE = "🟢 Faol testlar"
STATUS_CLOSED = "🔴 Yopilgan testlar (qayta faollashtirish)"


def paper_status_choice_kb() -> ReplyKeyboardMarkup:
    return _reply([STATUS_ACTIVE], [STATUS_CLOSED])


CONFIRM_YES = "✅ Ha"
CONFIRM_NO = "❌ Yo'q"


def confirm_reply_kb() -> ReplyKeyboardMarkup:
    return _reply([CONFIRM_YES, CONFIRM_NO])


# ============================================================
# ID'ga bog'liq dinamik ro'yxatlar — ATAYLAB inline qoldirildi
# ============================================================

def _with_back(builder: InlineKeyboardBuilder, *row_sizes: int) -> InlineKeyboardMarkup:
    builder.button(text="⬅️ Ortga", callback_data="adm:back")
    if row_sizes:
        builder.adjust(*row_sizes, 1)
    else:
        builder.adjust(1)
    return builder.as_markup()


def channels_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Kanal qo'shish", callback_data="ch:add")
    builder.button(text="➖ Kanalni o'chirish", callback_data="ch:remove_menu")
    return _with_back(builder, 1, 1)


def channels_remove_kb(channels: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(text=f"❌ {ch['title']}", callback_data=f"ch:remove:{ch['id']}")
    return _with_back(builder, *([1] * len(channels)))


def closed_papers_kb(papers: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in papers:
        builder.button(text=f"🔄 {p['title']}", callback_data=f"reactivate:{p['id']}")
        builder.button(text=f"🗑 O'chirish", callback_data=f"delpaper:{p['id']}")
    return _with_back(builder, *([2] * len(papers)))


def active_papers_delete_kb(papers: list[dict]) -> InlineKeyboardMarkup:
    """Faol testlar ro'yxatida har biriga o'chirish tugmasi bilan."""
    builder = InlineKeyboardBuilder()
    for p in papers:
        builder.button(text=f"🗑 {p['title']}", callback_data=f"delpaper:{p['id']}")
    return _with_back(builder, *([1] * len(papers)))


def confirm_delete_paper_kb(paper_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, butunlay o'chirish", callback_data=f"delpaper_yes:{paper_id}")
    builder.button(text="❌ Yo'q, bekor qilish", callback_data="delpaper_no")
    builder.adjust(1)
    return builder.as_markup()


def user_list_kb(users: list[dict], clickable: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, u in enumerate(users, start=1):
        label = f"{i}. {u['telegram_id']}"
        if clickable:
            builder.button(text=label, callback_data=f"profile:{u['id']}")
        else:
            builder.button(text=label, callback_data="noop")
    # Raqamlangan ID'lar tarki tarzda, 3 tadan bir qatorda joylashadi
    row_sizes = [3] * (len(users) // 3) + ([len(users) % 3] if len(users) % 3 else [])
    return _with_back(builder, *row_sizes)


def back_to_admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Ortga", callback_data="adm:back")
    return builder.as_markup()
