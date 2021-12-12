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
from datetime import date

project = 'PAOS'
author = 'Andrea Bocchieri, Enzo Pascale'
copyright = '2020-{:d}, {}'.format(date.today().year, author)

# The full version, including alpha/beta/rc tags
import os
import sys

# sys.path.insert(0, os.path.abspath('../../'))
current_dir = os.path.dirname(__file__)
target_dir = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.insert(0, target_dir)
print('-------------', target_dir)

from paos.__version__ import __version__

# __version__ = Version()
release = version = str(__version__)

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.doctest',
              'sphinx.ext.todo',
              'sphinx.ext.coverage',
              'sphinx.ext.mathjax',
              'sphinx.ext.viewcode',
              'sphinx.ext.doctest',
              'sphinx.ext.intersphinx',
              'sphinx.ext.autosummary',
              'sphinx.ext.githubpages',
              # 'nbsphinx',
              'matplotlib.sphinxext.plot_directive',
              'sphinx_rtd_theme'
              ]

# -----------------------------------------------------------------------------
# Autodoc
# -----------------------------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
    #    'exclude-members': '__weakref__'
}
napoleon_use_ivar = True
autodoc_typehints = 'description'  # show type hints in doc body instead of signature
autoclass_content = 'both'  # get docstring from class level and init simultaneously

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -----------------------------------------------------------------------------
# Intersphinx configuration
# -----------------------------------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/dev', None),
    'numpy': ('https://numpy.org/devdocs', None),
    'matplotlib': ('https://matplotlib.org', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/reference/', None),
    'astropy': ('https://docs.astropy.org/en/latest/', None),
    'h5py': ('https://docs.h5py.org/en/latest/', None)
}

# -----------------------------------------------------------------------------
# HTML output
# -----------------------------------------------------------------------------

html_theme = 'pydata_sphinx_theme'
html_theme_options = {
    "logo_link": "index",
    "github_url": "https://github.com/arielmission-space/PAOS",
    "collapse_navigation": True,
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["navbar-nav"],
    "navbar_end": ["navbar-icon-links"]
}

html_static_path = ['_static']
html_logo = "_static/paos_logo.jpg"
html_favicon = "_static/paos_logo.ico"

html_show_sourcelink = False


def setup(app):
    app.add_css_file('paos.css')


html_title = "%s v%s Manual" % (project, version)
html_last_updated_fmt = '%b %d, %Y'

html_use_modindex = True
html_copy_source = False
html_domain_indices = False
html_file_suffix = '.html'

htmlhelp_basename = 'paos'

add_module_names = False
add_function_parentheses = False

nbsphinx_execute = 'never'

if 'sphinx.ext.pngmath' in extensions:
    pngmath_use_preview = True
    pngmath_dvipng_args = ['-gamma', '1.5', '-D', '96', '-bg', 'Transparent']

# mathjax_path = "scipy-mathjax/MathJax.js?config=scipy-mathjax"
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML"

plot_html_show_formats = False
plot_html_show_source_link = False
