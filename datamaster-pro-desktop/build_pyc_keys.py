"""
Build: python build_pyc_keys.py
"""
import py_compile
import os

_J = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5dHB1ZWZwaXN2bWx4bXFrYmZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgxMTEzNTQsImV4cCI6MjA5MzY4NzM1NH0.ExGFv5Ltv8xI2Ajkm8lvQjuAor_CG7hW--o4HCGKF84"
_S = "f9c0ef564f87b5a3bb502a2d6a8dc05b"

_C = 8
_JC = [_J[i:i+_C] for i in range(0, len(_J), _C)]
_SC = [_S[i:i+_C] for i in range(0, len(_S), _C)]
_DIR = os.path.join(os.path.dirname(__file__), "src", "utils", "_net")


def _n(i):
    """gera nome de modulo: _a, _b, ..., _y, _ba, _bb, ... (skip _z)"""
    if i < 25:
        return f"_{chr(97+i)}"
    return f"_{chr(97+((i+1)//26-1))}{chr(97+(i+1)%26)}"


def _mk(c, n, idx):
    src = f'_v={repr(list(c.encode()))}\ndef _x{idx}():\n    return bytes(_v)\n'
    py = os.path.join(_DIR, f"{n}.py")
    pyc = os.path.join(_DIR, f"{n}.pyc")
    with open(py, "w") as f:
        f.write(src)
    py_compile.compile(py, cfile=pyc, doraise=True)
    os.remove(py)


def _ldr():
    nj = len(_JC)
    sj = ",".join(f'("{_n(i)}","_x{i}")' for i in range(nj))
    ss = ",".join(f'("{_n(nj+i)}","_x{nj+i}")' for i in range(len(_SC)))
    lines = [
        "import importlib as _i",
        "_a=None",
        "_b=None",
        "def _f():",
        "    global _a",
        "    if _a is not None: return _a",
        "    m=[]",
        f"    for n,g in [{sj}]:",
        '        mod=_i.import_module("src.utils._net."+n)',
        "        m.append(getattr(mod,g)())",
        '    _a=b"".join(m).decode()',
        "    return _a",
        "def _g():",
        "    global _b",
        "    if _b is not None: return _b",
        "    m=[]",
        f"    for n,g in [{ss}]:",
        '        mod=_i.import_module("src.utils._net."+n)',
        "        m.append(getattr(mod,g)())",
        '    _b=b"".join(m).decode()',
        "    return _b",
    ]
    py = os.path.join(_DIR, "_z.py")
    pyc = os.path.join(_DIR, "_z.pyc")
    with open(py, "w") as f:
        f.write("\n".join(lines) + "\n")
    py_compile.compile(py, cfile=pyc, doraise=True)
    os.remove(py)


if __name__ == "__main__":
    for f in os.listdir(_DIR):
        if f.endswith((".pyc", ".pyd")) and f != "__init__.py":
            os.remove(os.path.join(_DIR, f))

    for i, c in enumerate(_JC):
        _mk(c, _n(i), i)
    nj = len(_JC)
    for i, c in enumerate(_SC):
        _mk(c, _n(nj + i), nj + i)
    _ldr()

    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    for k in list(sys.modules.keys()):
        if "_net" in k:
            del sys.modules[k]

    from src.utils._net._z import _f, _g
    assert _f() == _J
    assert _g() == _S
    print("OK")
