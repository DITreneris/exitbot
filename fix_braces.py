import re

def fix_braces_in_file(filename):
    print(f"Processing {filename}...")
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all f-strings
    pattern = r'(f""")(.*?)(""")'
    
    def fix_fstring_content(match):
        fstring_start = match.group(1)
        fstring_content = match.group(2)
        fstring_end = match.group(3)
        
        # First, protect variable interpolations
        protected = re.sub(r'\{([A-Z0-9_]+)\}', r'PROTECTED_VAR_\1_PROTECTED', fstring_content)
        
        # Now double all braces
        doubled = protected.replace('{', '{{').replace('}', '}}')
        
        # Restore variable interpolations
        restored = re.sub(r'PROTECTED_VAR_([A-Z0-9_]+)_PROTECTED', r'{\1}', doubled)
        
        return fstring_start + restored + fstring_end
    
    # Apply fix to all f-strings
    fixed_content = re.sub(pattern, fix_fstring_content, content, flags=re.DOTALL)
    
    # Count replacements
    original_braces = len(re.findall(r'(?<!\{)\{(?!\{)|(?<!\})\}(?!\})', content))
    fixed_braces = len(re.findall(r'(?<!\{)\{(?!\{)|(?<!\})\}(?!\})', fixed_content))
    
    print(f"Found {original_braces} single braces, {fixed_braces} remain after fixing")
    
    # Write back to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed braces in {filename}")

# Fix the design_system.py file
fix_braces_in_file('exitbot/frontend/components/design_system.py') 