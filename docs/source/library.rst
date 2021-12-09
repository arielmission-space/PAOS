================
Library
================

Library with the main PAOS functions and an automatic pipeline,
with self-consistent examples to run in python shell or jupyter-lab interface.

Prepare the run
------------------------------------

To prepare the run, please follow these steps:
    - Add to PYTHONPATH the path to local libraries.
    - Define configuration lens file to use.
    - Define output folder and output file name.

Parse lens file
-----------------------------------
.. autofunction:: paos.paos_parseconfig.ReadConfig
    :noindex:
.. autofunction:: paos.paos_parseconfig.ParseConfig
    :noindex:

ABCD matrix
-----------------------------------
.. autofunction:: paos.paos_abcd.ABCD
    :noindex:

Ray tracing
-----------------------------------
.. autofunction:: paos.paos_raytrace.raytrace
    :noindex:

Physical optics propagation
------------------------------------
.. autofunction:: paos.paos_run.run
    :noindex:

Plot results
------------------
.. autofunction:: paos.paos_plotpop.simple_plot
    :noindex:
.. autofunction:: paos.paos_plotpop.plot_pop
    :noindex:

Save results
------------------
.. autofunction:: paos.paos_saveoutput.save_output
    :noindex:
.. autofunction:: paos.paos_saveoutput.save_datacube
    :noindex:

Automatic pipeline
------------------
.. autofunction:: paos.paos_pipeline.pipeline
    :noindex:

