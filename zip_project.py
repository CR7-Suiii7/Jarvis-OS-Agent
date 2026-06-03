import os
import zipfile

def zip_project(output_filename="jarvis_release.zip") -> None:
    # Target workspace base directory
    root_dir = "."
    
    # Directories and files to exclude from the release build
    exclusions = {
        "venv", ".venv", "env",
        ".secrets", ".env",
        ".git", ".pytest_cache", ".mypy_cache",
        "__pycache__", output_filename
    }

    print(f"Initializing Jarvis deployment builder. Packaging into '{output_filename}'...")
    file_count = 0
    
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Obtain relative path matching directory walkthrough
            relative_root = os.path.relpath(root, root_dir)
            parts = relative_root.split(os.sep)
            
            # Skip if directory is under an excluded folder
            if any(part in exclusions for part in parts if part != "."):
                continue
                
            # Filter directories in-place to prevent os.walk from scanning venv/ or .git/
            dirs[:] = [d for d in dirs if d not in exclusions]
            
            for file in files:
                if file in exclusions or file.endswith(".zip"):
                    continue
                    
                file_path = os.path.join(root, file)
                archive_name = os.path.relpath(file_path, root_dir)
                
                # Write file into the compressed file stream
                zipf.write(file_path, archive_name)
                print(f"  [Build] Zipped: {archive_name}")
                file_count += 1
                
    print(f"\nBuild complete. Created credentials-safe deployment archive: '{output_filename}' ({file_count} files).")

if __name__ == "__main__":
    zip_project()
