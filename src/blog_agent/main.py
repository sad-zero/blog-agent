"""
Entrypoint
"""

from pathlib import Path

from streamlit.web.bootstrap import run


def web():
    run(str(Path(__file__).parent / "web.py"), is_hello=False, args=[], flag_options={})
