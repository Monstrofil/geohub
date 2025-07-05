import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from models import Tree, TreeEntry, Commit, Ref, File
from git_service import Index, resolve_tree
from debug_utils import debug_tree


@pytest_asyncio.fixture
async def sample_tree():
    """Create a sample tree for testing."""
    tree = await Tree.create(
        entries=[],
        name="Test Tree",
        tags={}
    )
    return tree


@pytest_asyncio.fixture
async def sample_tree_entry():
    """Create a sample tree entry for testing."""
    entry = await TreeEntry.create(
        path="test_file.txt",
        object_type="file",
        object_id="file-uuid-1"
    )
    return entry


@pytest_asyncio.fixture
async def sample_file():
    """Create a sample file for testing."""
    file = await File.create(
        name="test_file.txt",
        original_name="test_file.txt",
        file_path="/path/to/test_file.txt",
        file_size=1024,
        mime_type="text/plain",
        base_file_type="raw",
        tags={}
    )
    return file


@pytest_asyncio.fixture
async def nested_tree_structure():
    """Create a nested tree structure for testing complex paths."""
    # Create root tree
    root_tree = await Tree.create(
        entries=[],
        name="Root",
        tags={}
    )
    
    # Create subdirectory tree
    subdir_tree = await Tree.create(
        entries=[],
        name="Subdir",
        tags={}
    )
    
    # Create tree entry for subdirectory
    subdir_entry = await TreeEntry.create(
        path="subdir",
        object_type="tree",
        object_id=subdir_tree.id
    )
    
    # Update root tree to include subdirectory
    root_tree.entries = [str(subdir_entry.id)]
    await root_tree.save()
    
    return {
        "root_tree": root_tree,
        "subdir_tree": subdir_tree,
        "subdir_entry": subdir_entry
    }


class TestIndexInsertTreeEntry:
    """Test cases for Index.insert_tree_entry method."""
    
    @pytest.mark.asyncio
    async def test_insert_tree_entry_simple_path(self, sample_tree):
        """Test inserting a tree entry at the root level."""
        # Create a test file
        object_file = await File.create(
            name="file1",
            original_name="file1",
            file_path="none",
            file_size=1,
            mime_type="test",
            base_file_type="raw",
            tags={},
            sha1="sha_1"
        )

        index = Index(sample_tree, {})
        new_entry = await TreeEntry.create(
            path="new_file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        new_tree = await index.insert_tree_entry(sample_tree, new_entry, "")
        
        # Verify original tree is immutable
        assert sample_tree.entries == [], "Original tree must be immutable"
        
        # Verify new tree contains the entry
        assert str(new_entry.id) in new_tree.entries
        
    
    @pytest.mark.asyncio
    async def test_insert_tree_entry_missing_path(self, sample_tree):
        """Test inserting a tree entry with a non-existent path."""
        # Create a test file
        object_file = await File.create(
            name="file1",
            original_name="file1",
            file_path="none",
            file_size=1,
            mime_type="test",
            base_file_type="raw",
            tags={},
            sha1="sha_1"
        )

        index = Index(sample_tree, {})
        new_entry = await TreeEntry.create(
            path="new_file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        # Should raise FileNotFoundError for non-existent path
        with pytest.raises(FileNotFoundError):
            await index.insert_tree_entry(sample_tree, new_entry, "sub/missing")

        # Verify original tree is immutable
        assert sample_tree.entries == [], "Original tree must be immutable"

    
    @pytest.mark.asyncio
    async def test_insert_tree_entry_not_a_collection(self, sample_tree):
        """Test inserting a tree entry into a file (which should fail)."""
        # Create a test file
        object_file = await File.create(
            name="file1",
            original_name="file1",
            file_path="none",
            file_size=1,
            mime_type="test",
            base_file_type="raw",
            tags={},
            sha1="sha_1"
        )

        index = Index(sample_tree, {})
        new_entry = await TreeEntry.create(
            path="new_file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        # Insert first file
        new_tree = await index.insert_tree_entry(sample_tree, new_entry, "")
        assert str(new_entry.id) in new_tree.entries, "File must be inserted"

        # Try to insert another file into the first file (should fail)
        new_entry2 = await TreeEntry.create(
            path="new_file2.txt",
            object_type="file",
            object_id=object_file.id
        )
        with pytest.raises(FileNotFoundError):
            await index.insert_tree_entry(sample_tree, new_entry2, "new_file.txt/sub")

    
    @pytest.mark.asyncio
    async def test_insert_tree_collection(self, sample_tree):
        """Test inserting a tree entry into a collection and then a file into that collection."""
        
        # Create collection tree
        object_collection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        # Create test file
        object_file = await File.create(
            name="file1",
            original_name="file1",
            file_path="none",
            file_size=1,
            mime_type="test",
            base_file_type="raw",
            tags={},
            sha1="sha_1"
        )

        index = Index(sample_tree, {})

        # Create tree entry for collection
        new_dir = await TreeEntry.create(
            path="new_collection",
            object_type="tree",
            object_id=object_collection.id
        )

        # Create tree entry for file
        new_entry = await TreeEntry.create(
            path="new_file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        await debug_tree(sample_tree, "Original")
        
        # Insert collection into root
        new_root_tree = await index.insert_tree_entry(sample_tree, new_dir, "")
        await debug_tree(new_root_tree, "After insertion of collection")
        
        # Insert file into collection
        new_root_tree_2 = await index.insert_tree_entry(new_root_tree, new_entry, "new_collection")
        await debug_tree(new_root_tree_2, "After insertion of file")

        # Verify collection can be resolved
        new_path = await resolve_tree(new_root_tree_2, "new_collection")
        assert new_path != [], "Collection should be resolvable"
        
        # Verify file can be resolved in collection
        new_path = await resolve_tree(new_root_tree_2, "new_collection/new_file.txt")
        assert new_path[-1][1].object_id == object_file.id, "File should be found in collection"

    
    @pytest.mark.asyncio
    async def test_insert_nested_tree_collection(self, sample_tree):
        """Test inserting nested collections and files."""
        
        # Create collection trees
        object_collection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        object_subcollection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        # Create test file
        object_file = await File.create(
            name="file1",
            original_name="file1",
            file_path="none",
            file_size=1,
            mime_type="test",
            base_file_type="raw",
            tags={},
            sha1="sha_1"
        )

        index = Index(sample_tree, {})

        # Create tree entries
        new_dir = await TreeEntry.create(
            path="new_collection",
            object_type="tree",
            object_id=object_collection.id
        )

        new_subdir = await TreeEntry.create(
            path="new_subcollection",
            object_type="tree",
            object_id=object_subcollection.id
        )

        new_entry = await TreeEntry.create(
            path="new_file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        await debug_tree(sample_tree, "Original")
        
        # Insert collection into root
        new_root_tree = await index.insert_tree_entry(sample_tree, new_dir, "")
        await debug_tree(new_root_tree, "After insertion of collection")

        # Insert subcollection into collection
        new_root_tree = await index.insert_tree_entry(new_root_tree, new_subdir, "new_collection")
        await debug_tree(new_root_tree, "After insertion of subcollection")
        
        # Insert file into subcollection
        new_root_tree = await index.insert_tree_entry(new_root_tree, new_entry, "new_collection/new_subcollection")
        await debug_tree(new_root_tree, "After insertion of file")

        # Verify collection can be resolved
        new_path = await resolve_tree(new_root_tree, "new_collection")
        assert new_path != [], "Collection should be resolvable"
        
        # Verify file can be resolved in nested collection
        new_path = await resolve_tree(new_root_tree, "new_collection/new_subcollection/new_file.txt")
        assert new_path[-1][1].object_id == object_file.id, "File should be found in nested collection"

        # Test hardlinking: add the same file to the parent collection
        new_hardlink = await TreeEntry.create(
            path="new_file.txt",
            object_type="file",
            object_id=object_file.id
        )

        new_root_tree = await index.insert_tree_entry(new_root_tree, new_hardlink, "new_collection")
        await debug_tree(new_root_tree, "After hardlinking of file")

        # Verify both instances of the file can be resolved
        new_path = await resolve_tree(new_root_tree, "new_collection")
        assert new_path != [], "Collection should be resolvable"
        
        new_path = await resolve_tree(new_root_tree, "new_collection/new_file.txt")
        assert new_path[-1][1].object_id == object_file.id, "Hardlinked file should be found in collection"
        
    