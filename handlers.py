from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from keyboards import join_channel_kb, main_menu_kb, admin_panel_kb
from config import ADMIN_IDS, CHANNEL_ID, BOT_USERNAME

router = Router()

class AdminState(StatesGroup):
    waiting_prize = State()
    waiting_broadcast = State()

async def check_channel_member(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked", "banned"]
    except:
        return False

@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    user = await db.get_user(user_id)
    if not user:
        user = await db.create_user(user_id, username, full_name)

    args = message.text.split()
    inviter_ref = args[1] if len(args) > 1 and args[1].startswith("ref_") else None
    ref_code = inviter_ref[4:] if inviter_ref else None

    is_member = await check_channel_member(bot, user_id)

    if not is_member:
        await message.answer(
            "👋 Salom! Konkursda ishtirok etish uchun avval kanalimizga a'zo bo'ling:",
            reply_markup=join_channel_kb()
        )
        if ref_code:
            from aiogram.fsm.context import FSMContext
            pass
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
                except:
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
async def check_join_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_member = await check_channel_member(bot, user_id)

    if not is_member:
        await callback.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
        return

    await db.update_channel_join(user_id)
    user = await db.get_user(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user['ref_code']}"

    await callback.message.edit_text(
        f"✅ Ajoyib! Siz kanalga a'zo bo'ldingiz!\n\n"
        f"🔗 Sizning referal linkingiz:\n{ref_link}\n\n"
        f"👥 Qo'shganlar: {user['invited_count']} ta\n\n"
        f"Bu linkni ulashing va g'olib bo'ling! 🏆"
    )
    await callback.message.answer("Menyu:", reply_markup=main_menu_kb())
    await callback.answer()

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

@router.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    contest = await db.get_contest()
    status = "✅ Faol" if contest and contest["is_active"] else "⏹ Faol emas"
    await message.answer(
        f"👨‍💼 Admin panel\n\nKonkurs holati: {status}",
        reply_markup=admin_panel_kb()
    )

@router.callback_query(F.data == "admin_start_contest")
async def admin_start_contest(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.answer("🎁 Mukofot tavsifini yozing (masalan: iPhone 15 Pro):")
    await state.set_state(AdminState.waiting_prize)
    await callback.answer()

@router.message(AdminState.waiting_prize)
async def process_prize(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await db.start_contest(message.text)
    await state.clear()
    await message.answer(f"✅ Konkurs boshlandi!\nMukofot: {message.text}")

@router.callback_query(F.data == "admin_stop_contest")
async def admin_stop_contest(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await db.stop_contest()
    await callback.message.answer("⏹ Konkurs to'xtatildi.")
    await callback.answer()

@router.callback_query(F.data == "admin_winners")
async def admin_winners(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    top = await db.get_top_users(3)
    if not top:
        await callback.message.answer("Hali ishtirokchilar yo'q.")
        await callback.answer()
        return

    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 G'oliblar:\n\n"
    for i, u in enumerate(top):
        text += (
            f"{medals[i]} {u['full_name']}\n"
            f"   Username: @{u['username'] or 'yo\'q'}\n"
            f"   ID: {u['telegram_id']}\n"
            f"   Qo'shganlar: {u['invited_count']} ta\n\n"
        )
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    total_users, total_refs, joined = await db.get_total_stats()
    await callback.message.answer(
        f"📊 Umumiy statistika:\n\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"✅ Kanalga qo'shilganlar: {joined}\n"
        f"🔗 Jami referal harakatlar: {total_refs}"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.answer("📣 Yubormoqchi bo'lgan xabaringizni yozing:")
    await state.set_state(AdminState.waiting_broadcast)
    await callback.answer()

@router.message(AdminState.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.clear()
    user_ids = await db.get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text)
            sent += 1
        except:
            failed += 1
    await message.answer(f"📣 Xabar yuborildi!\n✅ Yuborildi: {sent}\n❌ Yuborilmadi: {failed}")
