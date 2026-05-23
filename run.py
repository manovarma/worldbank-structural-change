"""
run.py — single entry point
Runs data collection then analysis in sequence.
Usage: python run.py
"""

import subprocess
import sys


def run(script: str):
    print(f"\n{'='*60}")
    print(f"  Running: {script}")
    print(f"{'='*60}\n")
    result = subprocess.run([sys.executable, script], check=True)
    return result


if __name__ == "__main__":
    run("collect.py")
    run("analyse.py")
    print("\n✓ All done. Outputs in data/ and findings.md")
