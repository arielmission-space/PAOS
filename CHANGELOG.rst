===========
Changelog
===========

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog (keepachangelog_), and this project adheres to Semantic Versioning (semver_).

Unreleased
====================

Changed
^^^^^^^
- Simplified ``paos_gui`` options by removing the unused ``--logger`` flag; only the debug toggle remains documented.
- CLI booleans now use paired flags: ``--save/--no-save`` and ``--plot/--no-plot`` for clearer UX; updated help text to explicitly mention the ``--no-*`` opt-outs.
- Updated Quickstart docs to reflect the new paired flags and clarify how to disable saving/plotting via ``--no-save`` and ``--no-plot``.
- Migrated CLI to ``rich-click`` for improved UX.
- Moved deprecated Excel configuration parser and sample files to ``retired/``.
- Relaxed ``marimo`` dependency to allow any version.
- Cleaned up imports and formatting across modules.

Fixed
^^^^^^^
- Corrected logger option naming in GUI/CLI; standardized variable name to ``logfile``.
- CLI now resolves relative/filename-only outputs before logging, avoiding attempts to write ``/configuration_name.log`` on read-only roots.

0.0.2 [15/09/2021]
---------------------

Setting up new ``PAOS`` repository

0.0.2.1 [20/10/2021]
----------------------

First documented ``PAOS`` release

0.0.3 [23/12/2021]
--------------------

Added
^^^^^^^^^
- Added support for optical materials

0.0.4 [22/01/2022]
--------------------

Changed
^^^^^^^^^
- Changed configuration file to .ini

1.0.0 [01/07/2023]
--------------------

``PAOS`` production ready

1.0.1 [10/01/2024]
--------------------

``PAOS`` documented on readthedocs

[Released_]
====================

1.0.2-alpha.0 [10/01/2024]
--------------------

``PAOS`` lives on PyPI

Changed
^^^^^^^^^
- Changed setup.cfg file to pyproject.toml

1.0.2 [10/01/2024]
--------------------

``PAOS`` production ready

1.0.3-post1 [11/03/2024]
--------------------

Added
^^^^^
- Implemented PSD/SR
- References to the Zernike ordering

Fixed
^^^^^
- optical chain dependency on wavelength in paos.core.pipeline

1.1.0 [22/06/2024]
--------------------

Fixed
^^^^^
- Zernike covariance (hermitianity)

Added
^^^^^
- class PolyOrthoNorm (based on Zernike)

1.0.3-post1 [11/03/2024]
--------------------

Added
^^^^^
- Implemented PSD/SR

1.1.1 [24/10/2024]
--------------------

Added
^^^^^
- Implemented Grid Sag

Fixed
^^^^^
- PySimpleGui version set to before v5.0

1.1.2 [26/10/2024]
--------------------

Changed
^^^^^^^
- Implemented ``loguru`` logger

1.2.1 [28/10/2024]
--------------------

Changed
^^^^^^^
- Implemented GUI v2.0

1.2.2 [28/10/2024]
--------------------

Changed
^^^^^^^
- Enabled ortho-normal polynomials to be used in ``PAOS`` run

1.2.3 [05/11/2024]
--------------------

Added
^^^^^^^
- Implemented Wavefront Editor in GUI

1.2.4 [07/11/2024]
--------------------

Changed
^^^^^^^
- Refactored Lens Editor in GUI

1.2.5 [07/11/2024]
--------------------

Added
^^^^^^^
- Missing docs in Aberration section

Changed
^^^^^^^
- Refactored docs

1.2.6 [15/12/2024]
--------------------

Added
^^^^^^^
- Marimo notebook/app for PAOS demo
- Material and PSD apps

Changed
^^^^^^^
- Deprecated Python 3.8
- Updated dependencies management with Poetry

1.2.7 [21/01/2025]
--------------------

Fixed
^^^^^^^
- Fixed f-string in plot function
- Fixed documentation dependencies

1.2.8 [19/04/2025]
--------------------

Changed
^^^^^^^
- Refactored WFO class sag handling
- Updated lens configuration parameters and grid size handling
- Improved logging system

Added
^^^^^^^
- Grid sag sizing feature

1.2.9-rc0 [21/04/2025]
--------------------

Added
^^^^^^^
- Contributor Covenant Code of Conduct
- Developer Guide in documentation

1.2.9 [18/07/2025]
--------------------

Added
^^^^^^^
- README section for Interactive ``marimo`` notebooks.

Changed
^^^^^^^
- Improved grid-sag handling: redefined ``nx``/``ny`` as sag shape, rescaled by physical sizes, handled half-pixel differences.
- Updated ``jinja2`` dependency to ``3.1.6``.
- Updated project badges and lockfile metadata.

Fixed
^^^^^^^
- Wavefront calculation in Zernike and ``grid_sag`` by applying mask fill inside the phase exponent to avoid cropping outside masks.
- Fixed links to the Developer Guide in the documentation.
- Removed stray debug prints.

1.2.10 [03/09/2025]
--------------------

Added
^^^^^^^
- ``save`` option in the pipeline and main entry-point for output control.
- Logging to file; refactored debug messages to f-strings.
- Return value now includes propagator type for traceability.

Changed
^^^^^^^
- Allowed grid sizes expanded to include ``2048`` and ``4096``.
- Quickstart and examples updated to cover the ``save`` option.


.. _Released: https://github.com/arielmission-space/PAOS/
.. _keepachangelog: https://keepachangelog.com/en/1.0.0/
.. _semver: https://semver.org/spec/v2.0.0.html
