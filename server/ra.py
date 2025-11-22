import os
from collections import defaultdict


def count_lines(content):
    return len(content.splitlines())


def read_files(root_dir, exclude_files=None, exclude_dirs=None):
    lines_in_files = defaultdict(int)
    if exclude_files is None:
        exclude_files = []
    if exclude_dirs is None:
        exclude_dirs = ["venv"]

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            if (
                filename.endswith(".py")
                or filename.endswith(".html")
                or filename.endswith(".txt")
                or filename.endswith(".ftl")
            ):
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)

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
    print("Lines in files")
    for file, n in sorted_lines_in_files.items():
        print(f"{file.rjust(70)}: {n}")
    print(f"Total lines: {total_lines}")


def main():
    directory = "."

    if not os.path.isdir(directory):
        print("Directory not found")
        return

    exclude_files = ["ra.py"]

    exclude_dirs = [
        ".venv",
        ".venv1",
        "gen",
        "admin",
        "edit_my_tasks",
        "profile"
    ]
    read_files(directory, exclude_files, exclude_dirs)


if __name__ == "__main__":
    main()
