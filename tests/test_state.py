import os
import pytest
from src.state import StateManager

@pytest.fixture
def isolated_manager(tmp_path):
    ctx_file = tmp_path / "generator_context.md"
    archive_file = tmp_path / "archive.md"
    manual_file = tmp_path / "manual_review.txt"
    
    return StateManager(
        ctx_file=str(ctx_file),
        archive_file=str(archive_file),
        manual_file=str(manual_file)
    )

def test_extract_next_block(isolated_manager):
    ctx_file = isolated_manager.ctx_file
    
    with open(ctx_file, 'w', encoding='utf-8') as f:
        f.write("Block 1\n---\nBlock 2\n---\nBlock 3")
    
    block = isolated_manager.pop_next_block()
    
    assert block.strip() == "Block 1"
    with open(ctx_file, 'r', encoding='utf-8') as f:
        assert f.read() == "Block 2\n---\nBlock 3"

def test_archive_block(isolated_manager):
    archive_file = isolated_manager.archive_file
    
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write("Old Archive")
    
    isolated_manager.archive_block("New Block")
    
    with open(archive_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Old Archive" in content
        assert "New Block" in content
        assert "---" in content

def test_save_manual_review(isolated_manager):
    manual_file = isolated_manager.manual_file
    
    isolated_manager.save_manual_review("Test Block", "Test Draft", "Test Feedback")
    
    with open(manual_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "CONTEXT:\nTest Block" in content
        assert "DRAFT:\nTest Draft" in content
        assert "FEEDBACK:\nTest Feedback" in content
        assert "---" in content
