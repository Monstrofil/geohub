from models import File, Tree, TreeEntry, Commit, Ref
import hashlib
import random
import logging
from contextlib import contextmanager, asynccontextmanager
import copy


async def create_commit(tree, parent_commit, message):
    commit = await Commit.create(
        tree=tree, 
        parent=parent_commit, 
        message=message
    )
    ref = await Ref.get_or_none(name="main")
    ref.commit = commit
    await ref.save()
    return commit


async def update_object(orig_obj_id, new_obj, message=None, object_type="file"):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_tree = await head.tree
    head_entries = set(head_tree.entries)
    entries_objs = await TreeEntry.filter(
        object_id=orig_obj_id, object_type=object_type
    )
    tree_entry_obj = None

    logging.debug("head_entries: %s", head_entries)
    logging.debug("entries_objs: %s", entries_objs)
    for entry in entries_objs:
        if str(entry.id) in head_entries:
            tree_entry_obj = entry
            break

    assert tree_entry_obj is not None, f"Unexpected {object_type} without tree entry"
    tree_entry = await TreeEntry.create(
        path=tree_entry_obj.path, object_type=object_type, object_id=new_obj.id
    )

    await tree_entry.save()
    head_entries.remove(str(tree_entry_obj.id))
    head_entries.add(str(tree_entry.id))
    tree = await Tree.create(entries=list(head_entries))

    commit_message = message or f"Update {object_type} {new_obj.name if hasattr(new_obj, 'name') else new_obj.id}"
    return await create_commit(tree, head, commit_message)


async def delete_object(obj, message=None, object_type="file"):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_tree = await head.tree
    head_entries = set(head_tree.entries)
    entries_objs = await TreeEntry.filter(object_id=obj.id, object_type=object_type)
    tree_entry_obj = None
    for entry in entries_objs:
        if str(entry.id) in head_entries:
            tree_entry_obj = entry
            break
    assert tree_entry_obj is not None, f"Unexpected {object_type} without tree entry"

    head_entries.remove(str(tree_entry_obj.id))
    tree_id = hashlib.sha1(("".join(list(head_entries))).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=list(head_entries))

    commit_message = message or f"Delete {object_type} {obj.name if hasattr(obj, 'name') else obj.id}"
    return await create_commit(tree, head, commit_message)


def create_tree_entry(object_type: str, object_id: int, path: str):
    entry = TreeEntry.create(
        path=path,
        object_type=object_type,
        object_id=object_id
    )
    return entry


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


class Index:
    def __init__(self, tree, entries):
        self.tree = tree
        self.entries: dict[str, TreeEntry] = entries
        self.updated = False

    async def add_tree_entry(self, new_entry):
        self.entries[str(new_entry.id)] = new_entry
        self.updated = True

    async def update_tree_entry(self, old_entry, new_entry):
        self.entries[str(old_entry.id)] = new_entry
        self.updated = True

    async def remove_tree_entry(self, tree: Tree, path: str) -> Tree:
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
        tree_path = await resolve_tree(tree, path)
        logging.debug("Resolved tree path for removal: %s", repr(tree_path))
        
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
            if target_tree.entries:
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
        return new_trees[-1]


    async def insert_tree_entry(self, tree: Tree, new_entry: TreeEntry, path: str) -> Tree:
        tree_path = await resolve_tree(tree, path)
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
        return new_trees[-1]


    async def commit(self, message, ref): 
        tree_ids = [str(entry.id) for entry in self.entries.values()]
        new_tree = await Tree.create(entries=tree_ids)

        new_commit = await Commit.create(
            tree_id=new_tree.id,
            parent_id=ref.commit_id,
            message=message
        )

        ref.commit = new_commit
        logging.debug("new commit head: %s", new_commit.id)
        await ref.save()
        return new_commit


@asynccontextmanager
async def stage_changes(head: Commit):
    """Context manager for staging changes to a commit's tree."""
    entries = {}

    tree_entry_ids = (await head.tree).entries
    logging.debug("tree_entry_ids: %s", tree_entry_ids)
    async for entry in TreeEntry.filter(id__in=tree_entry_ids).all():
        entries[str(entry.id)] = entry

    assert len(tree_entry_ids) == len(entries), "Entries mismatch (broken db?)"

    logging.debug("entries: %s", entries)
    index = Index(head, entries)
    try:
        yield index
    finally:
        pass
