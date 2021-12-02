.. _Quick start:

=======================
Quick start
=======================

Short explanation on how to quickly run `PAOS` and have its output stored in a convenient file.

Running PAOS from console
------------------------------

The quickest way to run `PAOS` is from console.
Run it with the `help` flag to read the available options:

.. code-block:: bash

   $ python paos.py --help

The main command line flags are listed below.

====================  =======================================================================
flag                  description
====================  =======================================================================
-c, --configuration   Input configuration file to pass
-o, --output          Output file
-p, --plot            Save output plots
-n, --nThreads        Number of threads for parallel processing
-d, --debug           Debug mode screen
-l, --log             Store the log output on file
====================  =======================================================================

Where the configuration file shall be an `.xlsx` file and the output file an `.h5` file (see later in :ref:`h5`).
`-n` must be followed by an integer. To activate `-p`, `-d` and `-l` no argument is needed.

Other option flags may be given to run specific simulations.

========================  ===========================================================================
flag                      description
========================  ===========================================================================
-wl, --wavelength         A list of specific wavelengths at which to run the simulation
-wlg, --wavelength_grid   A list with min wl, max wl, spectral resolution to build a wavelength grid
-wfe, --wfe_simulation    A list with wfe realization file and column to simulate an aberration
========================  ===========================================================================

To have a lighter output please use the option flags listed below.

========================  ===========================================================================
flag                      description
========================  ===========================================================================
-keys, --keys_to_keep     A list with the output dictionary keys to save
-lo, --light_output       Save only at last optical surface
========================  ===========================================================================

To activate `-lo` no argument is needed.

A quick look at the outputs
----------------------------

.. _h5:

The `.h5` file
^^^^^^^^^^^^^^^

`PAOS` stores its main output product to a HDF5_ `.h5` file. To open it, please choose your favourite viewer
(e.g. HDFView_, HDFCompass_) or API (e.g. Cpp_, FORTRAN_ and Python_).

.. image:: _static/main_output.png
   :width: 600
   :align: center


.. _HDF5: https://www.hdfgroup.org/solutions/hdf5/

.. _HDFView: https://www.hdfgroup.org/downloads/hdfview/

.. _HDFCompass: https://support.hdfgroup.org/projects/compass/

.. _FORTRAN: https://support.hdfgroup.org/HDF5/doc/fortran/index.html

.. _Cpp: https://support.hdfgroup.org/HDF5/doc/cpplus_RM/index.html

.. _Python: https://www.h5py.org/


The default plot
^^^^^^^^^^^^^^^^^^

An important part of understanding the `PAOS` output is often to look at the default plot. It shows the squared
amplitude of the complex wavefront at an optical surface such as the image plane, using a color scale (linear or
logarithmic). The x and y axes are in physical units, e.g. micron. For reference, dark circular rings are
superimposed on the first five zeros of the circular Airy function. The title of the plot features the optical
surface name, the focal number, the Gaussian beam width, the wavelength and the total optical throughput.

.. image:: _static/default_plot.png
   :width: 600
   :align: center