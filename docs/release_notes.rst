.. _release-notes:

Release Notes
=============

v0.3.13
-------

* Made comment uploaded to QATrack+ optional (defaults to off because the comment prevents auto review)

v0.3.12
-------

* Fixed bug related to logging of certificate paths
* Added a "Fast Search" option to MPC pumps. This option will restrict search
  for Results.csv files to subdirectories called MPCChecks. (defaults to on)  
* Adjusted auth headers to make it possible for QCPump to talk to RadMachine

* For FFF beams, added Beam Shape Constancy results from the DQA3\_TREND table for DQA3 v1.06
  SQL Server DBs. There are 9 new results sent to the server:

    .. code-block::

        bsc{1,2,3}_{beam}
        bsc{1,2,3}_baseline_{beam}
        bsc{1,2,3}_diff_{beam}

        e.g. 

        bsc2_6_fff
        bsc2_baseline_6_fff
        bsc_diff_6_fff

  It is believed that bsc2 is the value shown in the DQA3 software so you
  should configure a test in QATrack+/RadMachine with slugs like bsc2_6_fff or
  bsc2_10_fff

* Partial work around for a suspected race condition occuring in the DQA3
  database software. The race condition causes an incorrect data_key to be
  written to the dqa3_trend table, and hence data was being sent to the wrong
  unit.  The workaround implmented here results in the dosimetry data being
  sent to the correct unit, but the temperature, pressure, comment, signature,
  and device serial number will still be incorrect if this occurs again.  This
  is the result of a defect in the DQA3 software and should be exceedingly
  rare.


v0.3.11
-------

* Fixed bug with base64 encoding of files for QATrackGenericBinaryFileUploader pump
* MPC pumps should now handle 2.5X and HDTSE beams
* MPC pumps should handle directory names like NDS-WKS-SN1234-2015-01-01-00-00-00-0001-10x-Beam
* QATrack+ validation requests receiving a 307 Temporary Redirect response will
  retry their request. This is an attempt (possibly in vain) to work arround
  network monitoring software which may temporarily return 307s.

v0.3.10
-------

* Added DQA SQL Server database pumps

v0.3.9
------

* Fix issue with missing Unit names for MPC
* Fix issue with "Â" appearing in some files
* Fixed broken link to QATrack docs

v0.3.8
------

* Allow disabling certificate patching by putting a file called
  nopatch.txt in C:\ProgramData\QATrack Project\qcpump\
* fix to retain unit choices when connection to QATrack+ fails for DQA3 pumps
* Attempt to fix SSL certificate errors in some networks.

v0.3.6
------

* Resolves an issue with unknown null urls being cached leading to pumps
  needing to be restarted in order to "re-discover" the URL to upload data to.

v0.3.5
------

* Ensure ssl certificate files are found / installed by pyinstaller
* Switch to using site_config_dir instead of user_config_dir for storing QCPump
  configs and logs so that multiple users can use same configuration. It is
  recommended that you "Install for All Users" when installing QCPump.
* Instructions for starting QCPump automatically have been added.

v0.3.4
------

* retracted

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
