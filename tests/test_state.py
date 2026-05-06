import os
import pytest
from src.state import StateManager

def test_extract_next_block(tmp_path):
    ctx_file = tmp_path / "generator_context.md"
    archive_file = tmp_path / "archive.md"
    
    ctx_file.write_text("Block 1\n---\nBlock 2\n---\nBlock 3")
    
    manager = StateManager(ctx_file=str(ctx_file), archive_file=str(archive_file))
    block = manager.pop_next_block()
    
    assert block.strip() == "Block 1"
    assert ctx_file.read_text().strip() == "Block 2\n---\nBlock 3"

def test_archive_block(tmp_path):
    archive_file = tmp_path / "archive.md"
    archive_file.write_text("Old Archive")
    
    manager = StateManager(ctx_file="dummy.md", archive_file=str(archive_file))
    manager.archive_block("New Block")
    
    assert "Old Archive" in archive_file.read_text()
    assert "New Block" in archive_file.read_text()
    assert "---" in archive_file.read_text()
