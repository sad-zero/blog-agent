"""
Entrypoint
"""

import json
import logging
import logging.config
from pathlib import Path

from streamlit.web.bootstrap import run


def web():
    with open("logconfig.json") as fd:
        logconfig = json.load(fd)
        logging.config.dictConfig(logconfig)
    run(str(Path(__file__).parent / "web.py"), is_hello=False, args=[], flag_options={})
