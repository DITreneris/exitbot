"""
Direct fix for the design_system.py file
"""

def fix_design_system():
    # Path to the file
    file_path = 'exitbot/frontend/components/design_system.py'
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a backup
        with open(file_path + '.final_backup', 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Created backup at", file_path + '.final_backup')
        
        # Replace keyframes section which is causing the error
        lines = content.split('\n')
        fixed_lines = []
        
        # Define replacement pairs for CSS braces in strings
        replacements = [
            ("@keyframes fadeIn {", "@keyframes fadeIn {{"),
            ("from { ", "from {{ "),
            ("to { ", "to {{ "),
            ("opacity: 0; transform: translateY(10px); }", "opacity: 0; transform: translateY(10px); }}"),
            ("opacity: 1; transform: translateY(0); }", "opacity: 1; transform: translateY(0); }}"),
            ("}\n\n    .animate-fade-in {", "}}\n\n    .animate-fade-in {{"),
            ("animation: fadeIn 0.5s ease forwards;\n    }", "animation: fadeIn 0.5s ease forwards;\n    }}"),
            (".screen-reader-only {", ".screen-reader-only {{"),
            ("border-width: 0;\n    }", "border-width: 0;\n    }}"),
        ]
        
        # Apply all replacements
        for old, new in replacements:
            content = content.replace(old, new)
            
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Fixed file saved at", file_path)
        print("Try running your app again now!")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fix_design_system() 