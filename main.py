import asyncio
from dotenv import load_dotenv
from src.state import StateManager
from src.ai import AIPipeline
from src.publisher import Publisher

async def run():
    load_dotenv()
    
    state = StateManager()
    ai = AIPipeline()
    publisher = Publisher()
    
    try:
        while True:
            context = await state.pop_next_block()
            if not context:
                print("No more topics in queue.")
                return False
                
            print(f"Processing context: {context[:50]}...")
            approved, draft, feedback = await ai.process_block(context)
            
            if not approved:
                print("Post rejected after 3 attempts. Saving for manual review...")
                await state.save_manual_review(context, draft, feedback)
                continue # Try next block
                
            print("Post approved! Publishing...")
            pub_success = await publisher.publish(draft)
            
            if pub_success:
                print("Published successfully. Archiving...")
                await state.archive_block(context)
                return True
            else:
                print("Failed to publish.")
                # Put it back to manual review if publish failed
                await state.save_manual_review(context, draft, "API Publishing Error")
                return False
    finally:
        await ai.close()
        await publisher.close()

if __name__ == "__main__":
    asyncio.run(run())
