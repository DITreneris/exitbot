"""
Script to fix CSS braces in f-strings
For design_system.py
"""

import os

def fix_file(filename):
    print(f"Processing {filename}...")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Read {len(content)} bytes from file")
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # First, analyze the file
    problem_patterns = [
        "0% {", "25% {", "50% {", "75% {", "100% {",
        "@keyframes", ".dashboard-card {", "section[data-testid=\"stSidebar\"] {",
        "from {", "to {"
    ]
    
    for pattern in problem_patterns:
        count = content.count(pattern)
        if count > 0:
            print(f"Found {count} occurrences of '{pattern}'")
    
    # Create a backup
    backup_file = filename + ".backup"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created backup at {backup_file}")
    
    # Replace problematic patterns with doubles
    replacements = [
        ("0% {", "0% {{"),
        ("25% {", "25% {{"),
        ("50% {", "50% {{"),
        ("75% {", "75% {{"),
        ("100% {", "100% {{"),
        ("from {", "from {{"),
        ("to {", "to {{"),
        (".dashboard-card {", ".dashboard-card {{"),
        ("section[data-testid=\"stSidebar\"] {", "section[data-testid=\"stSidebar\"] {{"),
        ("}", "}}"),
    ]
    
    fixed_content = content
    for old, new in replacements:
        fixed_content = fixed_content.replace(old, new)
    
    # Now fix any double replacements of variable interpolations
    var_patterns = ["PRIMARY_", "NEUTRAL_", "SUCCESS_", "WARNING_", "ERROR_", 
                   "FONT_", "SPACING_", "BORDER_RADIUS_", "SHADOW_", "FONT_WEIGHT_"]
    
    for var_prefix in var_patterns:
        # Fix over-replaced variable interpolations
        for i in range(50):  # Check common indices 0-49
            fixed_content = fixed_content.replace(f"{{{{{var_prefix}{i}}}}}}}", f"{{{var_prefix}{i}}}")
        
        # Also fix common suffixes
        suffixes = ["XS", "SM", "MD", "LG", "XL", "2XL", "3XL", "4XL", "FULL", "BASE", 
                   "NORMAL", "MEDIUM", "SEMIBOLD", "BOLD", "TIGHT", "RELAXED"]
        for suffix in suffixes:
            fixed_content = fixed_content.replace(f"{{{{{var_prefix}{suffix}}}}}}}", f"{{{var_prefix}{suffix}}}")
    
    # Write the fixed content back to the file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Successfully fixed and saved {filename}")
    except Exception as e:
        print(f"Error writing file: {e}")

# Process the design system file
fix_file('exitbot/frontend/components/design_system.py') 