import os
import time


# ---------------------------------------------------
# Get Single File Info
# ---------------------------------------------------
def get_file_info(file_path):
    """
    Returns metadata of a single file.
    """

    return {
        "fullfilepath": os.path.realpath(file_path),
        "size": os.path.getsize(file_path),
        "last_modified": time.ctime(os.path.getmtime(file_path)),
        "last_accessed": time.ctime(os.path.getatime(file_path))
    }


# ---------------------------------------------------
# Detailed Folder Structure (Recursive)
# ---------------------------------------------------
def get_folder_structure(root_dir):
    """
    Creates a detailed folder tree from a starting path,
    listing every file with its size and timestamps.
    """

    def build_structure(current_path):
        structure = {}

        for entry in os.listdir(current_path):
            entry_path = os.path.join(current_path, entry)

            if os.path.isdir(entry_path):
                structure[entry] = build_structure(entry_path)
            else:
                structure[entry] = get_file_info(entry_path)

        return structure

    return {
        os.path.basename(root_dir): build_structure(root_dir)
    }


# ---------------------------------------------------
# Simplified Folder Tree (Most Useful Version)
# ---------------------------------------------------
def list_files(startpath):
    """
    Builds a simplified folder tree with file details.
    Recommended function for APIs.
    """

    tree = {}

    for root, dirs, files in os.walk(startpath, followlinks=True):

        relative_path = os.path.relpath(root, startpath)

        # Handle root directory
        if relative_path == ".":
            current_dict = tree
        else:
            dir_path = relative_path.split(os.sep)
            current_dict = tree
            for subdir in dir_path:
                current_dict = current_dict.setdefault(subdir, {})

        # Add files
        for f in files:
            file_path = os.path.join(root, f)

            current_dict[f] = {
                "fullfilepath": os.path.realpath(file_path),
                "size": os.path.getsize(file_path),
                "last_modified": time.ctime(os.path.getmtime(file_path)),
                "last_accessed": time.ctime(os.path.getatime(file_path))
            }

        # Ensure directories appear even if empty
        for d in dirs:
            current_dict.setdefault(d, {})

    return tree


# ---------------------------------------------------
# Alternative Tree Builder (Depth-Based)
# ---------------------------------------------------
def list_files_depth_based(startpath):
    """
    Organizes files and folders based on depth in directory.
    """

    tree = {}

    for root, dirs, files in os.walk(startpath, followlinks=True):

        level = root.replace(startpath, "").count(os.sep)

        if level == 0:
            tree[root] = {}
            current_dict = tree[root]
        else:
            dir_path = root.split(os.sep)
            current_dict = tree[startpath]

            for subdir in dir_path[1:]:
                current_dict = current_dict.setdefault(subdir, {})

        for f in files:
            file_path = os.path.join(root, f)

            current_dict[f] = {
                "fullfilepath": os.path.realpath(file_path),
                "size": os.path.getsize(file_path),
                "last_modified": time.ctime(os.path.getmtime(file_path)),
                "last_accessed": time.ctime(os.path.getatime(file_path))
            }

    return tree


# ---------------------------------------------------
# Alternative Clean Tree Builder
# ---------------------------------------------------
def list_files_simple(startpath):
    """
    Clean alternative tree builder.
    """

    def build_tree(current_path):
        tree = {}

        for root, dirs, files in os.walk(current_path, followlinks=True):

            relative_path = os.path.relpath(root, startpath)
            dir_path = relative_path.split(os.sep)

            current_dict = tree

            for subdir in dir_path:
                if subdir != ".":
                    current_dict = current_dict.setdefault(subdir, {})

            for f in files:
                file_path = os.path.join(root, f)

                current_dict[f] = {
                    "fullfilepath": os.path.realpath(file_path),
                    "size": os.path.getsize(file_path),
                    "last_modified": time.ctime(os.path.getmtime(file_path)),
                    "last_accessed": time.ctime(os.path.getatime(file_path))
                }

        return tree

    return build_tree(startpath)
