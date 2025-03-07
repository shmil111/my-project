import os
import re

# Files to process
doc_files = [
    'windows.md',
    'woodenghostsummary.md',
    'updatereadme.md',
    'userguide.txt',
    'implementation_guide.md'
]

# Characters to remove
special_chars = r'[-_\.]'

def clean_content(content):
    # Clean up file names in content
    content = re.sub(r'\w+[-_\.]+\w+\.(js|py|json|md|txt|bat|ps1|sh)', 
                    lambda m: re.sub(special_chars, '', m.group(0)), 
                    content)
    
    # Clean up other special characters
    content = content.replace('Node.js', 'Nodejs')
    content = content.replace('Eve.exe', 'Eveexe')
    content = re.sub(r'\b\w+[-_\.]\w+\b',
                    lambda m: re.sub(special_chars, '', m.group(0)),
                    content)
    
    return content

def main():
    for file in doc_files:
        file_path = os.path.join(os.getcwd(), file)
        
        # Skip if file doesn't exist
        if not os.path.exists(file_path):
            print(f"Skipping {file} - not found")
            continue
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean up content
        cleaned_content = clean_content(content)
        
        # Write cleaned content back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        print(f"Cleaned {file}")
        
        # If file name contains special characters, rename it
        new_name = re.sub(special_chars, '', file)
        if new_name != file:
            new_path = os.path.join(os.getcwd(), new_name)
            os.rename(file_path, new_path)
            print(f"Renamed {file} to {new_name}")

if __name__ == '__main__':
    main()
    print("File cleanup complete") 