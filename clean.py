import os
import re

files_to_clean = [
    'windows.md',
    'woodenghostsummary.md',
    'updatereadme.md',
    'userguide.txt',
    'implementation_guide.md'
]

def clean_text(text):
    # Replace common special characters
    text = text.replace('Node.js', 'Nodejs')
    text = text.replace('Eve.exe', 'Eveexe')
    text = text.replace('-', '')
    text = text.replace('_', '')
    text = re.sub(r'\.(?!md|txt|js|py|json|bat|ps1|sh)', '', text)
    return text

for filename in files_to_clean:
    if os.path.exists(filename):
        print(f"Processing {filename}")
        
        # Read content
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean content
        cleaned = clean_text(content)
        
        # Write back
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        # Clean filename
        new_name = clean_text(filename)
        if new_name != filename:
            os.rename(filename, new_name)
            print(f"Renamed {filename} to {new_name}")
    else:
        print(f"File not found: {filename}")

print("Cleanup complete") 