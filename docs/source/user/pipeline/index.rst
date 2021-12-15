.. _Automatic pipeline:

Automatic pipeline
=======================

Pipeline to run a POP simulation and save the results, given the input dictionary.

Base pipeline
--------------------
This pipeline parses the lens file, performs a diagnostic ray tracing (optional),
sets up the simulation wavelength or produces a user defined wavelength grid,
sets up the optical chain for the POP run automatizing the input of an aberration (optional),
runs the POP in parallel or using a single thread and produces an output where all
(or a subset) of the products are stored. If indicated, the output includes plots.

Example
~~~~~~~~~~~~~

.. code-block:: python

        from paos.paos_pipeline import pipeline

        pipeline(passvalue={'conf':'path/to/conf/file',
                            'output': 'path/to/output/file',
                            'wavelengths': '1.95,3.9',
                            'plot': True,
                            'loglevel': 'debug',
                            'n_jobs': 2,
                            'store_keys': 'amplitude,dx,dy,wl',
                            'return': False})