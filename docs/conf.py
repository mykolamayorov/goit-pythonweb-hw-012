import os
import sys
from datetime import datetime

# щоб sphinx бачив пакет app/
sys.path.insert(0, os.path.abspath(".."))

project = "goit-pythonweb-hw-012"
author = "Mykola Mayorov"
copyright = f"{datetime.now().year}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# autodoc / napoleon
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = False