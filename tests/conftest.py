"""
Pytest configuration and shared fixtures for mailprune tests.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import mailprune
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
