#!/usr/bin/env python3
import importlib.metadata as m, shutil, sys, platform, subprocess

print(f"Python   : {sys.executable}")
print(f"Version  : {platform.python_version()}")
print()

pkgs = ["pytest", "flake8", "mypy", "pylint", "bandit"]
for p in pkgs:
    path = shutil.which(p) or "binary not on PATH"
    try:
        ver = m.version(p)
    except m.PackageNotFoundError:
        ver = "not installed"
    print(f"{p:<7} | {ver:<14} | {path}")