import hashlib

def calculate_md5(file_path):
    """Calculate and return the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):  # Read the file in chunks to handle large files
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return "File not found."
    except Exception as e:
        return f"An error occurred: {e}"

# Example usage
file_path = "path/to/your/file.txt"  # Replace with the actual file path
md5_hash = calculate_md5(file_path)
print(f"MD5 hash of the file: {md5_hash}")
