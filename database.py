import aiosqlite
import uuid
from datetime import datetime

DB_PATH = "contest.db"

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
                prize_description TEXT,
                started_at DATETIME,
                ended_at DATETIME
            )
        """)
        await db.commit()

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

async def get_contest():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM contest ORDER BY id DESC LIMIT 1") as cursor:
            return await cursor.fetchone()

async def start_contest(prize: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE contest SET is_active = 0")
        await db.execute(
            "INSERT INTO contest (is_active, prize_description, started_at) VALUES (1, ?, ?)",
            (prize, datetime.now())
        )
        await db.commit()

async def stop_contest():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE contest SET is_active = 0, ended_at = ? WHERE is_active = 1",
            (datetime.now(),)
        )
        await db.commit()

async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT telegram_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]
