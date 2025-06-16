import os

def print_directory_tree(start_path, indent=''):
    for item in os.listdir(start_path):
        path = os.path.join(start_path, item)
        if os.path.isdir(path):
            print(f"{indent}📁 {item}/")
            print_directory_tree(path, indent + '    ')
        else:
            print(f"{indent}📄 {item}")

# Start from current working directory
project_root = os.getcwd()
print(f"\n📦 Project structure for: {project_root}\n")
print_directory_tree(project_root)
