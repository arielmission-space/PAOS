.. _installation:

Installation
============

The following notes guide you toward the installation of PAOS.

Install from git
-------------------
You can clone `PAOS` from our main git repository.

.. code-block:: bash

    $ git clone https://github.com/arielmission-space/PAOS

Then, move into the `PAOS` folder.

.. code-block:: bash

    $ cd /your_path/PAOS

Prepare the run
-----------------

If you want to use `PAOS` in a python shell or jupyter notebook, you may need to add to PYTHONPATH
the path to local `PAOS` path.

This can be done as in the below code example.

.. jupyter-execute::
        :stderr:

        import os, sys
        paospath = "~/git/PAOS"
        if not os.path.expanduser(paospath) in sys.path:
            sys.path.append( os.path.expanduser(paospath) )

        import paos
