Development Notes
=================


Runing tests
------------

The tests can be run by running:

.. code:: bash

    py.test

in the root qcpump directory.


Release Checklist
-----------------

* [ ] Tests all passing
* [ ] docs/release_notes.rst updated
* [ ] Version updated in:

    * [ ] setup.py
    * [ ] qcpump/settings.py
    * [ ] qcpump-installer.iss
    * [ ] docs/install.rst (link to installer)
* [ ] Exe built (`pyinstaller qcpump.spec`)
    * [ ] New data files added to qcpump.spec::data_files
    * [ ] New dependencies added to qcpump.spec::hidden_import
* [ ] Installer built
    * [ ] Installer comitted to repository

* [ ] Installer tested
* [ ] Release tagged  `git tag -a vX.X.X -m vX.X.X`


Building an exe on Windows
--------------------------

In order to create an executable version of QCPump on Windows you need to install pyinstaller:

.. code:: bash

    pip install pyinstaller


Then run:

.. code:: 

    pyinstaller qcpump.spec


Building the Installer
----------------------

* Install Inno Setup Compiler
* Build the exe as described above
* Open qcpump-installer.iss in Inno
* Update MyAppVersion
* Build Menu -> Compile (or Ctrl+F9)
* Test that the installer works and QCPump launches after installation
* Add the installer to the repository and push.
