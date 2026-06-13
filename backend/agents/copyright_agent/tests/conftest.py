# This file is responsible for test import path setup ko handle karne ke liye.
# Yahan local package access ke liye project root manage kiya jata hai.

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
