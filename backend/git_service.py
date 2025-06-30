from models import File, Tree, TreeEntry, Commit, Ref
import hashlib
import random


async def add_file(file_obj, message=None):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_entries = list((await head.tree).entries)
    tree_entry_sha1 = hashlib.sha1(str(random.getrandbits(256)).encode()).hexdigest()
    tree_entry = await TreeEntry.create(
        sha1=tree_entry_sha1, object_type="file", object_id=file_obj.id
    )
    await tree_entry.save()
    entries_sha1s = head_entries + [tree_entry.sha1]
    tree_id = hashlib.sha1(("".join(entries_sha1s)).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=entries_sha1s)
    commit_message = message or f"Add file {file_obj.name}"
    commit_content = tree_id + head.id + commit_message
    commit_id = hashlib.sha1(commit_content.encode()).hexdigest()
    commit = await Commit.create(
        id=commit_id, tree=tree, parent=head, message=commit_message
    )
    ref.commit = commit
    await ref.save()
    return commit


async def update_file(orig_file_obj_id, new_file_obj, message=None):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_tree = await head.tree
    head_entries = set(head_tree.entries)
    entries_objs = await TreeEntry.filter(
        object_id=orig_file_obj_id, object_type="file"
    )

    tree_entry_obj = None
    for entry in entries_objs:
        if entry.sha1 in head_entries:
            tree_entry_obj = entry
            break
    assert tree_entry_obj is not None, "Unexpected file without tree entry"

    tree_entry_sha1 = hashlib.sha1(str(random.getrandbits(256)).encode()).hexdigest()
    tree_entry = await TreeEntry.create(
        sha1=tree_entry_sha1, object_type="file", object_id=new_file_obj.id
    )
    await tree_entry.save()

    head_entries.remove(tree_entry_obj.sha1)
    head_entries.add(tree_entry.sha1)

    tree_id = hashlib.sha1(("".join(list(head_entries))).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=list(head_entries))

    commit_message = message or f"Update file {new_file_obj.name}"
    commit_content = tree_id + head.id + commit_message
    commit_id = hashlib.sha1(commit_content.encode()).hexdigest()
    commit = await Commit.create(
        id=commit_id, tree=tree, parent=head, message=commit_message
    )

    ref.commit = commit
    await ref.save()
    return commit


async def delete_file(file_obj, message=None):
    ref = await Ref.get_or_none(name="main")
    head = await ref.commit.get()
    head_tree = await head.tree
    head_entries = set(head_tree.entries)
    entries_objs = await TreeEntry.filter(object_id=file_obj.id, object_type="file")
    tree_entry_obj = None
    for entry in entries_objs:
        if entry.sha1 in head_entries:
            tree_entry_obj = entry
            break
    assert tree_entry_obj is not None, "Unexpected file without tree entry"
    head_entries.remove(tree_entry_obj.sha1)
    tree_id = hashlib.sha1(("".join(list(head_entries))).encode()).hexdigest()
    tree = await Tree.create(id=tree_id, entries=list(head_entries))
    commit_message = message or f"Delete file {file_obj.name}"
    commit_content = tree_id + head.id + commit_message
    commit_id = hashlib.sha1(commit_content.encode()).hexdigest()
    commit = await Commit.create(
        id=commit_id, tree=tree, parent=head, message=commit_message
    )
    ref.commit = commit
    await ref.save()
    return commit
