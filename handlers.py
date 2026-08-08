import time
import html
from datetime import datetime, timezone, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import (
    join_channels_kb, main_menu_kb, admin_main_menu_kb, channels_menu_kb, channels_remove_kb,
    ADMIN_BTN_START_CONTEST, ADMIN_BTN_WINNERS, ADMIN_BTN_STATS, ADMIN_BTN_BROADCAST,
    ADMIN_BTN_CHANNELS, ADMIN_BTN_ADD_ADMIN, ADMIN_BTN_EXIT,
    CHANNELS_BTN_ADD, CHANNELS_BTN_REMOVE, BACK_BTN,
)
from config import ADMIN_IDS, BOT_USERNAME

router = Router()


class AdminState(StatesGroup):
    waiting_broadcast = State()
    waiting_start_time = State()
    waiting_end_time = State()
    waiting_terms = State()
    waiting_prizes = State()
    waiting_channel_username = State()
    waiting_new_admin_id = State()


# ============================================================
# Yordamchi funksiyalar
# ============================================================

async def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    return await db.is_admin_in_db(user_id)


async def get_unjoined_channels(bot: Bot, user_id: int):
    channels = await db.get_mandatory_channels()
    unjoined = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                unjoined.append(ch)
        except Exception:
            continue
    return unjoined


async def get_contest_status():
    contest = await db.get_contest()
    if not contest or not contest["is_active"]:
        return "not_configured", contest
    now = int(time.time())
    if contest["start_time"] and now < contest["start_time"]:
        return "not_started", contest
    if contest["end_time"] and now > contest["end_time"]:
        return "ended", contest
    return "active", contest


async def is_contest_active() -> bool:
    status, _ = await get_contest_status()
    return status == "active"


TASHKENT_TZ = timezone(timedelta(hours=5))


def _parse_dt_tashkent(text: str) -> datetime:
    """Admin O'zbekiston (Toshkent, UTC+5) vaqtida kiritadi deb ANIQ belgilaymiz —
    serverning (Railway, odatda UTC) o'z vaqt zonasiga ishonib qolmaymiz."""
    naive = datetime.strptime(text.strip(), "%d.%m.%Y %H:%M")
    return naive.replace(tzinfo=TASHKENT_TZ)


def _fmt_dt(ts: int) -> str:
    """Epoch vaqtni har doim O'zbekiston vaqtida ko'rsatish (kim qayerdan kirmasin)."""
    return datetime.fromtimestamp(ts, tz=TASHKENT_TZ).strftime("%d.%m.%Y %H:%M")


# ============================================================
# Universal "⬅️ Ortga"
# ============================================================

@router.message(F.text == BACK_BTN)
async def universal_back(message: Message, state: FSMContext):
    await state.clear()
    if await is_admin(message.from_user.id):
        await message.answer("🛠 Admin panel", reply_markup=admin_main_menu_kb())
    else:
        await message.answer("Bosh menyu:", reply_markup=main_menu_kb())


# ============================================================
# /start va kanalga a'zolik
# ============================================================

@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    user = await db.get_user(user_id)
    if not user:
        user = await db.create_user(user_id, username, full_name)

    status, contest = await get_contest_status()
    if status == "not_configured":
        await message.answer("⏳ Hozircha faol konkurs mavjud emas. Konkurs boshlanganda xabar beramiz!")
        return
    if status == "not_started":
        await message.answer(f"⏳ Konkurs hali boshlanmagan.\n🗓 Boshlanish vaqti: {_fmt_dt(contest['start_time'])}")
        return
    if status == "ended":
        await message.answer("🏁 Konkurs allaqachon yakunlangan. Natijalarni tez orada e'lon qilamiz!")
        return

    args = message.text.split()
    inviter_ref = args[1] if len(args) > 1 and args[1].startswith("ref_") else None
    ref_code = inviter_ref[4:] if inviter_ref else None

    unjoined = await get_unjoined_channels(bot, user_id)

    if unjoined:
        if ref_code:
            await state.update_data(pending_ref_code=ref_code)
        await message.answer(
            "👋 Salom! Konkursda ishtirok etish uchun avval quyidagi kanal(lar)ga a'zo bo'ling:",
            reply_markup=join_channels_kb(unjoined)
        )
        return

    await db.update_channel_join(user_id)

    if ref_code:
        inviter = await db.get_user_by_refcode(ref_code)
        if inviter and inviter["telegram_id"] != user_id:
            added = await db.add_referral(inviter["telegram_id"], user_id)
            if added:
                try:
                    await bot.send_message(
                        inviter["telegram_id"],
                        f"🎉 Yangi odam siz orqali qo'shildi! Jami: {inviter['invited_count'] + 1} ta"
                    )
                except Exception:
                    pass

    user = await db.get_user(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user['ref_code']}"

    await message.answer(
        f"✅ Xush kelibsiz, {full_name}!\n\n"
        f"🔗 Sizning referal linkingiz:\n{ref_link}\n\n"
        f"👥 Qo'shganlar: {user['invited_count']} ta\n\n"
        f"Bu linkni do'stlaringizga yuboring — ular orqali eng ko'p odam qo'shgan g'olib bo'ladi! 🏆",
        reply_markup=main_menu_kb()
    )


@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if not await is_contest_active():
        await callback.answer("⏳ Hozircha faol konkurs mavjud emas.", show_alert=True)
        return

    user_id = callback.from_user.id
    unjoined = await get_unjoined_channels(bot, user_id)

    if unjoined:
        await callback.answer("❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
        return

    await db.update_channel_join(user_id)

    data = await state.get_data()
    ref_code = data.get("pending_ref_code")
    if ref_code:
        inviter = await db.get_user_by_refcode(ref_code)
        if inviter and inviter["telegram_id"] != user_id:
            added = await db.add_referral(inviter["telegram_id"], user_id)
            if added:
                try:
                    await bot.send_message(
                        inviter["telegram_id"],
                        f"🎉 Yangi odam siz orqali qo'shildi! Jami: {inviter['invited_count'] + 1} ta"
                    )
                except Exception:
                    pass
        await state.clear()

    user = await db.get_user(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user['ref_code']}"

    await callback.message.edit_text(
        f"✅ Ajoyib! Siz kanal(lar)ga a'zo bo'ldingiz!\n\n"
        f"🔗 Sizning referal linkingiz:\n{ref_link}\n\n"
        f"👥 Qo'shganlar: {user['invited_count']} ta\n\n"
        f"Bu linkni ulashing va g'olib bo'ling! 🏆"
    )
    await callback.message.answer("Menyu:", reply_markup=main_menu_kb())
    await callback.answer()


# ============================================================
# Oddiy foydalanuvchi menyusi
# ============================================================

@router.message(F.text == "🔗 Mening linkım")
async def my_link_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing.")
        return
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user['ref_code']}"
    rank = await db.get_user_rank(message.from_user.id)
    await message.answer(
        f"🔗 Sizning shaxsiy linkingiz:\n{ref_link}\n\n"
        f"👥 Qo'shganlar soni: {user['invited_count']} ta\n"
        f"📊 Reytingdagi o'rningiz: {rank}-o'rin\n\n"
        f"Linkni do'stlarga yuboring! 🚀"
    )


@router.message(F.text == "📊 Statistikam")
async def my_stats_handler(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosing.")
        return
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user['ref_code']}"
    rank = await db.get_user_rank(message.from_user.id)
    await message.answer(
        f"📊 Sizning statistikangiz:\n\n"
        f"👤 Ism: {user['full_name']}\n"
        f"🔗 Link: {ref_link}\n"
        f"👥 Qo'shganlar: {user['invited_count']} ta\n"
        f"🏅 Reyting o'rni: {rank}-o'rin"
    )


@router.message(F.text == "🏆 Top 10 reyting")
async def top_handler(message: Message):
    top = await db.get_top_users(10)
    if not top:
        await message.answer("Hali hech kim ishtirok etmagan.")
        return

    text = "🏆 Top 10 ishtirokchilar:\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, u in enumerate(top):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = u["full_name"] or "Noma'lum"
        text += f"{medal} {name} — {u['invited_count']} ta\n"

    user = await db.get_user(message.from_user.id)
    if user:
        rank = await db.get_user_rank(message.from_user.id)
        text += f"\n📍 Sizning o'rningiz: {rank}-o'rin ({user['invited_count']} ta)"

    await message.answer(text)


@router.message(F.text == "📜 Shartlar")
async def terms_handler(message: Message):
    contest = await db.get_contest()
    if not contest or not contest["terms"]:
        await message.answer("📜 Konkurs shartlari hali belgilanmagan.")
        return
    text = f"📜 <b>Konkurs shartlari:</b>\n\n{contest['terms']}"
    if contest["start_time"] and contest["end_time"]:
        text += f"\n\n🗓 Muddat: {_fmt_dt(contest['start_time'])} — {_fmt_dt(contest['end_time'])}"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🎁 Sovg'alar")
async def prizes_handler(message: Message):
    contest = await db.get_contest()
    if not contest or not contest["prizes"]:
        await message.answer("🎁 Sovg'alar hali belgilanmagan.")
        return
    await message.answer(f"🎁 <b>Konkurs sovg'alari:</b>\n\n{contest['prizes']}", parse_mode="HTML")


# ============================================================
# Admin panel — PASTKI DOIMIY MENYU
# ============================================================

@router.message(Command("debug"))
async def debug_handler(message: Message):
    if not await is_admin(message.from_user.id):
        return
    contest = await db.get_contest()
    now = int(time.time())
    if not contest:
        await message.answer("🔍 DEBUG: bazada hech qanday konkurs yozuvi yo'q.")
        return
    start_diff = contest["start_time"] - now if contest["start_time"] else None
    end_diff = contest["end_time"] - now if contest["end_time"] else None
    await message.answer(
        f"🔍 <b>DEBUG</b>\n\n"
        f"ID: {contest['id']}\n"
        f"is_active: {contest['is_active']}\n"
        f"start_time (epoch): {contest['start_time']}\n"
        f"end_time (epoch): {contest['end_time']}\n"
        f"HOZIRGI vaqt (epoch): {now}\n\n"
        f"Boshlanishiga qoldi: {start_diff} soniya\n"
        f"Tugashiga qoldi: {end_diff} soniya\n\n"
        f"start_time (O'zbek vaqtida): {_fmt_dt(contest['start_time']) if contest['start_time'] else '-'}\n"
        f"end_time (O'zbek vaqtida): {_fmt_dt(contest['end_time']) if contest['end_time'] else '-'}\n"
        f"HOZIR (O'zbek vaqtida): {_fmt_dt(now)}",
        parse_mode="HTML"
    )


@router.message(Command("admin"))
async def admin_handler(message: Message):
    if not await is_admin(message.from_user.id):
        return
    status, contest = await get_contest_status()
    if status == "not_configured":
        status_text = "⏹ Hali sozlanmagan"
    elif status == "not_started":
        status_text = f"⏳ Rejalashtirilgan ({_fmt_dt(contest['start_time'])} da boshlanadi)"
    elif status == "active":
        status_text = f"✅ Faol (tugash: {_fmt_dt(contest['end_time'])})"
    else:
        status_text = "🏁 Yakunlangan"
    await message.answer(
        f"👨‍💼 Admin panel\n\nKonkurs holati: {status_text}",
        reply_markup=admin_main_menu_kb()
    )


@router.message(F.text == ADMIN_BTN_EXIT)
async def admin_exit(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("🚪 Admin paneldan chiqdingiz.", reply_markup=main_menu_kb())


# --- Konkursni boshlash: vaqt -> vaqt -> shartlar -> sovg'alar ---

@router.message(F.text == ADMIN_BTN_START_CONTEST)
async def admin_start_contest(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await message.answer(
        "🗓 Konkurs QACHON boshlanadi? Formatda yuboring:\n<code>KK.OO.YYYY SS:DD</code>\n"
        "Masalan: <code>15.08.2026 09:00</code>",
        parse_mode="HTML", reply_markup=None
    )
    await state.set_state(AdminState.waiting_start_time)


@router.message(AdminState.waiting_start_time, F.text != BACK_BTN)
async def process_start_time(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    try:
        dt = _parse_dt_tashkent(message.text)
    except ValueError:
        await message.answer("❌ Format noto'g'ri. Masalan: <code>15.08.2026 09:00</code>", parse_mode="HTML")
        return
    await state.update_data(start_time=int(dt.timestamp()))
    await message.answer(
        "🏁 Konkurs QACHON tugaydi? Formatda yuboring:\n<code>KK.OO.YYYY SS:DD</code>", parse_mode="HTML"
    )
    await state.set_state(AdminState.waiting_end_time)


@router.message(AdminState.waiting_end_time, F.text != BACK_BTN)
async def process_end_time(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    try:
        dt = _parse_dt_tashkent(message.text)
    except ValueError:
        await message.answer("❌ Format noto'g'ri. Masalan: <code>20.08.2026 20:00</code>", parse_mode="HTML")
        return
    data = await state.get_data()
    end_ts = int(dt.timestamp())
    if end_ts <= data["start_time"]:
        await message.answer("❌ Tugash vaqti boshlanish vaqtidan KEYIN bo'lishi kerak. Qaytadan yuboring:")
        return
    await state.update_data(end_time=end_ts)
    await message.answer("📜 Konkurs SHARTLARINI yozing (bitta xabar sifatida):")
    await state.set_state(AdminState.waiting_terms)


@router.message(AdminState.waiting_terms, F.text != BACK_BTN)
async def process_terms(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.update_data(terms=message.text)
    await message.answer("🎁 Endi SOVG'ALAR ro'yxatini yozing (bitta xabar sifatida):")
    await state.set_state(AdminState.waiting_prizes)


@router.message(AdminState.waiting_prizes, F.text != BACK_BTN)
async def process_prizes(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    data = await state.get_data()
    await db.start_contest(data["start_time"], data["end_time"], data["terms"], message.text)
    await state.clear()
    await message.answer(
        f"✅ <b>Konkurs sozlandi va faollashtirildi!</b>\n\n"
        f"🗓 Boshlanish: {_fmt_dt(data['start_time'])}\n"
        f"🏁 Tugash: {_fmt_dt(data['end_time'])}\n\n"
        f"📜 Shartlar:\n{data['terms']}\n\n"
        f"🎁 Sovg'alar:\n{message.text}\n\n"
        f"Endi barcha foydalanuvchilar \"📜 Shartlar\" va \"🎁 Sovg'alar\" tugmalari orqali buni ko'ra oladi.",
        parse_mode="HTML", reply_markup=admin_main_menu_kb()
    )


# --- G'oliblar / statistika / broadcast ---

@router.message(F.text == ADMIN_BTN_WINNERS)
async def admin_winners(message: Message):
    if not await is_admin(message.from_user.id):
        return
    top = await db.get_top_users(10)
    if not top:
        await message.answer("Hali ishtirokchilar yo'q.", reply_markup=admin_main_menu_kb())
        return

    lines = ["🏆 G'oliblar ro'yxati:\n"]
    for i, u in enumerate(top, start=1):
        full_name = html.escape(u["full_name"] or "Noma'lum")
        tid = u["telegram_id"]
        count = u["invited_count"]
        # ID raqami ko'k rangda va bosiladigan (bosilganda profilga o'tadi)
        lines.append(
            f"{i}.{full_name}  {count} <a href=\"tg://user?id={tid}\">id:{tid}</a>"
        )

    await message.answer("\n".join(lines), parse_mode="HTML", reply_markup=admin_main_menu_kb())


@router.message(F.text == ADMIN_BTN_STATS)
async def admin_stats(message: Message):
    if not await is_admin(message.from_user.id):
        return
    total_users, total_refs, joined = await db.get_total_stats()
    await message.answer(
        f"📊 Umumiy statistika:\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"✅ Kanal(lar)ga qo'shilganlar: {joined}\n"
        f"🔗 Jami referal harakatlar: {total_refs}",
        reply_markup=admin_main_menu_kb()
    )


@router.message(F.text == ADMIN_BTN_BROADCAST)
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await message.answer("📣 Yubormoqchi bo'lgan xabaringizni yozing:", reply_markup=None)
    await state.set_state(AdminState.waiting_broadcast)


@router.message(AdminState.waiting_broadcast, F.text != BACK_BTN)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await db.get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(
        f"📣 Xabar yuborildi!\n✅ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}",
        reply_markup=admin_main_menu_kb()
    )


# --- Majburiy kanallar ---

@router.message(F.text == ADMIN_BTN_CHANNELS)
async def admin_channels_menu(message: Message):
    if not await is_admin(message.from_user.id):
        return
    channels = await db.get_mandatory_channels()
    if channels:
        text = "🔒 <b>Hozirgi majburiy kanallar:</b>\n\n" + "\n".join(f"📢 {ch['title']}" for ch in channels)
    else:
        text = "🔒 Hozircha majburiy kanal qo'shilmagan."
    await message.answer(text, reply_markup=channels_menu_kb(), parse_mode="HTML")


@router.message(F.text == CHANNELS_BTN_ADD)
async def channel_add_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await message.answer(
        "✏️ Kanalning @username'ini yuboring (masalan: <code>@mening_kanalim</code>).\n\n"
        "⚠️ Bot o'sha kanalda ADMIN bo'lishi shart, aks holda a'zolikni tekshira olmaydi.",
        parse_mode="HTML", reply_markup=None
    )
    await state.set_state(AdminState.waiting_channel_username)


@router.message(AdminState.waiting_channel_username, F.text != BACK_BTN)
async def channel_add_finish(message: Message, state: FSMContext, bot: Bot):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    username = message.text.strip()
    if not username.startswith("@"):
        username = "@" + username

    try:
        chat = await bot.get_chat(username)
    except Exception as e:
        await message.answer(
            f"❌ Kanal topilmadi: {e}\nBotni kanalga admin qilib qo'shib, qaytadan urinib ko'ring.",
            reply_markup=channels_menu_kb()
        )
        return

    try:
        invite_link = await bot.export_chat_invite_link(chat.id)
    except Exception:
        invite_link = f"https://t.me/{chat.username}" if chat.username else None

    await db.add_mandatory_channel(chat.id, chat.username, chat.title, invite_link)
    await message.answer(f"✅ \"{chat.title}\" majburiy kanallar ro'yxatiga qo'shildi.", reply_markup=channels_menu_kb())


@router.message(F.text == CHANNELS_BTN_REMOVE)
async def channel_remove_menu(message: Message):
    if not await is_admin(message.from_user.id):
        return
    channels = await db.get_mandatory_channels()
    if not channels:
        await message.answer("Hozircha kanal yo'q.", reply_markup=channels_menu_kb())
        return
    await message.answer("O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=channels_remove_kb(channels))


@router.callback_query(F.data.startswith("ch_remove:"))
async def channel_remove_confirm(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer()
        return
    channel_db_id = int(callback.data.split(":", 1)[1])
    await db.remove_mandatory_channel(channel_db_id)
    await callback.message.edit_text("✅ Kanal o'chirildi.")
    await callback.answer()


# --- Admin qo'shish ---

@router.message(F.text == ADMIN_BTN_ADD_ADMIN)
async def add_admin_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await message.answer(
        "✏️ Yangi admin etib tayinlamoqchi bo'lgan foydalanuvchining Telegram ID raqamini yuboring:",
        reply_markup=None
    )
    await state.set_state(AdminState.waiting_new_admin_id)


@router.message(AdminState.waiting_new_admin_id, F.text != BACK_BTN)
async def add_admin_finish(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.clear()
    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Faqat raqam yuboring.")
        return
    await db.add_admin(new_admin_id)
    await message.answer(
        f"✅ <code>{new_admin_id}</code> endi admin etib tayinlandi.",
        parse_mode="HTML", reply_markup=admin_main_menu_kb()
    )
