# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
# -- Project information -----------------------------------------------------
import os
import sys
from datetime import date

# The full version, including alpha/beta/rc tags
# sys.path.insert(0, os.path.abspath('../../'))
current_dir = os.path.dirname(__file__)
target_dir = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.insert(0, target_dir)
print("-------------", target_dir)

from paos import __version__, __author__, __pkg_name__

# __version__ = Version()
release = version = str(__version__)

project = __pkg_name__.upper()
copyright = "2020-{:d}, {}".format(date.today().year, __author__)

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
    # 'nbsphinx',
    "jupyter_sphinx",
    "matplotlib.sphinxext.plot_directive",
    "sphinx_rtd_theme",
    "sphinx_markdown_tables",
]

# -----------------------------------------------------------------------------
# Autodoc
# -----------------------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    #    'exclude-members': '__weakref__'
}
napoleon_use_ivar = True
autodoc_typehints = (
    "description"  # show type hints in doc body instead of signature
)
autoclass_content = (
    "both"  # get docstring from class level and init simultaneously
)

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]
# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -----------------------------------------------------------------------------
# Intersphinx configuration
# -----------------------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/dev", None),
    "numpy": ("https://numpy.org/devdocs", None),
    "matplotlib": ("https://matplotlib.org", None),
    "scipy": ("https://scipy.github.io/devdocs/", None),
    "astropy": ("https://docs.astropy.org/en/latest/", None),
    "h5py": ("https://docs.h5py.org/en/latest/", None),
}

# -----------------------------------------------------------------------------
# HTML output
# -----------------------------------------------------------------------------

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named 'default.css' will overwrite the builtin 'default.css'.

# Required theme setup
html_theme = "sphinx_material"

# Set link name generated in the top bar.
html_title = "{} v{} Manual".format(project, version)
html_last_updated_fmt = "%b %d, %Y"

# Material theme options (see theme.conf for more information)
html_theme_options = {
    # Set the name of the project to appear in the navigation.
    "nav_title": "PAOS",
    # Specify a base_url used to generate sitemap.xml. If not
    # specified, then no sitemap will be built.
    "base_url": "https://github.com/arielmission-space/PAOS",
    # Set the color and the accent color
    "color_primary": "blue-grey",
    "color_accent": "light-blue",
    # Set the repo location to get a badge with stats
    "repo_url": "https://github.com/arielmission-space/PAOS",
    "repo_name": "Git repo",
    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": 2,
    # If False, expand all TOC entries
    "globaltoc_collapse": True,
    # If True, show hidden TOC entries
    "globaltoc_includehidden": False,
    # 'html_prettify': True,
}

html_static_path = ["_static"]
html_logo = "_static/paos_logo.svg"

html_show_sourcelink = False

html_additional_pages = {
    "index": "index.html",
    "user/index": "user_index.html",
    "ariel/index": "ariel.html",
}

html_use_modindex = True
html_copy_source = False
html_domain_indices = False
html_file_suffix = ".html"

htmlhelp_basename = "paos"

html_sidebars = {
    "**": [
        "logo-text.html",
        "globaltoc.html",
        "localtoc.html",
        "searchbox.html",
    ]
}

add_module_names = False
add_function_parentheses = False

nbsphinx_execute = "never"

if "sphinx.ext.pngmath" in extensions:
    pngmath_use_preview = True
    pngmath_dvipng_args = ["-gamma", "1.5", "-D", "96", "-bg", "Transparent"]

# mathjax_path = "scipy-mathjax/MathJax.js?config=scipy-mathjax"
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"

plot_html_show_formats = False
plot_html_show_source_link = False


html_css_files = ["_static/paos.css"]

numfig = True

# -- Options for LaTeX output ---------------------------------------------

with open("_templates/latexstyling.tex", "r+") as f:
    PREAMBLE = f.read()

with open("_templates/latexstyling_maketitle.tex", "r+") as f:
    MAKETITLE = f.read()

latex_engine = "pdflatex"
latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    "papersize": "a4paper",
    "releasename": " ",
    # Sonny, Lenny, Glenn, Conny, Rejne, Bjarne and Bjornstrup
    "fncychap": "\\usepackage[Glenn]{fncychap}",
    # 'fncychap': '\\usepackage{fncychap}',
    "fontpkg": "\\usepackage{amsmath,amsfonts,amssymb,amsthm}",
    "figure_align": "htbp",
    # The font size ('10pt', '11pt' or '12pt').
    "pointsize": "11pt",
    # Additional stuff for the LaTeX preamble.
    "preamble": PREAMBLE,
    "maketitle": MAKETITLE,
    # Latex figure (float) alignment
    #
    "sphinxsetup": "hmargin={0.7in,0.7in}, vmargin={1in,1in}, \
        verbatimwithframe=true, \
        TitleColor={rgb}{0,0,0}, \
        HeaderFamily=\\rmfamily\\bfseries, \
        InnerLinkColor={rgb}{0,0,1}, \
        OuterLinkColor={rgb}{0,0,1}",
    "tableofcontents": " ",
}

latex_logo = "_static/paos.jpg"

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, report, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "paos.tex",
        "PAOS Manual",
        "Andrea Bocchieri, Enzo Pascale",
        "manual",
    )
]

# This will ensure that your package is importable by any IPython kernels, as they will inherit the environment
# variables from the main Sphinx process.
package_path = os.path.abspath("../..")
os.environ["PYTHONPATH"] = ":".join(
    (package_path, os.environ.get("PYTHONPATH", ""))
)
