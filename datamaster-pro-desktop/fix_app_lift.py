import re

with open('src/gui/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Após current_page.grid() em todos os lugares, precisamos garantir o lift do execution_panel e task_bar
pattern = r'(self\.current_page\.grid\(row=0,\s*column=0,\s*sticky="nsew"\))'
replacement = r'\1\n        if hasattr(self, "execution_panel"):\n            self.execution_panel.lift()\n        if hasattr(self, "task_bar"):\n            self.task_bar.lift()'

new_content = re.sub(pattern, replacement, content)

with open('src/gui/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("LIFT ADICIONADO NO APP.PY")
