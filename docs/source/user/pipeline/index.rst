.. _Pipeline:

Pipeline
=======================

Pipeline to run a POP simulation and save the results, given an input dictionary with selected options.

Base pipeline
--------------------
This pipeline

#. Sets up the logger;
#. Parses the lens file;
#. Performs a diagnostic ray tracing (optional);
#. Sets up the optical chain for the POP run automatizing the input of an aberration (optional);
#. Runs the POP in parallel or using a single thread;
#. Produces an output where all (or a subset) of the products are stored;
#. If indicated, the output includes plots.

Example
~~~~~~~~~~~~~

Code example to the method :func:`~paos.core.pipeline.pipeline` to run a simulation using a configuration file.

.. code-block:: python

        from paos.core.pipeline import pipeline

        pipeline(passvalue={'conf':'path/to/ini/file',
                            'output': 'path/to/hdf5',
                            'plot': True,
                            'loglevel': 'info',
                            'n_jobs': 2,
                            'store_keys': 'amplitude,dx,dy,wl',
                            'return': False})
