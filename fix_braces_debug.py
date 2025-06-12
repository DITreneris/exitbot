import re
import os

def fix_braces_in_file(filename):
    print(f"Processing {filename}...")
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"Error: File {filename} does not exist!")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Successfully read {len(content)} characters from file")
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # First, let's directly search for suspect patterns
    print("Searching for problematic patterns...")
    
    # Look for single unmatched braces
    unmatched_open = re.findall(r'(?<!\{)\{(?!\{)(?![A-Z0-9_]+\})', content)
    unmatched_close = re.findall(r'(?<!\})\}(?!\})(?<!\{[A-Z0-9_]+)', content)
    
    print(f"Found {len(unmatched_open)} unmatched open braces and {len(unmatched_close)} unmatched close braces")
    
    # Look for keyframes which often have brace issues
    keyframes = re.findall(r'@keyframes\s+[a-zA-Z0-9_-]+\s*\{', content)
    print(f"Found {len(keyframes)} keyframe definitions")
    
    # Simple fix - just double all non-variable braces
    def protect_vars(match):
        return f"PROTECTED_VAR_{match.group(1)}_PROTECTED"
    
    # First protect variable interpolations like {PRIMARY_600}
    protected = re.sub(r'\{([A-Z0-9_]+)\}', protect_vars, content)
    
    # Now double all braces
    doubled = protected.replace('{', '{{').replace('}', '}}')
    
    # Restore variable interpolations
    fixed_content = re.sub(r'PROTECTED_VAR_([A-Z0-9_]+)_PROTECTED', r'{\1}', doubled)
    
    # Count how many braces we fixed
    original_single_braces = content.count('{') + content.count('}') - 2 * (content.count('{{') + content.count('}}'))
    fixed_single_braces = fixed_content.count('{') + fixed_content.count('}') - 2 * (fixed_content.count('{{') + fixed_content.count('}}'))
    
    print(f"Original single braces: {original_single_braces}, After fixing: {fixed_single_braces}")
    
    # Write back to a new file to be safe
    fixed_filename = filename + '.fixed'
    try:
        with open(fixed_filename, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed content written to {fixed_filename}")
        
        print(f"Now backing up original file and replacing it with fixed version")
        # Backup original file
        backup_filename = filename + '.bak'
        os.rename(filename, backup_filename)
        # Move fixed file to original name
        os.rename(fixed_filename, filename)
        print(f"Original backed up to {backup_filename}, fixed file is now {filename}")
    except Exception as e:
        print(f"Error writing file: {e}")

# Fix the design_system.py file
fix_braces_in_file('exitbot/frontend/components/design_system.py') 