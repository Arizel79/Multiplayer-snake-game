import os


def read_files(root_dir, exclude_files=None, exclude_dirs=None):
    if exclude_files is None:
        exclude_files = []
    if exclude_dirs is None:
        exclude_dirs = ['venv']

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            if filename.endswith('.html') or filename.endswith('.js') or filename.endswith('.css'):
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)

                if rel_path in exclude_files or filename in exclude_files:
                    continue

                try:
                    with open(full_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        print(f"\n{'=' * 10} {rel_path} {'=' * 10}")
                        print(content)
                except Exception as e:
                    print(f"\nError reading {rel_path}: {str(e)}")


def main():
    directory = "."

    if not os.path.isdir(directory):
        print("Directory not found")
        return

    exclude_files = ["read_all.py"]


    exclude_dirs = ['.venv', "gen"]
    read_files(directory, exclude_files, exclude_dirs)


if __name__ == '__main__':
    main()