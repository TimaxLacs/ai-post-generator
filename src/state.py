import os
import re
import aiofiles
from typing import Optional

class StateManager:
    def __init__(self, ctx_file: str = "generator_context.md", archive_file: str = "archive.md", manual_file: str = "manual_review.txt"):
        self.ctx_file = ctx_file
        self.archive_file = archive_file
        self.manual_file = manual_file

    async def setup(self) -> None:
        for f in [self.ctx_file, self.archive_file, self.manual_file]:
            if not os.path.exists(f):
                try:
                    async with aiofiles.open(f, 'w', encoding='utf-8') as file:
                        await file.write("")
                except (OSError, PermissionError) as e:
                    print(f"Error creating file {f}: {e}")

    async def pop_next_block(self) -> Optional[str]:
        async with aiofiles.open(self.ctx_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            
        if not content.strip():
            return None
            
        blocks = re.split(r'\r?\n---+\s*\r?\n', content)
        first_block = blocks[0].strip()
        
        if len(blocks) > 1:
            remaining_content = '\n---\n'.join(blocks[1:])
        else:
            remaining_content = ""
            
        tmp_file = f"{self.ctx_file}.tmp"
        async with aiofiles.open(tmp_file, 'w', encoding='utf-8') as f:
            await f.write(remaining_content)
            
        os.replace(tmp_file, self.ctx_file)
            
        return first_block

    async def archive_block(self, block: str) -> None:
        async with aiofiles.open(self.archive_file, 'a', encoding='utf-8') as f:
            await f.write(f"\n{block}\n---\n")
            
    async def save_manual_review(self, block: str, draft: str, feedback: str) -> None:
        async with aiofiles.open(self.manual_file, 'a', encoding='utf-8') as f:
            await f.write(f"CONTEXT:\n{block}\n\nDRAFT:\n{draft}\n\nFEEDBACK:\n{feedback}\n---\n")
