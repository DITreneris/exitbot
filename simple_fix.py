"""
Simple script to fix f-string CSS braces in design_system.py
"""
import re

def fix_design_system():
    # Path to file
    file_path = 'exitbot/frontend/components/design_system.py'
    
    # First make a backup
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(file_path + '.original', 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    print("Backup created at", file_path + '.original')
    
    # Process content line by line
    lines = original_content.split('\n')
    in_f_string = False
    fixed_lines = []
    
    for line in lines:
        # Check if entering an f-string
        if 'f"""' in line:
            in_f_string = True
            fixed_lines.append(line)
        # Check if exiting an f-string
        elif '"""' in line and in_f_string:
            in_f_string = False
            fixed_lines.append(line)
        # Process lines within an f-string
        elif in_f_string:
            # If line has a variable interpolation like {PRIMARY_200}
            if re.search(r'\{[A-Z0-9_]+\}', line):
                # Replace only non-variable curly braces with double curly braces
                # First, temporarily mark variables
                line = re.sub(r'\{([A-Z0-9_]+)\}', r'@@@\1@@@', line)
                # Double all remaining braces
                line = line.replace('{', '{{').replace('}', '}}')
                # Restore variables
                line = re.sub(r'@@@([A-Z0-9_]+)@@@', r'{\1}', line)
                fixed_lines.append(line)
            else:
                # No variables, just double all braces
                fixed_lines.append(line.replace('{', '{{').replace('}', '}}'))
        else:
            # Outside of f-string, keep as is
            fixed_lines.append(line)
    
    # Write the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Fixed file saved at", file_path)

if __name__ == "__main__":
    fix_design_system() 