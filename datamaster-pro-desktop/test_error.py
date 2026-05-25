import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.tools.consolidador.consolidador import Consolidador
import pandas as pd

c = Consolidador()
df1 = pd.DataFrame({"nome": ["João", "Maria"], "valor": [100, 200]})
df2 = pd.DataFrame({"nome": ["Pedro", "Ana"], "valor": [300, 400]})
file1 = "file1.xlsx"
file2 = "file2.xlsx"
df1.to_excel(file1, index=False)
df2.to_excel(file2, index=False)

res = c.consolidate([file1, file2], "output.xlsx")
print("RESULT:", res)

import os
for f in [file1, file2, "output.xlsx"]:
    try:
        if os.path.exists(f):
            os.remove(f)
    except:
        pass
