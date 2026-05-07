import pytest
import os
import aiosqlite
from src.db import init_db, ingest_markdown, get_next_pending_post, update_post_state

@pytest.mark.asyncio
async def test_db_workflow(tmp_path):
    db_path = tmp_path / "queue.db"
    md_path = tmp_path / "generator_context.md"
    
    # Setup markdown
    md_path.write_text("Post 1\n---\nPost 2")
    
    await init_db(str(db_path))
    await ingest_markdown(str(md_path), str(db_path))
    
    # Verify markdown is empty
    assert md_path.read_text().strip() == ""
    
    # Get first post
    post = await get_next_pending_post(str(db_path))
    assert post is not None
    assert post["context"] == "Post 1"
    
    # Update state
    await update_post_state(str(db_path), post["id"], draft="Draft 1", status="published", tg_ok=True, vk_ok=True)
    
    # Get second post
    post2 = await get_next_pending_post(str(db_path))
    assert post2["context"] == "Post 2"