"""Add scripts/ to sys.path so hyphenated modules (get-tickets, normalize-tickets) are importable."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
