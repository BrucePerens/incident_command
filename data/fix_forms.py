import sys
import re
import os

def process_file(filepath):
    # Ensure the file exists
    if not os.path.isfile(filepath):
        print(f"[-] Skipping: {filepath} (File not found)")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[-] Error reading {filepath}: {e}")
        return

    # Check if the fix has already been applied to avoid duplicating it
    if 'will-change: transform' in content:
        print(f"[~] Skipping: {filepath} (Fix already applied)")
        return

    # Regex pattern to find the .form-field class and capture everything inside it
    # \1 captures the declaration up to just before the closing brace
    # \2 captures the closing brace
    pattern = r'(\.form-field\s*\{[^}]*)(\})'
    replacement = r'\1 will-change: transform; \2'

    new_content, count = re.subn(pattern, replacement, content)

    # If the replacement was successful, write the file back
    if count > 0:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"[+] Success: Updated {filepath}")
        except Exception as e:
            print(f"[-] Error writing {filepath}: {e}")
    else:
        print(f"[!] Warning: {filepath} (Could not find '.form-field' class)")

if __name__ == "__main__":
    # Get all arguments passed to the script (excluding the script name itself)
    files = sys.argv[1:]
    
    if not files:
        print("Usage: python3 patch_forms.py <file1.html> <file2.html> ...")
        print("Example: python3 patch_forms.py forms/*.html")
        sys.exit(1)

    print(f"Processing {len(files)} files...\n" + "-"*30)
    
    for file in files:
        process_file(file)
        
    print("-" * 30 + "\nDone!")
