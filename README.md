# ``PAOS``

[![PyPI version](https://badge.fury.io/py/paos.svg)](https://badge.fury.io/py/paos)
[![GitHub version](https://badge.fury.io/gh/arielmission-space%2FPAOS.svg)](https://badge.fury.io/gh/arielmission-space%2FPAOS)
[![Downloads](https://static.pepy.tech/badge/paos)](https://pepy.tech/project/paos)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Documentation Status](https://readthedocs.org/projects/paos/badge/?version=latest)](https://paos.readthedocs.io/en/latest/?badge=latest)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md)

## Introduction

``PAOS``, the Physical Optics Simulator, is a fast, modern, and reliable Python package for Physical Optics studies.

It implements Physical Optics Propagation in Fresnel approximation and paraxial ray tracing to analyze complex waveform propagation through both generic and off-axes optical systems.

It handles diffractive materials and can implement wavefront aberrations as Zernike polynomials, orthonormal polynomials, or grid sags.

## Table of contents

- [``PAOS``](#paos)
  - [Introduction](#introduction)
  - [Table of contents](#table-of-contents)
  - [How to install](#how-to-install)
    - [Install from PyPI](#install-from-pypi)
    - [Install from source code](#install-from-source-code)
      - [Test your installation](#test-your-installation)
  - [Documentation](#documentation)
    - [Build the html documentation](#build-the-html-documentation)
    - [Build the pdf documentation](#build-the-pdf-documentation)
  - [How to contribute](#how-to-contribute)
  - [How to cite](#how-to-cite)

## How to install

Instructions on how to install ``PAOS``.

### Install from PyPI

``PAOS`` is available on PyPI and can be installed via pip as

    pip install paos

### Install from source code

``PAOS`` is compatible (tested) with Python 3.9+

To install from source, clone the [repository](https://github.com/arielmission-space/PAOS/) and move inside the directory.

Then use `pip` as

    pip install .

#### Test your installation

Try importing ``PAOS`` as

    python -c "import paos; print(paos.__version__)"

Or running ``PAOS`` itself with the `help` flag as

    paos -h

Or the Graphical User Interface with the `help` flag as

    paos_gui -h

If there are no errors then the installation was successful!

## Documentation

``PAOS`` comes with an extensive documentation, which can be built using Sphinx.
The documentation includes a tutorial, a user guide and a reference guide.

To build the documentation, install the needed packages first via `poetry`:

    pip install poetry
    poetry install --with docs

### Build the html documentation

To build the html documentation, move into the `docs` directory and run

    make html

The documentation will be produced into the `build/html` directory inside `docs`.
Open `index.html` to read the documentation.

### Build the pdf documentation

To build the pdf, move into the `docs` directory and run

    make latexpdf

The documentation will be produced into the `build/latex` directory inside `docs`.
Open `paos.pdf` to read the documentation.

The developers use `pdflatex`; if you have another compiler for LaTex, please refer to [sphinx documentation](https://www.sphinx-doc.org/en/master/usage/configuration.html#latex-options).

## How to contribute

You can contribute to ``PAOS`` by reporting bugs, suggesting new features, or contributing to the code itself.
If you wish to contribute to the code, please follow the steps described in the documentation under `Contribution Guidelines`.

## How to cite

```bibtex
@INPROCEEDINGS{2024SPIE13092E..4KB,
       author = {{Bocchieri}, Andrea and {Mugnai}, Lorenzo V. and {Pascale}, Enzo},
        title = "{PAOS: a fast, modern, and reliable Python package for physical optics studies}",
    booktitle = {Space Telescopes and Instrumentation 2024: Optical, Infrared, and Millimeter Wave},
         year = 2024,
       editor = {{Coyle}, Laura E. and {Matsuura}, Shuji and {Perrin}, Marshall D.},
       series = {Society of Photo-Optical Instrumentation Engineers (SPIE) Conference Series},
       volume = {13092},
        month = aug,
          eid = {130924K},
        pages = {130924K},
          doi = {10.1117/12.3018333},
       adsurl = {https://ui.adsabs.harvard.edu/abs/2024SPIE13092E..4KB},
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}
}
```
