from models import File, Tree, TreeEntry, Commit, Ref
import hashlib
import random
import logging
import debug_utils
from contextlib import contextmanager, asynccontextmanager
import copy


async def resolve_tree(root: Tree, path: str) -> list[tuple[Tree, TreeEntry]]:
    if not path:
        return [(root, None)]

    tokens = path.split('/')
    
    leaf = root
    leafs = []
    
    # Process tokens from left to right (not reverse)
    for i, path_token in enumerate(tokens):
        entries_query = TreeEntry.filter(id__in=leaf.entries)
        entries_list = list(await entries_query.filter())
        logging.debug('all entries: %s', entries_list)
        entry = await entries_query.get_or_none(path=path_token)
        if entry is None:
            raise FileNotFoundError("Path %s does not exist" % path_token)
        assert entry is not None

        leafs.append((leaf, entry))

        if entry.object_type == "file":
            # If we found a file, check if there are more tokens
            # If so, we're trying to access a file as if it were a directory
            if i < len(tokens) - 1:
                raise NotADirectoryError("Path %s is not a directory" % path_token)
            # If we found a file and it's the last token, we're done
            break

        # Navigate to the next tree
        leaf = await Tree.get_or_none(id=entry.object_id)
        if leaf is None:
            raise FileNotFoundError("Tree %s does not exist" % entry.object_id)
    else:
        # Add the final leaf (the tree where we ended up)
        leafs.append((leaf, None))

    return leafs



async def resolve_entry(root: Tree, path: str) -> list[tuple[Tree, TreeEntry]]:
    if not path:
        raise FileNotFoundError(path)

    tokens = path.split('/')
    
    leaf = root
    
    entry = None
    for i, path_token in enumerate(tokens):
        entries_query = TreeEntry.filter(id__in=leaf.entries)
        entries_list = list(await entries_query.filter())
        logging.debug('all entries: %s', entries_list)

        entry = await entries_query.get_or_none(path=path_token)
        if entry is None:
            raise FileNotFoundError("Path %s does not exist" % path_token)
        assert entry is not None

        if entry.object_type == "file":
            # If we found a file, check if there are more tokens
            # If so, we're trying to access a file as if it were a directory
            if i < len(tokens) - 1:
                raise NotADirectoryError("Path %s is not a directory" % path_token)
            # If we found a file and it's the last token, we're done
            break

        # Navigate to the next tree
        leaf = await Tree.get_or_none(id=entry.object_id)
        if leaf is None:
            raise FileNotFoundError("Tree %s does not exist" % entry.object_id)

    if entry is None:
        raise FileNotFoundError(path)
    return entry



class Index:
    def __init__(self, tree):
        self.tree = tree
        self.updated = False

    async def remove_tree_entry(self, path: str, force: bool = False) -> Tree:
        """
        Remove a tree entry from the specified path.
        
        Args:
            tree: The root tree to modify
            path: The path to the entry to remove
            
        Returns:
            A new tree with the entry removed
            
        Raises:
            FileNotFoundError: If the path does not exist
            OSError: If trying to remove a non-empty collection
        """
        tree_path = await resolve_tree(self.tree, path)
        logging.debug("Resolved tree path for removal: %s", repr(tree_path))
        
        # TODO: rewrite this hallucination from AI
        # Find the target entry to remove (last non-None entry in path)
        target_entry = None
        for i in range(len(tree_path) - 1, -1, -1):
            if tree_path[i][1] is not None:
                target_entry = tree_path[i][1]
                break
        
        if target_entry is None:
            raise FileNotFoundError(f"No entry found at path: {path}")
        
        logging.debug("Target entry to remove: %s (type: %s)", repr(target_entry), target_entry.object_type)
        
        # Rule 2: If target is a tree and has entries, raise OSError
        if target_entry.object_type == "tree":
            target_tree = await Tree.get(id=target_entry.object_id)
            if not force and target_tree.entries:
                raise OSError(f"collection not empty")
        
        # Rule 1: Only remove the last item, rest stay
        # Process the tree path in reverse order to rebuild the tree structure
        new_trees = []
        
        for i, (leaf, tree_entry) in enumerate(reversed(tree_path)):
            logging.debug("Processing leaf %d: leaf=%s, tree_entry=%s", i, repr(leaf), repr(tree_entry))
            
            # Create a copy of the current leaf
            new_leaf = await Tree.create(
                entries=list(leaf.entries),
                name=leaf.name,
                tags=dict(leaf.tags)
            )
            
            if tree_entry:
                if tree_entry.id == target_entry.id:
                    # This is the target entry to remove
                    new_leaf.entries.remove(str(tree_entry.id))
                    logging.debug("Removed target entry %s from new_leaf", str(tree_entry.id))
                else:
                    # This is an intermediate entry - update it to point to the new child tree
                    if tree_entry.object_type == "tree" and new_trees:
                        # Remove old entry and create new one pointing to updated child
                        new_leaf.entries.remove(str(tree_entry.id))
                        child_tree_id = new_trees[-1].id
                        new_tree_entry = await TreeEntry.create(
                            path=tree_entry.path,
                            object_type=tree_entry.object_type,
                            object_id=child_tree_id
                        )
                        new_leaf.entries.append(str(new_tree_entry.id))
                        logging.debug("Updated intermediate entry %s to point to new child tree", str(tree_entry.id))
                    # For file entries or when no new_trees, keep the entry as is
            
            await new_leaf.save()
            new_trees.append(new_leaf)
        
        # Return the root tree (last one created)
        self.tree = new_trees[-1]

        await debug_utils.debug_tree(await self.tree, "Tree after remove")
        return new_trees[-1]


    async def insert_tree_entry(self, new_entry: TreeEntry, path: str) -> Tree:
        tree_path = await resolve_tree(self.tree, path)
        logging.debug("Resolved tree path: %s (type: %s)", repr(tree_path), type(tree_path))

        # Process the tree path in reverse order so we can properly link trees
        new_trees = []
        
        for leaf, tree_entry in reversed(tree_path):
            new_leaf = await Tree.create(
                entries=list(leaf.entries),
                name=leaf.name,
                tags=dict(leaf.tags)
            )

            if tree_entry:
                new_leaf.entries.remove(str(tree_entry.id))
                # Since we're processing in reverse, the next tree in new_trees is the child
                child_tree_id = new_trees[-1].id if new_trees else tree_entry.object_id
                new_tree_entry = await TreeEntry.create(
                    path=tree_entry.path,
                    object_type=tree_entry.object_type,
                    object_id=child_tree_id
                )

                new_leaf.entries.append(str(new_tree_entry.id))
                logging.debug("added entry %s to %s", repr(new_tree_entry), repr(new_leaf))
            else:
                new_leaf.entries.append(str(new_entry.id))
                logging.debug("added entry %s to %s", repr(new_entry), repr(new_leaf))

            logging.debug("new_leaf: %s", repr(new_leaf))
            
            await new_leaf.save()
            new_trees.append(new_leaf)
        
        # Return the root tree (last one created)
        self.tree = new_trees[-1]
        await debug_utils.debug_tree(await self.tree, "Tree after insert")
        return new_trees[-1]


    async def commit(self, message, ref): 
        import debug_utils

        await debug_utils.debug_tree(await (await ref.commit).tree, "Tree before commit")

        new_commit = await Commit.create(
            tree_id=self.tree.id,
            parent_id=ref.commit_id,
            message=message
        )

        ref.commit = new_commit
        logging.debug("new commit head: %s", new_commit.id)
        await ref.save()

        await debug_utils.debug_tree(await new_commit.tree, "Tree after commit")

        return new_commit


@asynccontextmanager
async def stage_changes(head: Commit):
    """Context manager for staging changes to a commit's tree."""
    index = Index(await head.tree)
    try:
        yield index
    finally:
        pass
