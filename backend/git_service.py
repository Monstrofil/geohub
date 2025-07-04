from models import File, Tree, TreeEntry, Commit, Ref
import hashlib
import random
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

    print("head_entries", head_entries)
    print("entries_objs", entries_objs)
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

    async def commit(self, message, ref): 
        tree_ids = [str(entry.id) for entry in self.entries.values()]
        new_tree = await Tree.create(entries=tree_ids)

        new_commit = await Commit.create(
            tree_id=new_tree.id,
            parent_id=ref.commit_id,
            message=message
        )

        ref.commit = new_commit
        print("new commit head ", new_commit.id)
        await ref.save()
        return new_commit


@asynccontextmanager
async def stage_changes(head: Commit):
    """Context manager for staging changes to a commit's tree."""
    entries = {}

    tree_entry_ids = (await head.tree).entries
    print("tree_entry_ids", tree_entry_ids)
    async for entry in TreeEntry.filter(id__in=tree_entry_ids).all():
        entries[str(entry.id)] = entry

    assert len(tree_entry_ids) == len(entries), "Entries mismatch (broken db?)"

    print("entries", entries)
    index = Index(head, entries)
    try:
        yield index
    finally:
        pass
