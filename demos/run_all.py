"""3つのデモを順に実行する。  python demos/run_all.py [--fast]"""
import os
import runpy
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
for i, name in enumerate(["harness_demo", "loop_demo", "graph_demo"]):
    runpy.run_path(os.path.join(here, f"{name}.py"), run_name="__main__")
    if i < 2 and "--fast" not in sys.argv:
        input("\n[Enter] で次のデモへ ")
