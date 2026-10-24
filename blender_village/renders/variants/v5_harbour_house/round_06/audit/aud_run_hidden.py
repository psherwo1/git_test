import sys, runpy
a = sys.argv[sys.argv.index("--") + 1:]
sys.argv = [a[0]] + a[1:]
runpy.run_path(a[0], run_name="__main__")
