import os
from collections import defaultdict


def count_lines(content):
    return len(content.splitlines())


ALLOWED_EXTENSIONS = ["py", "css", "js", "html"]


def read_files(root_dir, exclude_files=None, exclude_dirs=None):
    lines_in_files = defaultdict(int)
    if exclude_files is None:
        exclude_files = []
    if exclude_dirs is None:
        exclude_dirs = ["venv", ".venv"]

    shown_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            ext = filename.split(".")[-1]
            if ext in ALLOWED_EXTENSIONS:

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)

                if full_path == __file__:
                    continue

                shown_files.append(rel_path)

                if rel_path in exclude_files or filename in exclude_files:
                    continue

                try:
                    with open(full_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        lines_in_files[full_path] = count_lines(content)
                        print(f"\n{'=' * 10} {rel_path} {'=' * 10}")
                        print(content)
                except Exception as e:
                    print(f"\nError reading {rel_path}: {str(e)}")

    total_lines = sum(lines_in_files.values())
    sorted_lines_in_files = dict(
        sorted(lines_in_files.items(), key=lambda item: item[1])
    )
    print()
    print("Lines in files")
    for file, n in sorted_lines_in_files.items():
        print(f"{file.rjust(70)}: {n}")

    shown_files_count = len(shown_files)
    print(f"Total files: {shown_files_count}")
    print(f"Total lines: {total_lines}")


def main():
    directory = "."

    if not os.path.isdir(directory):
        print("Directory not found")
        return

    exclude_files = []

    exclude_dirs = [".venv", ".venv1", "gen", "admin", "edit_my_tasks", "profile"]
    read_files(directory, exclude_files, exclude_dirs)


if __name__ == "__main__":
    main()
