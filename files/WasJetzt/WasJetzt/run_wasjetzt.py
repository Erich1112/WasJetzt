"""Punct de intrare pentru PyInstaller și pentru rulare din surse: python run_wasjetzt.py"""
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from wasjetzt.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
