.. _release-notes:

Release Notes
=============

v0.3.4
------

* Attempt to correct path for cacert.pem when running in pyinstaller

v0.3.3
------

* Fix stdio redirect
* Fix logging window history
* Add more json decoding errors

v0.3.2
------

* Handle non-missing test 400 Bad Requests when uploading to QATrack+

v0.3.1
------

* The File Mover pump types can now be set to `Copy` mode to have source files
  copied to the destination directory rather than moved

* The Python package `python-certifi-win32` has been added so that requests
  can use the Windows Certificate Store for SSL verification rather than using
  its bundled certificate chain.  This should resolve some issues users were
  having with firewalls & network monitoring software.

* Added a missing permission for the DQA3 QCPump Firebird user

v0.3.0
------

General Features & Fixes
........................


* A bug has been fixed where only the last subsection of a *Multiple*
  configuration section was being validated.

* Pumps which are marked as *Inactive* will not run validation code until they
  are re-activated.  This eliminiates un-necessary network calls and other
  validation work which, in addition to being more efficient overall, makes
  debugging QCPump itself simpler when multiple pumps are configured.

* New MPC pump type for uploading MPC results. See :ref:`pump_type-mpc`.

* New generic pump types for uploading Text & Binary Files to QATrack+ have
  been implemented. See :ref:`pump_type-qatrack-upload`.

* A `DISPLAY_NAME` attribute has been added to Pump Types to aid with grouping
  together similar pump types when adding new pumps.

* Warning level debug messages were being logged as errors. This has been fixed.

* A new `PUMP_ON_STARTUP` (see :ref:`qcpump-settings`) setting has been added
  to allow pumping to begin immediately after QCPump is launched. This allows you
  to place QCPump in a startup folder and have it launched & start pumping when
  your computer is restarted.


DQA3 Pump Type Changes
......................

* The `DATEADD` for calculating a `work_completed` value in Firebird DQA3
  queries has been eliminated in order to allow the query to work with Firebird
  versions < 2.1.  `work_completed` is now just calculated in Python code
  instead.

* The template for looking up Test Lists for beams now defaults to: 
  
    .. code::

        Daily QA3 Results: {{ beam_name }}

  where `beam_name` is is the DQA3 test name (e.g. '6MeV', '6MV WDG', '6MV EDW
  60 Weekly', '20 MeV DQA3 Daily').  This allows QCPump to handle a wider variety
  of beam types/configurations.

* More context variables are available when generating your test list name.  In
  most cases you should only need to use `beam_name`, however other variables
  are available should you need them. See the :ref:`DQA3 Test List Name docs
  <pump_type-dqa3-test-list>`.


* New :ref:`Multiple Beam Per Test List <pump_type-dqa3-grouped>` DQA3 pumps
  have been added which will group results from multiple measurements together
  based on the results being recorded in a short window of time.  There are two
  disadvantages to using the Multiple Beams Per Test List:

    1. If you have many beams configured this will result in long test
       lists which can impact performance when uploading data, or reviewing
       data in QATrack+.

    2. If you perform a measurement twice (e.g. take 2 6X measurements), only
       the 2nd result will be included.

* QATrack+ Unit names will now be displayed along with their Site in order
  to disambiguate units with the same name

* DQA3 machine names will now be shown with their Room name to disambiguate
  machines using the same tree names.
