import os
import json
from pathlib import Path

here = os.path.dirname(os.path.abspath(__file__))

def find_glb_files(directory="."):
    """Recursively find all .glb files in directory, ignoring .git folders, and return paths relative to current dir with leading slash"""
    glb_files = []
    for root, dirs, files in os.walk(directory):
        # Skip .git directories
        if '.git' in dirs:
            dirs.remove('.git')
            
        for file in files:
            if file.lower().endswith('.glb'):
                full_path = Path(root) / file
                # Get path relative to current directory
                rel_path = full_path.relative_to(here)
                # Convert to string with forward slashes and prepend with /
                rel_path_str = "/" + str(rel_path).replace('\\', '/')
                glb_files.append(rel_path_str)
    return glb_files

def save_to_json(file_paths, output_file="models.json"):
    """Save list of file paths to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(file_paths, f, indent=2)

if __name__ == "__main__":
    # Find all GLB files
    glb_files = find_glb_files(here)
    
    # Print found files to console
    print(f"Found {len(glb_files)} .glb files:")
    for file in glb_files:
        print(f"  - {file}")
    
    # Save to JSON
    save_to_json(glb_files)
    print(f"\nSaved file paths to 'models.json'")