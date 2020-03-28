import re
import sys
from pathlib import Path

import setuptools

setuptools.setup(
    version=re.findall(
        r"""__version__ = "([^"]+)"$""",
        (Path(__file__).parent / "src" / "lsp_json_schema" / "_version.py").read_text(),
    )[0],
)
