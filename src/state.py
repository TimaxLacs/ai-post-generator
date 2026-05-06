import os

class StateManager:
    def __init__(self, ctx_file="generator_context.md", archive_file="archive.md", manual_file="manual_review.txt"):
        self.ctx_file = ctx_file
        self.archive_file = archive_file
        self.manual_file = manual_file
        
        for f in [self.ctx_file, self.archive_file, self.manual_file]:
            if not os.path.exists(f):
                with open(f, 'w', encoding='utf-8') as file:
                    file.write("")

    def pop_next_block(self):
        with open(self.ctx_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.strip():
            return None
            
        blocks = content.split('\n---\n')
        first_block = blocks[0].strip()
        
        remaining_content = '\n---\n'.join(blocks[1:])
        with open(self.ctx_file, 'w', encoding='utf-8') as f:
            f.write(remaining_content)
            
        return first_block

    def archive_block(self, block):
        with open(self.archive_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{block}\n---\n")
            
    def save_manual_review(self, block, draft, feedback):
        with open(self.manual_file, 'a', encoding='utf-8') as f:
            f.write(f"CONTEXT:\n{block}\n\nDRAFT:\n{draft}\n\nFEEDBACK:\n{feedback}\n---\n")
