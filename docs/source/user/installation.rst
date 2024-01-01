.. _installation:

Installation
====================================

.. _install pip:

Install with pip
-------------------

.. warning::
    ``PAOS`` is not on PyPI yet. Please proceed with the installation from Git.

The ``PAOS`` package is hosted on PyPI repository. You can install it by

.. code-block:: console

    pip install paos

.. _install git:

Install from git
-------------------
You can clone ``PAOS`` from its git repository

.. code-block:: console

    git clone https://github.com/arielmission-space/PAOS.git

Move into the ``PAOS`` folder

.. code-block:: console

    cd /your_path/PAOS

Then, just do

.. code-block:: console

    pip install .

To test for correct setup you can do

.. code-block:: console

    python -c "import paos"

If no errors appeared then it was successfully installed.

Additionally the ``PAOS`` program should now be available in the command line

.. code-block:: console

    paos

and the ``PAOS`` GUI (see :ref:`GUI editor`) can be accessed calling

.. code-block:: console

    paosgui

Uninstall `PAOS`
-------------------

``PAOS`` is installed in your system as a standard python package:
you can uninstall it from your Environment as

.. code-block:: console

    pip uninstall paos


Update `PAOS`
---------------

If you have installed ``PAOS`` using Pip, now you can update the package simply as

.. code-block:: console

    pip install paos --upgrade

If you have installed ``PAOS`` from GitHub, you can download or pull a newer version of ``PAOS`` over the old one, replacing all modified data.

Then you have to place yourself inside the installation directory with the console

.. code-block:: console

    cd /your_path/PAOS

Now you can update ``PAOS`` simply as

.. code-block:: console

    pip install . --upgrade

or simply

.. code-block:: console

    pip install .

Modify `PAOS`
---------------

You can modify ``PAOS`` main code, editing as you prefer, but in order to make the changes effective

.. code-block:: console

    pip install . --upgrade

or simply

.. code-block:: console

    pip install .

To produce new ``PAOS`` functionalities and contribute to the code, please see :ref:`Developer Guide`.
