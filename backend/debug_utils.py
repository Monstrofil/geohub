"""
Debug utilities for tree structures and other debugging needs.
"""

from models import Tree, TreeEntry, File


async def dump_tree_structure(root_tree: Tree, indent: str = "", max_depth: int = 10, current_depth: int = 0):
    """
    Recursively dump tree structure for debugging.
    
    Args:
        root_tree: The root tree to dump
        indent: Current indentation string
        max_depth: Maximum depth to traverse (prevent infinite recursion)
        current_depth: Current depth level
    """
    if current_depth >= max_depth:
        print(f"{indent}... (max depth reached)")
        return
    
    print(f"{indent}📁 {root_tree.name} (id: {root_tree.id})")
    
    if not root_tree.entries:
        print(f"{indent}   └── (empty)")
        return
    
    # Get all entries for this tree
    entries = await TreeEntry.filter(id__in=root_tree.entries)
    
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        prefix = "└──" if is_last else "├──"
        
        if entry.object_type == "file":
            # Get file details
            file_obj = await File.get_or_none(id=entry.object_id)
            file_name = file_obj.name if file_obj else f"<file {entry.object_id}>"
            print(f"{indent}   {prefix} 📄 {entry.path} -> {file_name}")
            
            # Dump file tags information
            if file_obj and file_obj.tags:
                print(f"{indent}      🏷️  Tags: {file_obj.tags}")
            elif file_obj:
                print(f"{indent}      🏷️  Tags: (empty)")
            else:
                print(f"{indent}      🏷️  Tags: (file not found)")
        elif entry.object_type == "tree":
            # Recursively dump subtree
            subtree = await Tree.get_or_none(id=entry.object_id)
            if subtree:
                print(f"{indent}   {prefix} 📁 {entry.path}/")
                next_indent = indent + ("   " if is_last else "│  ")
                await dump_tree_structure(subtree, next_indent, max_depth, current_depth + 1)
            else:
                print(f"{indent}   {prefix} ❌ {entry.path} -> <missing tree {entry.object_id}>")
        else:
            print(f"{indent}   {prefix} ❓ {entry.path} -> <unknown type {entry.object_type}>")


async def debug_tree(tree: Tree, title: str = "Tree Structure"):
    """
    Helper function to dump tree structure with a title.
    
    Args:
        tree: The tree to display
        title: Title for the tree dump
    """
    print(f"\n{'='*50}")
    print(f"🌳 {title}")
    print(f"{'='*50}")
    await dump_tree_structure(tree)
    print(f"{'='*50}\n") 