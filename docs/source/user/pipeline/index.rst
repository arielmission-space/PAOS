.. _Automatic pipeline:

Automatic pipeline
=======================

Pipeline to run a POP simulation and save the results, given an input dictionary with selected options.

Base pipeline
--------------------
This pipeline

#. Sets up the logger;
#. Parses the lens file;
#. Performs a diagnostic ray tracing (optional);
#. Sets up the simulation wavelength or produces a user defined wavelength grid;
#. Sets up the optical chain for the POP run automatizing the input of an aberration (optional);
#. Runs the POP in parallel or using a single thread;
#. Produces an output where all (or a subset) of the products are stored;
#. If indicated, the output includes plots.

Example
~~~~~~~~~~~~~

Code example to the method :func:`~paos.core.pipeline.pipeline` to run a simulation for two wavelengths,
:math:`w_1 = 3.9` and :math:`w_1 = 7.8` micron, using the configuration file for AIRS-CH1.

Using the option 'wl_grid' instead of 'wavelengths', the user can define the minimum wavelength, the maximum wavelength
and the spectral resolution. `PAOS` will then automatically create a wavelength grid to perform the POP.

.. code-block:: python

        from paos.core.pipeline import pipeline

        pipeline(passvalue={'conf':'path/to/ini/file',
                            'output': 'path/to/hdf5',
                            'wavelengths': '3.9,7.8',
                            # or 'wl_grid': '3.9,7.8,5'
                            'plot': True,
                            'loglevel': 'info',
                            'n_jobs': 2,
                            'store_keys': 'amplitude,dx,dy,wl',
                            'return': False})
