"""
Entrypoint
"""

import logging
from pathlib import Path

from streamlit.web.bootstrap import run


def web():
    logging.basicConfig(level=logging.INFO)
    run(str(Path(__file__).parent / "web.py"), is_hello=False, args=[], flag_options={})
