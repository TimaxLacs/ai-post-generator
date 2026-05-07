import asyncio
import logging
from src.config import settings
from src.utils import extract_images, setup_logging
from src.db import init_db, ingest_markdown, get_next_pending_post, update_post_state
from src.ai import AIPipeline
from src.publishers import PublisherManager

logger = logging.getLogger(__name__)

async def run() -> bool:
    setup_logging()
    logger.info("Starting AI Post Generator")
    
    await init_db()
    await ingest_markdown()
    
    ai = AIPipeline()
    pub_manager = PublisherManager()
    
    try:
        while True:
            post = await get_next_pending_post()
            if not post:
                logger.info("No pending topics in queue.")
                return True
                
            post_id = post["id"]
            context = post["context"]
            
            try:
                # 1. Clean context and extract images securely
                clean_context, images = extract_images(context)
                logger.info("Processing post_id %s: %s...", post_id, clean_context[:50])
                
                # 2. Update status to generating
                await update_post_state("queue.db", post_id, draft="", status="generating")
                
                # 3. AI Generation
                approved, draft, feedback = await ai.process_block(clean_context)
                
                if not approved:
                    logger.warning("Post %s rejected after 3 attempts.", post_id)
                    await update_post_state("queue.db", post_id, draft=draft, status="manual_review", feedback=feedback)
                    continue
                    
                # 4. Publishing
                logger.info("Post %s approved! Publishing...", post_id)
                await update_post_state("queue.db", post_id, draft=draft, status="publishing")
                
                pub_results = await pub_manager.publish_all(draft, images)
                
                tg_ok = pub_results.get("telegram", False)
                vk_ok = pub_results.get("vk", False)
                
                # 5. Determine final state
                if tg_ok and vk_ok:
                    logger.info("Post %s published successfully to all channels.", post_id)
                    await update_post_state("queue.db", post_id, draft=draft, status="published", tg_ok=True, vk_ok=True)
                elif tg_ok or vk_ok:
                    logger.warning("Post %s partially published: %s", post_id, pub_results)
                    await update_post_state("queue.db", post_id, draft=draft, status="partial_failure", feedback="API Error on some platforms", tg_ok=tg_ok, vk_ok=vk_ok)
                else:
                    logger.error("Post %s failed to publish entirely.", post_id)
                    await update_post_state("queue.db", post_id, draft=draft, status="failed", feedback="Complete API Publishing Error")
                    
                # Sleep interval after successful (or partially successful) publish
                if tg_ok or vk_ok:
                    logger.info("Waiting %s seconds before next post...", settings.post_interval_seconds)
                    await asyncio.sleep(settings.post_interval_seconds)
                    
            except Exception as e:
                logger.exception("Unhandled error processing post %s", post_id)
                await update_post_state("queue.db", post_id, draft="", status="failed", feedback=f"Processing Error: {e}")
                continue
                
    finally:
        await ai.close()
        await pub_manager.close()

if __name__ == "__main__":
    asyncio.run(run())
