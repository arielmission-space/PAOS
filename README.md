# `PAOS`
The Physical `Ariel` Optics Simulator

## How to install 

`PAOS` is compatible with Python 3.8.

To install from source, clone the repository and move inside the directory. 
Then use pip as 
    
    pip install .

## How to build the documentation

### html documentation

To build the html documentation, Sphinx is needed. To install the dependencies run

    pip install sphinx sphinxcontrib-jsmath sphinx_rtd_theme sphinx_markdown_tables

Then move into the `docs` directory and run

    make html

The documentation will be produced into the `build/html` directory inside `docs`. 
Open `index.html` to read the documentation.

### pdf documentation

To build the pdf version of the documentation, Sphinx is needed. To install the dependencies run

    pip install sphinx sphinxcontrib-jsmath sphinx_rtd_theme sphinx_markdown_tables

Then move into the `docs` directory and run

    make latexpdf

Doing so, the documentation is compiled by `pdflatex` and stored into the `build/latex` directory inside `docs`. 
Open `paos.pdf` to read the documentation.

Please refer to the [official sphinx documentation](https://www.sphinx-doc.org/en/master/usage/configuration.html#latex-options) 
for a different LaTex compiler.