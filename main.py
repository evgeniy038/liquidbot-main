"""
Bot launcher - allows running with: python main.py
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run
from src.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())