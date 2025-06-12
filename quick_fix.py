"""
Quick fix for the keyframes animation in design_system.py
"""

def fix_keyframes():
    file_path = 'exitbot/frontend/components/design_system.py'
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a backup
    with open(file_path + '.keyframes_backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created backup at {file_path}.keyframes_backup")
    
    # Fix the keyframes section specifically 
    keyframes_original = '''
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }'''
    
    keyframes_fixed = '''
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}'''
    
    # Replace the keyframes section
    if keyframes_original in content:
        content = content.replace(keyframes_original, keyframes_fixed)
        print("Found and fixed the keyframes section")
    else:
        print("Couldn't find the exact keyframes section, trying a more general approach")
        # More targeted replacements
        content = content.replace('@keyframes fadeIn {', '@keyframes fadeIn {{')
        content = content.replace('from {', 'from {{')
        content = content.replace('to {', 'to {{')
        # Close the braces properly
        content = content.replace('transform: translateY(10px); }', 'transform: translateY(10px); }}')
        content = content.replace('transform: translateY(0); }', 'transform: translateY(0); }}')
        content = content.replace('}\n\n    .animate-fade-in', '}}\n\n    .animate-fade-in')
    
    # Save the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed file saved at {file_path}")

if __name__ == "__main__":
    fix_keyframes() 