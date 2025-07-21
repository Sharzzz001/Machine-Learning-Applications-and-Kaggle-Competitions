import os
from tqdm import tqdm

def get_folder_size(folder):
    total_size = 0
    for entry in os.scandir(folder):
        if entry.is_file():
            total_size += entry.stat().st_size
    return total_size

def print_subfolder_sizes_live(parent_folder):
    subfolders = [entry for entry in os.scandir(parent_folder) if entry.is_dir()]
    results = []

    print(f"Calculating folder sizes in: {parent_folder}\n")
    
    for entry in tqdm(subfolders, desc="Processing Folders", unit="folder"):
        folder_size = get_folder_size(entry.path)
        size_mb = folder_size / (1024 * 1024)
        results.append((entry.name, size_mb))
        print(f"{entry.name}: {size_mb:.2f} MB", flush=True)

    # Print final summary sorted by size (descending)
    print("\nSummary (Sorted by Size Descending):\n")
    for name, size_mb in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{name}: {size_mb:.2f} MB")

# Example usage:
parent_folder_path = r"C:\Your\Folder\Path"
print_subfolder_sizes_live(parent_folder_path)