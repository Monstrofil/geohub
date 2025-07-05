import pytest
import pytest_asyncio
import sys
import os
import logging
from unittest.mock import AsyncMock, patch, MagicMock

# Add the parent directory to the Python path so we can import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

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
        
    
class TestIndexRemoveTreeEntry:
    """Test cases for Index.remove_tree_entry method."""
    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_simple_file(self, sample_tree):
        """Test removing a simple file from the root level."""
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
        
        # Insert file first
        tree_with_file = await index.insert_tree_entry(sample_tree, new_entry, "")
        await debug_tree(tree_with_file, "Tree with file")
        
        # Remove the file
        tree_after_removal = await index.remove_tree_entry(tree_with_file, "new_file.txt")
        await debug_tree(tree_after_removal, "Tree after file removal")
        
        # Verify original tree is immutable
        assert str(new_entry.id) in tree_with_file.entries, "Original tree should still contain the file"
        
        # Verify file is removed from new tree
        assert str(new_entry.id) not in tree_after_removal.entries, "File should be removed from new tree"
        
        # Verify new tree is empty (since we started with empty tree)
        assert tree_after_removal.entries == [], "New tree should be empty after removing the only file"

    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_simple_collection(self, sample_tree):
        """Test removing a simple empty collection."""
        # Create an empty collection
        object_collection = await Tree.create(
            entries=[],
            name="empty_dir",
            tags={}
        )

        index = Index(sample_tree, {})
        new_dir = await TreeEntry.create(
            path="empty_collection",
            object_type="tree",
            object_id=object_collection.id
        )
        
        # Insert collection first
        tree_with_collection = await index.insert_tree_entry(sample_tree, new_dir, "")
        await debug_tree(tree_with_collection, "Tree with empty collection")
        
        # Remove the collection
        tree_after_removal = await index.remove_tree_entry(tree_with_collection, "empty_collection")
        await debug_tree(tree_after_removal, "Tree after collection removal")
        
        # Debug: print the entries
        print(f"Original tree entries: {tree_with_collection.entries}")
        print(f"New tree entries: {tree_after_removal.entries}")
        
        # Verify original tree is immutable
        assert str(new_dir.id) in tree_with_collection.entries, "Original tree should still contain the collection"
        
        # Verify collection is removed from new tree
        assert str(new_dir.id) not in tree_after_removal.entries, "Collection should be removed from new tree"
        
        # Verify new tree is empty
        assert tree_after_removal.entries == [], "New tree should be empty after removing the only collection"

    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_non_empty_collection_raises_exception(self, sample_tree):
        """Test that removing a non-empty collection raises an exception."""
        # Create a collection with a file inside
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

        object_collection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        index = Index(sample_tree, {})
        
        # Create tree entry for collection
        new_dir = await TreeEntry.create(
            path="collection",
            object_type="tree",
            object_id=object_collection.id
        )

        # Create tree entry for file
        new_file = await TreeEntry.create(
            path="file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        # Insert collection first
        tree_with_collection = await index.insert_tree_entry(sample_tree, new_dir, "")
        await debug_tree(tree_with_collection, "Tree with collection")
        
        # Insert file into collection
        tree_with_file = await index.insert_tree_entry(tree_with_collection, new_file, "collection")
        await debug_tree(tree_with_file, "Tree with file in collection")
        
        # Attempt to remove the non-empty collection - should raise exception
        with pytest.raises(OSError):
            await index.remove_tree_entry(tree_with_file, "collection")
        
        # Verify original tree is unchanged
        assert str(new_dir.id) in tree_with_collection.entries, "Original tree should remain unchanged"

    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_file_from_collection(self, sample_tree):
        """Test removing a file from within a collection."""
        # Create a collection with a file inside
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

        object_collection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        index = Index(sample_tree, {})
        
        # Create tree entry for collection
        new_dir = await TreeEntry.create(
            path="collection",
            object_type="tree",
            object_id=object_collection.id
        )

        # Create tree entry for file
        new_file = await TreeEntry.create(
            path="file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        # Insert collection first
        tree_with_collection = await index.insert_tree_entry(sample_tree, new_dir, "")
        
        # Insert file into collection
        tree_with_file = await index.insert_tree_entry(tree_with_collection, new_file, "collection")
        await debug_tree(tree_with_file, "Tree with file in collection")
        
        # Remove the file from the collection
        tree_after_removal = await index.remove_tree_entry(tree_with_file, "collection/file.txt")
        await debug_tree(tree_after_removal, "Tree after file removal from collection")
        
        # Verify original tree is immutable
        collection_path = await resolve_tree(tree_with_file, "collection")
        collection_tree = collection_path[-1][0]
        assert str(new_file.id) in collection_tree.entries, "Original collection should still contain the file"
        
        # Verify file is removed from new tree's collection
        new_collection_path = await resolve_tree(tree_after_removal, "collection")
        new_collection_tree = new_collection_path[-1][0]
        assert str(new_file.id) not in new_collection_tree.entries, "File should be removed from new collection"
        
        # Verify collection still exists but is now empty
        assert len(tree_after_removal.entries) == 1, "Collection should still exist in root"
        assert new_collection_tree.entries == [], "Collection should be empty after file removal"

    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_subcollection(self, sample_tree):
        """Test removing a subcollection from within a collection."""
        # Create nested collections
        object_subcollection = await Tree.create(
            entries=[],
            name="subdir",
            tags={}
        )

        object_collection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        index = Index(sample_tree, {})
        
        # Create tree entries
        new_dir = await TreeEntry.create(
            path="collection",
            object_type="tree",
            object_id=object_collection.id
        )

        new_subdir = await TreeEntry.create(
            path="subcollection",
            object_type="tree",
            object_id=object_subcollection.id
        )
        
        # Insert collection first
        tree_with_collection = await index.insert_tree_entry(sample_tree, new_dir, "")
        
        # Insert subcollection into collection
        tree_with_subcollection = await index.insert_tree_entry(tree_with_collection, new_subdir, "collection")
        await debug_tree(tree_with_subcollection, "Tree with subcollection")
        
        # Remove the subcollection
        tree_after_removal = await index.remove_tree_entry(tree_with_subcollection, "collection/subcollection")
        await debug_tree(tree_after_removal, "Tree after subcollection removal")
        
        # Verify original tree is immutable
        collection_path = await resolve_tree(tree_with_subcollection, "collection")
        collection_tree = collection_path[-1][0]
        assert str(new_subdir.id) in collection_tree.entries, "Original collection should still contain the subcollection"
        
        # Verify subcollection is removed from new tree's collection
        new_collection_path = await resolve_tree(tree_after_removal, "collection")
        new_collection_tree = new_collection_path[-1][0]
        assert str(new_subdir.id) not in new_collection_tree.entries, "Subcollection should be removed from new collection"
        
        # Verify main collection still exists but is now empty
        assert len(tree_after_removal.entries) == 1, "Main collection should still exist in root"
        assert new_collection_tree.entries == [], "Main collection should be empty after subcollection removal"

    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_nonexistent_path_raises_exception(self, sample_tree):
        """Test that removing a non-existent path raises an exception."""
        index = Index(sample_tree, {})
        
        # Attempt to remove non-existent path
        with pytest.raises(FileNotFoundError):
            await index.remove_tree_entry(sample_tree, "nonexistent/file.txt")
        
        # Verify original tree is unchanged
        assert sample_tree.entries == [], "Original tree should remain unchanged"

    
    @pytest.mark.asyncio
    async def test_remove_tree_entry_collection_with_nested_content_raises_exception(self, sample_tree):
        """Test that removing a collection with nested files and subcollections raises an exception."""
        # Create nested structure: collection/subcollection/file.txt
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

        object_subcollection = await Tree.create(
            entries=[],
            name="subdir",
            tags={}
        )

        object_collection = await Tree.create(
            entries=[],
            name="dir",
            tags={}
        )

        index = Index(sample_tree, {})
        
        # Create tree entries
        new_dir = await TreeEntry.create(
            path="collection",
            object_type="tree",
            object_id=object_collection.id
        )

        new_subdir = await TreeEntry.create(
            path="subcollection",
            object_type="tree",
            object_id=object_subcollection.id
        )

        new_file = await TreeEntry.create(
            path="file.txt",
            object_type="file",
            object_id=object_file.id
        )
        
        # Build nested structure
        tree_with_collection = await index.insert_tree_entry(sample_tree, new_dir, "")
        tree_with_subcollection = await index.insert_tree_entry(tree_with_collection, new_subdir, "collection")
        tree_with_file = await index.insert_tree_entry(tree_with_subcollection, new_file, "collection/subcollection")
        await debug_tree(tree_with_file, "Tree with nested structure")
        
        # Attempt to remove the main collection (which contains subcollection and file)
        with pytest.raises(OSError):
            await index.remove_tree_entry(tree_with_file, "collection")
        
        # Verify original tree is unchanged
        assert str(new_dir.id) in tree_with_collection.entries, "Original tree should remain unchanged"
        
    