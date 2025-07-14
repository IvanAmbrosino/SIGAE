#!/usr/bin/env python3
import subprocess

scripts = ["send_test_tle.py"]

for script in scripts:
    print(f"Ejecutando: {script}...")
    subprocess.run(["python", script], check=True)

print("✅ Todos los tests ejecutados correctamente.")