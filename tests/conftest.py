"""
conftest.py – Pytest configuration.
Adds the project root to sys.path so all modules are importable.
"""

import sys
import os

# Project root = one level above /tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
