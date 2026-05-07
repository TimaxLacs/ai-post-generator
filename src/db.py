import aiosqlite
import aiofiles
import re
import os
from typing import Optional, Dict, Any

async def init_db(db_path: str = "queue.db"):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context TEXT NOT NULL,
                draft TEXT DEFAULT '',
                feedback TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                tg_published BOOLEAN DEFAULT 0,
                vk_published BOOLEAN DEFAULT 0
            )
        """)
        await db.commit()

async def ingest_markdown(md_path: str = "generator_context.md", db_path: str = "queue.db"):
    if not os.path.exists(md_path):
        return
        
    async with aiofiles.open(md_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        
    if not content.strip():
        return
        
    blocks = re.split(r'\r?\n---+\s*\r?\n', content)
    
    async with aiosqlite.connect(db_path) as db:
        for block in blocks:
            cleaned = block.strip()
            if cleaned:
                await db.execute("INSERT INTO posts (context) VALUES (?)", (cleaned,))
        await db.commit()
        
    # Clear the file atomically
    async with aiofiles.open(md_path, 'w', encoding='utf-8') as f:
        await f.write("")

async def get_next_pending_post(db_path: str = "queue.db") -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM posts WHERE status = 'pending' LIMIT 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_post_state(db_path: str, post_id: int, draft: str, status: str, feedback: str = "", tg_ok: bool = False, vk_ok: bool = False):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            UPDATE posts 
            SET draft = ?, status = ?, feedback = ?, tg_published = ?, vk_published = ?
            WHERE id = ?
        """, (draft, status, feedback, tg_ok, vk_ok, post_id))
        await db.commit()