from models import File, Tree, TreeEntry, Commit, Ref
import hashlib
import random


async def create_commit(tree, parent_commit, message):
    tree_id = tree.id
    parent_id = parent_commit.id
    commit_content = tree_id + parent_id + message
    commit_id = hashlib.sha1(commit_content.encode()).hexdigest()
    commit = await Commit.create(
        id=commit_id, 
        tree=tree, 
        parent=parent_commit, 
        message=message
    )
    ref = await Ref.get_or_none(name="main")
    ref.commit = commit
    await ref.save()
    return commit


async def add_object(obj, message=None, object_type="file"):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_entries = list((await head.tree).entries)
    tree_entry_sha1 = hashlib.sha1(str(random.getrandbits(256)).encode()).hexdigest()
    tree_entry = await TreeEntry.create(
        sha1=tree_entry_sha1, object_type=object_type, object_id=obj.id
    )
    await tree_entry.save()
    entries_sha1s = head_entries + [tree_entry.sha1]
    tree_id = hashlib.sha1(("".join(entries_sha1s)).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=entries_sha1s)
    commit_message = message or f"Add {object_type} {obj.name if hasattr(obj, 'name') else obj.id}"
    return await create_commit(tree, head, commit_message)


async def update_object(orig_obj_id, new_obj, message=None, object_type="file"):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_tree = await head.tree
    head_entries = set(head_tree.entries)
    entries_objs = await TreeEntry.filter(
        object_id=orig_obj_id, object_type=object_type
    )
    tree_entry_obj = None
    for entry in entries_objs:
        if entry.sha1 in head_entries:
            tree_entry_obj = entry
            break

    assert tree_entry_obj is not None, f"Unexpected {object_type} without tree entry"
    tree_entry_sha1 = hashlib.sha1(str(random.getrandbits(256)).encode()).hexdigest()
    tree_entry = await TreeEntry.create(
        sha1=tree_entry_sha1, object_type=object_type, object_id=new_obj.id
    )

    await tree_entry.save()
    head_entries.remove(tree_entry_obj.sha1)
    head_entries.add(tree_entry.sha1)
    tree_id = hashlib.sha1(("".join(list(head_entries))).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=list(head_entries))
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
        if entry.sha1 in head_entries:
            tree_entry_obj = entry
            break
    assert tree_entry_obj is not None, f"Unexpected {object_type} without tree entry"
    head_entries.remove(tree_entry_obj.sha1)
    tree_id = hashlib.sha1(("".join(list(head_entries))).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=list(head_entries))
    commit_message = message or f"Delete {object_type} {obj.name if hasattr(obj, 'name') else obj.id}"
    return await create_commit(tree, head, commit_message)
