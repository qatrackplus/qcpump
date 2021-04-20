.. _pump_type-qatrack-upload:

QATrack+ Generic File Uploads
=============================

QCPump currently has two pumps for uploading text or binary files
to QATrack+.  Both pumps operate by watching a directory for files,
uploading them to a QATrack+ test list, and optionally, moving the
file to a new directory after the file is processed.  



Configuration options
.....................

.. todo:: Add common config options


.. warning::

   Files in your Destination directory may be overwritten by new files if they
   have the same name!


.. _pump_type-qatrack-upload-text:

QATrack+ File Upload: Generic Text File
---------------------------------------

For uploading text files (e.g. csv, Profiler exports, etc)


.. _pump_type-qatrack-upload-binary:

QATrack+ File Upload: Generic Binary File
-----------------------------------------

.. todo:: Text File upload docs

