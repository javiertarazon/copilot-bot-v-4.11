
import sys
import os
import importlib
import traceback

# Add project root (descarga_datos) to path
# Tests are in descarga_datos/tests, so we go up one level
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def check_module(module_name):
    print(f"Checking {module_name}...", end=" ")
    try:
        importlib.import_module(module_name)
        print("✅ OK")
        return True
    except Exception as e:
        print("❌ FAIL")
        print(traceback.format_exc())
        return False

print("--- SYSTEM MODULE INTEGRITY CHECK ---")
modules_to_check = [
    "risk_management.risk_management",
    "core.downloader",
    "strategies.base_strategy",
    "utils.logger",
    "config.config_loader"
]

passed = 0
for m in modules_to_check:
    if check_module(m):
        passed += 1

print(f"\nSummary: {passed}/{len(modules_to_check)} modules loaded successfully.")
