const fs = require('fs');
const path = require('path');

// Files to process
const docFiles = [
    'windows.md',
    'woodenghostsummary.md',
    'updatereadme.md',
    'userguide.txt',
    'implementation_guide.md'
];

// Characters to remove
const specialChars = /[-_\.]/g;

// Process each file
docFiles.forEach(file => {
    const filePath = path.join(__dirname, file);

    // Skip if file doesn't exist
    if (!fs.existsSync(filePath)) {
        console.log(`Skipping ${file} - not found`);
        return;
    }

    // Read file content
    let content = fs.readFileSync(filePath, 'utf8');

    // Clean up file names in content
    content = content.replace(/\w+[-_\.]+\w+\.(js|py|json|md|txt|bat|ps1|sh)/g, match => {
        return match.replace(specialChars, '');
    });

    // Clean up other special characters
    content = content.replace(/Node\.js/g, 'Nodejs');
    content = content.replace(/Eve\.exe/g, 'Eveexe');
    content = content.replace(/\b\w+[-_\.]\w+\b/g, match => {
        return match.replace(specialChars, '');
    });

    // Write cleaned content back to file
    fs.writeFileSync(filePath, content);
    console.log(`Cleaned ${file}`);

    // If file name contains special characters, rename it
    const newName = file.replace(specialChars, '');
    if (newName !== file) {
        const newPath = path.join(__dirname, newName);
        fs.renameSync(filePath, newPath);
        console.log(`Renamed ${file} to ${newName}`);
    }
});

console.log('File cleanup complete'); 