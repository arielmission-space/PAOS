.. _Input system:

=======================
Input system
=======================

`PAOS` has a generic input system that mimics the Zemax OpticStudio interface to allow the user
expert in Computer Aided Design (CAD) modeling to simulate also optical systems other than `Ariel`.

For instance, `PAOS` is used to simulate the optical performance of the stratospheric balloon-borne
experiment EXCITE
(`Tucker et al., The Exoplanet Climate Infrared TElescope (EXCITE) (2018) <https://doi.org/10.1117/12.2314225>`_).

Configuration file
----------------------------

The configuration file is an Excel spreadsheet containing three data sheets named ‘general’, ‘LD’ and ‘field’.
‘general’ has the simulation wavelength, grid size and zoom, defined as the ratio of grid size to initial
beam size in unit of pixel. ‘LD’ is the lens data and contains the sequence of surfaces for the simulation.
Supported surfaces include Coordinate Break, Standard, Obscuration, Paraxial Lens, Prism, Slit and Zernike.

Read configuration file
-------------------------

Given the input file name, `PAOS` implements a function that opens it and returns the simulation parameters.

Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

        from paos.paos_parseconfig import ReadConfig
        simulation_parameters = ReadConfig('path/to/conf/file')

Parse configuration file
-------------------------

This is used by another `PAOS` function, which parses the simulation parameters and returns the input pupil
diameter along with three dictionaries for the POP simulation: the general parameters, the input fields and
the optical chain.

Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

        from paos.paos_parseconfig import ParseConfig
        pupil_diameter, general, fields, optical_chain = ParseConfig('path/to/conf/file')
