import os
from typing import List, Dict, Any, Union


class FileTreeService:
    def get_file_tree(self, root_path: str) -> Dict[str, Any]:
        """
        Generates a recursive JSON tree of the directory structure.
        """
        name = os.path.basename(root_path)
        return self._build_tree(root_path, name)

    def _build_tree(self, path: str, name: str) -> Dict[str, Any]:
        node = {
            "name": name,
            "path": path,
            "type": "directory" if os.path.isdir(path) else "file",
        }

        if node["type"] == "directory":
            children = []
            try:
                # specific sort: folders first, then files
                with os.scandir(path) as it:
                    entries = list(it)
                    entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))

                    for entry in entries:
                        # Skip hidden files/dirs and common noise
                        if entry.name.startswith(".") or entry.name in [
                            "__pycache__",
                            "venv",
                            "node_modules",
                            "wiki_docs",
                        ]:
                            continue

                        children.append(self._build_tree(entry.path, entry.name))
            except PermissionError:
                pass  # Skip folders we can't read

            node["children"] = children

        return node
