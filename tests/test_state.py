import os
import pytest
import pytest_asyncio
from src.state import StateManager

@pytest_asyncio.fixture
async def isolated_manager(tmp_path):
    ctx_file = tmp_path / "generator_context.md"
    archive_file = tmp_path / "archive.md"
    manual_file = tmp_path / "manual_review.txt"
    
    manager = StateManager(
        ctx_file=str(ctx_file),
        archive_file=str(archive_file),
        manual_file=str(manual_file)
    )
    await manager.setup()
    return manager

@pytest.mark.asyncio
async def test_extract_next_block(isolated_manager):
    ctx_file = isolated_manager.ctx_file
    
    with open(ctx_file, 'w', encoding='utf-8') as f:
        f.write("Block 1\n---\nBlock 2\n---\nBlock 3")
    
    block = await isolated_manager.pop_next_block()
    
    assert block.strip() == "Block 1"
    with open(ctx_file, 'r', encoding='utf-8') as f:
        assert f.read() == "Block 2\n---\nBlock 3"

@pytest.mark.asyncio
async def test_extract_next_block_empty(isolated_manager):
    ctx_file = isolated_manager.ctx_file
    
    with open(ctx_file, 'w', encoding='utf-8') as f:
        f.write("")
        
    block = await isolated_manager.pop_next_block()
    assert block is None

@pytest.mark.asyncio
async def test_extract_next_block_single(isolated_manager):
    ctx_file = isolated_manager.ctx_file
    
    with open(ctx_file, 'w', encoding='utf-8') as f:
        f.write("Only Block")
        
    block = await isolated_manager.pop_next_block()
    assert block.strip() == "Only Block"
    
    with open(ctx_file, 'r', encoding='utf-8') as f:
        assert f.read() == ""

@pytest.mark.asyncio
async def test_archive_block(isolated_manager):
    archive_file = isolated_manager.archive_file
    
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write("Old Archive")
    
    await isolated_manager.archive_block("New Block")
    
    with open(archive_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "Old Archive" in content
        assert "New Block" in content
        assert "---" in content

@pytest.mark.asyncio
async def test_save_manual_review(isolated_manager):
    manual_file = isolated_manager.manual_file
    
    await isolated_manager.save_manual_review("Test Block", "Test Draft", "Test Feedback")
    
    with open(manual_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "CONTEXT:\nTest Block" in content
        assert "DRAFT:\nTest Draft" in content
        assert "FEEDBACK:\nTest Feedback" in content
        assert "---" in content
