import os
import aiosqlite
import uuid
import time
from datetime import datetime

# Railway Volume mount qilinganda DB_DIR shu yerga ko'rsatadi (masalan /app/data).
# Agar DB_DIR o'rnatilmagan bo'lsa (masalan lokal test paytida), joriy papka ishlatiladi.
DB_DIR = os.getenv("DB_DIR", ".")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "contest.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                full_name TEXT,
                ref_code TEXT UNIQUE,
                invited_count INTEGER DEFAULT 0,
                is_joined_channel INTEGER DEFAULT 0,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inviter_telegram_id INTEGER,
                invited_telegram_id INTEGER UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_active INTEGER DEFAULT 0,
                start_time INTEGER,
                end_time INTEGER,
                terms TEXT,
                prizes TEXT,
                created_at INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                added_at INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mandatory_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                username TEXT,
                title TEXT,
                invite_link TEXT,
                added_at INTEGER
            )
        """)
        await db.commit()
        await _migrate_old_contest_table(db)


async def _migrate_old_contest_table(db):
    """Eski 'contest' jadvalida (prize_description, started_at, ended_at
    ustunlari bilan) yaratilgan bazalarni yangi ustunlar bilan xavfsiz
    to'ldiradi — mavjud ma'lumotlar yo'qolmaydi."""
    cur = await db.execute("PRAGMA table_info(contest)")
    columns = {row[1] for row in await cur.fetchall()}
    if "start_time" not in columns:
        await db.execute("ALTER TABLE contest ADD COLUMN start_time INTEGER")
    if "end_time" not in columns:
        await db.execute("ALTER TABLE contest ADD COLUMN end_time INTEGER")
    if "terms" not in columns:
        await db.execute("ALTER TABLE contest ADD COLUMN terms TEXT")
    if "prizes" not in columns:
        await db.execute("ALTER TABLE contest ADD COLUMN prizes TEXT")
        if "prize_description" in columns:
            await db.execute("UPDATE contest SET prizes = prize_description WHERE prizes IS NULL")
    await db.commit()


# ============================================================
# Users
# ============================================================

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            return await cursor.fetchone()


async def create_user(telegram_id: int, username: str, full_name: str):
    ref_code = str(uuid.uuid4())[:8]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, full_name, ref_code) VALUES (?, ?, ?, ?)",
            (telegram_id, username or "", full_name or "Foydalanuvchi", ref_code)
        )
        await db.commit()
    return await get_user(telegram_id)


async def update_channel_join(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_joined_channel = 1 WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()


async def add_referral(inviter_id: int, invited_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        existing = await db.execute(
            "SELECT id FROM referrals WHERE invited_telegram_id = ?", (invited_id,)
        )
        row = await existing.fetchone()
        if row:
            return False
        await db.execute(
            "INSERT INTO referrals (inviter_telegram_id, invited_telegram_id) VALUES (?, ?)",
            (inviter_id, invited_id)
        )
        await db.execute(
            "UPDATE users SET invited_count = invited_count + 1 WHERE telegram_id = ?",
            (inviter_id,)
        )
        await db.commit()
        return True


async def get_user_by_refcode(ref_code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE ref_code = ?", (ref_code,)) as cursor:
            return await cursor.fetchone()


async def get_top_users(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users ORDER BY invited_count DESC LIMIT ?", (limit,)
        ) as cursor:
            return await cursor.fetchall()


async def get_user_rank(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE invited_count > (SELECT invited_count FROM users WHERE telegram_id = ?)",
            (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return (row[0] + 1) if row else 0


async def get_total_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            total_users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM referrals") as c:
            total_referrals = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_joined_channel = 1") as c:
            joined = (await c.fetchone())[0]
    return total_users, total_referrals, joined


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT telegram_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


# ============================================================
# Konkurs (vaqt, shartlar, sovg'alar)
# ============================================================

async def get_contest():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contest ORDER BY id DESC LIMIT 1") as cursor:
            return await cursor.fetchone()


async def start_contest(start_time: int, end_time: int, terms: str, prizes: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE contest SET is_active = 0")
        await db.execute(
            """INSERT INTO contest (is_active, start_time, end_time, terms, prizes, created_at)
               VALUES (1, ?, ?, ?, ?, ?)""",
            (start_time, end_time, terms, prizes, int(time.time()))
        )
        await db.commit()


async def stop_active_contest():
    """Hozirgi eng oxirgi konkursni DARHOL yakunlaydi: end_time'ni
    HOZIRGI vaqtdan 1 soniya oldinga o'rnatadi. is_active=1 qoldiriladi
    (shunda get_contest_status vaqt bo'yicha 'ended' deb hisoblaydi),
    barcha ma'lumotlar (g'oliblar, statistika) bazada saqlanib qoladi."""
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE contest SET end_time = ? WHERE id = (SELECT id FROM contest ORDER BY id DESC LIMIT 1)",
            (now - 1,)
        )
        await db.commit()


# ============================================================
# Ko'p admin (bazada saqlanadi)
# ============================================================

async def add_admin(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (telegram_id, added_at) VALUES (?, ?)",
            (telegram_id, int(time.time()))
        )
        await db.commit()


async def is_admin_in_db(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM admins WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            return (await cursor.fetchone()) is not None


# ============================================================
# Majburiy kanallar
# ============================================================

async def add_mandatory_channel(chat_id: int, username, title: str, invite_link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO mandatory_channels (chat_id, username, title, invite_link, added_at)
               VALUES (?, ?, ?, ?, ?)""",
            (chat_id, username, title, invite_link, int(time.time()))
        )
        await db.commit()


async def remove_mandatory_channel(channel_db_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM mandatory_channels WHERE id = ?", (channel_db_id,))
        await db.commit()


async def get_mandatory_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mandatory_channels ORDER BY added_at ASC") as cursor:
            return await cursor.fetchall()
