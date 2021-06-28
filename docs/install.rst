.. _install:

Installing QCPump
-----------------

.. _install-win-installer:


Installing with the Windows Installer
.....................................

On Windows platforms please download the `QCPump Installer
<https://github.com/qatrackplus/qcpump/raw/master/installer/qcpump-setup-0.3.3.exe>`_.
Download and run the installer following the prompts, then go to the
:ref:`pumps-configure-new` page to start configuring some *Pumps*.


.. _install-source:

Obtaining and running from source
.................................


.. note::

    You will need both Python (version 3.7-3.9) and Git installed on 
    your computer to run QCPump from source.


In order to obtain the source code for QCPump install Git and then clone the
QCPump repository:


.. code:: bash

    git clone https://github.com/qatrackplus/qcpump.git


If you are on Windows, visit https://www.lfd.uci.edu/~gohlke/pythonlibs/ and
download DukPy for your particular version of Python.  Now create a new venv to
install the QCPump requirements:

.. code:: bash

    cd qcpump

    # create your venv
    python -m venv env

    # activate venv on Windows and install requirements
    env\Scripts\Activate.ps1
    pip install C:\path\to\dukpy-0.2.3-cp39-cp39-win_amd64.whl
    pip install -r requirements\base.txt

    # activate venv on *nix
    source env/bin/activate
    # replace 18.04 with your Ubuntu version 
    pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-18.04 wxPython
    pip install -r requirements/base.txt


and then to run the program:

.. code:: bash

    python launch_qcpump.py

Now you can proceed to the :ref:`pumps-configure-new` page to start configuring
some *Pumps*.

