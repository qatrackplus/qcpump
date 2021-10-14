.. _pump_type-mpc:


Varian MPC Pumps
================

.. contents:: Contents
   :depth: 2


.. note::

    The DQA3 pumps are tested on QATrack+ v3.1. QCPump is not compatible with
    QATrack v0.3.X

Varian's automated Machine Performance Check (MPC) stores its results in CSV
files on disk which makes it easy to review those results using third party
programs (thanks Varian!).


How The MPC Pump Works
----------------------

The MPC Pump works by periodically searching the `va_transer\\TDS` directory
for any `Results.csv` files and then grouping the data from the csv files
together and uploading that data to QATrack+.  The data from the `Results.csv`
files are combined based on the following three factors:

1. **The machine they were performed on.**  QCPump uses the serial number from the MPCChecks
   directories to match with a QATrack+ Unit.  For example, for an MPC directory like:

    .. code::

        NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV

    QCPump considers the serial number to be `1234`. In order to upload results
    to QATrack+, QCPump must be able to find a QATrack+ unit with its serial
    number set to `1234`.

2. **The type of MPC check that was run.**  QCPump will retrieve data from the
   following MPC directory types:

    a. GeometryCheckTemplate6xMVkV
        e.g. NDS-WKS-SN####-YYYY-MM-DD-HH-MM-SS-####-GeometryCheckTemplate6xMVkV\\Results.csv
    b. BeamCheckTemplate{energy}{beam_type}
        e.g. NDS-WKS-SN####-YYYY-MM-DD-HH-MM-SS-####-BeamCheckTemplate6x\\Results.csv
    c. GeometryCheckTemplate6xMVkVEnhancedCouch
        e.g. NDS-WKS-SN####-YYYY-MM-DD-HH-MM-SS-####-GeometryCheckTemplate6xMVkVEnhancedCouch\\Results.csv
    d. EnhancedMLCCheckTemplate6x
        e.g. NDS-WKS-SN####-YYYY-MM-DD-HH-MM-SS-####-EnhancedMLCCheckTemplate6x\\Results.csv

    results from a. and b. are grouped together into a single set of results to
    upload to QATrack+, while "enhanced" results from c. and d. are uploaded on
    their own.

3. **The date & time the results files were generated.** For the
   GeometryCheckTemplate & BeamCheckTemplate check types, QCPump will combine
   results from a period of N minutes into a single data set.

For example, given the following list of directories and Results.csv files with a 
time grouping window of 20 minutes:

.. code::


        NDS-WKS-SN5678-2020-06-25-07-10-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv
        NDS-WKS-SN5678-2020-06-25-07-20-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv
        NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate10x\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate10xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-01-21-0000-BeamCheckTemplate18x\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-01-21-0000-BeamCheckTemplate6e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-01-21-0000-BeamCheckTemplate9e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-02-21-0000-BeamCheckTemplate12e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-02-21-0000-BeamCheckTemplate16e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-02-21-0000-BeamCheckTemplate20e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-03-21-0009-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0009-GeometryCheckTemplate6xMVkV\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0000-BeamCheckTemplate6xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0000-BeamCheckTemplate10x\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0000-BeamCheckTemplate10xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-01-21-0000-BeamCheckTemplate18x\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-01-21-0000-BeamCheckTemplate6e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-01-21-0000-BeamCheckTemplate9e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-02-21-0000-BeamCheckTemplate12e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-02-21-0000-BeamCheckTemplate16e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-02-21-0000-BeamCheckTemplate20e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-03-21-0009-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv


the results would be grouped as:

.. code::

        # Group 1) SN 5678, 2020-06-25 07:10, Enhanced Couch Checks
        NDS-WKS-SN5678-2020-06-25-07-10-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv
    
        # Group 2) SN 5678, 2020-06-25 07:20, Enhanced Couch Checks
        # Even though these results were performed within 20min of Group 1),
        # they are not grouped together because they are an "Enhanced" check type.
        NDS-WKS-SN5678-2020-06-25-07-20-30-0000-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv

        # Group 3) SN 6789, 2020-09-30 09:15, Enhanced MLC Checks
        NDS-WKS-SN6789-2020-09-30-09-15-17-0011-EnhancedMLCCheckTemplate6x\Results.csv

        # Group 4) SN 6789, 2020-11-06 09:59, Beam and Geometry Checks
        # These are grouped together because they are not "enhanced" check types and 
        # all occurred within 20min of each other
        NDS-WKS-SN1234-2020-11-06-09-59-21-0009-GeometryCheckTemplate6xMVkV\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate6xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate10x\Results.csv
        NDS-WKS-SN1234-2020-11-06-09-59-21-0000-BeamCheckTemplate10xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-01-21-0000-BeamCheckTemplate18x\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-01-21-0000-BeamCheckTemplate6e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-01-21-0000-BeamCheckTemplate9e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-02-21-0000-BeamCheckTemplate12e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-02-21-0000-BeamCheckTemplate16e\Results.csv
        NDS-WKS-SN1234-2020-11-06-10-02-21-0000-BeamCheckTemplate20e\Results.csv


        # Group 5) SN 1234, 2020-11-06 03:21, Enhanced Couch Checks
        NDS-WKS-SN1234-2020-11-06-10-03-21-0009-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv

        # Group 6) SN 1234, 2020-11-06 11:59, Beam and Geometry Checks
        # These are grouped together because they are not "enhanced" check types and 
        # all occurred within 20min of each other. They are not grouped with Group 4)
        # results because they occurred at least 20 min after the last result from Group 4
        NDS-WKS-SN1234-2020-11-06-11-59-21-0009-GeometryCheckTemplate6xMVkV\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0000-BeamCheckTemplate6xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0000-BeamCheckTemplate10x\Results.csv
        NDS-WKS-SN1234-2020-11-06-11-59-21-0000-BeamCheckTemplate10xFFF\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-01-21-0000-BeamCheckTemplate18x\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-01-21-0000-BeamCheckTemplate6e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-01-21-0000-BeamCheckTemplate9e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-02-21-0000-BeamCheckTemplate12e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-02-21-0000-BeamCheckTemplate16e\Results.csv
        NDS-WKS-SN1234-2020-11-06-12-02-21-0000-BeamCheckTemplate20e\Results.csv

        # Group 7) SN 1234, 2020-11-06 12:03, Enhanced Couch Checks
        NDS-WKS-SN1234-2020-11-06-12-03-21-0009-GeometryCheckTemplate6xMVkVEnhancedCouch\Results.csv


Configuring QATrack+ for MPC Data
---------------------------------

In order to upload MPC data to QATrack+ you need to do a bit of setup work in
QATrack+ first.

Create an API Token
...................

In order to upload your data to QATrack+ via the API you will require an API
token.  See the `QATrack+ documentation
<https://docs.qatrackplus.com/en/stable/api/guide.html#getting-an-api-token>`_
for how to create an API token.  You may wish to create a dedicated user in
QATrack+ just for use with QCPump.  The user will only need a single permission
in order to upload data: `qa | test list instance | Can add test list
instance`.

Configure Your Unit's Serial Numbers
....................................

In order to determine which unit to upload MPC results to, QCPump queries the
QATrack+ API to look for a unit with a serial number matching the MPC directory
it finds results in. For example if QCPump finds a Results.csv file in a
directory like "NDS-WKS-SN\
**1234**-2020-11-06-12-03-21-0009-GeometryCheckTemplate6xMVkVEnhancedCouch"
then it will look for a unit configured in QATrack+ with a serial number of
1234.  If QCPump can't find a unit with a matching serial number, the MPC
results from that directory will be ignored.


Configure Test Lists
....................

You will need 1 or more test lists to record the MPC data uploaded by QCPump.

1. A test list named "MPC: Beam and Geometry Checks" to record data from
   `GeometryCheckTemplate6xMVkV` & `BeamCheckTemplate{energy}{beam_type}` MPC
   results.
2. A test list named "MPC: Enhanced Couch Checks" to record data from
   `GeometryCheckTemplate6xMVkVEnhancedCouch` results files.
3. A test list named "MPC: Enhanced MLC Checks" to record data from
   `EnhancedMLCCheckTemplate6x` results files.


These test lists should have tests with macro names corresponding to the
name of results in the Results.csv files.  The Results.csv files have names
like the following:

.. code:: text

    IsoCenterGroup/IsoCenterSize [mm]
    IsoCenterGroup/IsoCenterMVOffset [mm]
    IsoCenterGroup/IsoCenterKVOffset [mm]
    BeamGroup/BeamOutputChange [%]
    BeamGroup/BeamUniformityChange [%]
    BeamGroup/BeamCenterShift [mm]
    CollimationGroup/MLCGroup/MLCMaxOffsetA [mm]
    CollimationGroup/MLCGroup/MLCMaxOffsetB [mm]
    CollimationGroup/MLCGroup/MLCMeanOffsetA [mm]
    GantryGroup/GantryAbsolute [°], -0.09, 0.3, Pass
    GantryGroup/GantryRelative [°], 0.11, 0.3, Pass

and QCPump transforms these names into valid QATrack+ macro names using the
following rules:

    1. All slashes (`/`) and spaces are converted into underscores (`_`)
    2. Unit replacements are made as follows:

           * `[mm]` is replaced with `mm`,
           * `[%]` is replaced with `per`,
           * `[°]` is replaced with `deg`
    3. The beam energy/type is appended to the macro name 
    4. The macro name is lowercased.

Examples of this substitution from a Results.csv file in a directory called
`NDS-WKS-SN1234-2020-12-01-01-00-00-0009-GeometryCheckTemplate6xMVkV` are:


.. code:: text

    IsoCenterGroup/IsoCenterSize [mm] --> isocentergroup_isocentresize_mm_6x
    BeamGroup/BeamOutputChange [%] -->  beamgroup_beamoutputchange_per_6x
    GantryGroup/GantryAbsolute [°] --> gantrygroup_gantryabsolute_deg_6x


.. warning::

    Currently results for individual MLC leaves are not included.  Any result
    which starts with any of these 4 strings:

    .. code::

        CollimationGroup/MLCGroup/MLCLeavesA/MLCLeaf
        CollimationGroup/MLCGroup/MLCLeavesB/MLCLeaf
        CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesA/MLCBacklashLeaf
        CollimationGroup/MLCBacklashGroup/MLCBacklashLeavesB/MLCBacklashLeaf

    will not be included in the api payload.


As a further example, the following Results.csv file found in a directory with
the name `NDS-WKS-SN1234-2020-12-01-01-00-00-0009-GeometryCheckTemplate6xMVkV`

.. code:: text
    
    Name [Unit], Value, Threshold, Evaluation Result
    IsoCenterGroup/IsoCenterSize [mm], 0.3, 0.5, Pass
    IsoCenterGroup/IsoCenterMVOffset [mm], 0.26, 0.5, Pass
    IsoCenterGroup/IsoCenterKVOffset [mm], 0.25, 0.5, Pass
    BeamGroup/BeamOutputChange [%], -0.17, 2, Pass
    BeamGroup/BeamUniformityChange [%], 0.31, 2, Pass
    BeamGroup/BeamCenterShift [mm], 0.07, 0.5, Pass
    CollimationGroup/MLCGroup/MLCMaxOffsetA [mm], 0.33, 1, Pass
    CollimationGroup/MLCGroup/MLCMaxOffsetB [mm], 0.38, 1, Pass
    CollimationGroup/MLCGroup/MLCMeanOffsetA [mm], 0.24, 1, Pass
    ...
    GantryGroup/GantryAbsolute [°], -0.09, 0.3, Pass


would result in an API payload like this:


.. code:: python

    {
        "unit_test_collection": "https://qatrack.example.com/api/qa/unittestcollections/1234/",
        "work_started": "2020-12-01 01:00",
        "work_completed": "2020-12-01 01:01",
        "user_key": "1234-2020-12-01-01-01",
        "day": 0,
        "tests": {
            isocentergroup_isocentersize_mm_6x: {"value": 0.3},
            isocentergroup_isocentermvoffset_mm_6x: {"value": 0.26},
            # ...
            beamgroup_beamoutputchange_per_6x: {"value": -0.17},
            # ... and so on
            gantrygroup_gantryabsolute_deg: {"value": -0.09}
            # ... and so on
        }
    }
    

Therefore you will need to configure `Simple Numerical` tests for your test
lists with these macro names (or a subset of them).  The names of the tests can
be anything you like, but naming your test the same as the names in the
Results.csv file might be a good idea.  So a Test List might look like:

.. figure:: images/mpc/mpc-beam-and-geometry.png
    :alt: MPC Beam And Geometry Example Test List

    MPC Beam And Geometry Example Test List


.. note:: 

    If QCPump detects that not all tests results for a given test list are included
    when it tries to upload results. It will automatically skip those results
    and attempt to upload the data again.  This allows QCPump to upload partial
    result sets when e.g. you only run a single beam in MPC but your test list
    is configured to receive results from multiple beam types.


Assign Test Lists to Units
..........................

Once you have created these Test Lists in QATrack+ you need to `assign them to
units <https://docs.qatrackplus.com/en/stable/admin/qa/assign_to_unit.html>`_
you want to record DQA3 data for.


MPC QCPump Configuration Options
--------------------------------

MPC
...

TDS Directory
    The "TDS directory" where MPC results are stored. Examples may be I:\\TDS or
    \\\\\\YOURSERVER\\VA_Transer\\TDS

Days of history
     The number of prior days you want to look for data to import. This should
     generall be 1 unless you are doing an initial import of historical results

Results group time interval (min)
    Enter the time interval (in minutes) for which results should be grouped
    together.  That is to say, for Beam & Geometry checks how large of a time window
    should be used to consider MPC results part of the same session.  This value
    should be a little bit longer than the typical time it takes you to run all 
    your morning MPC checks.

Wait for results (min)
    Wait this many minutes for more results to be written to disk before
    uploading grouped results.  In order to ensure all results from an MPC
    session, are written to disk, QCPump will wait this many minutes after the
    most recent Results.csv file it finds for a given machine before uploading
    results to QATrack+.


QATrack+ API
............

Api Url
    Enter the root api url for the QATrack+ instance you want to upload data to. 
    For Example http://yourqatrackserver/api

Auth Token
    Enter an authorization token for the QATrack+ instance you want to upload data to

Throttle
    Enter the minimum interval between data uploads (i.e. a value of 1 will
    allow 1 record per second to be uploded)

Verify SSL
    Set to False if you want to bypass SSL certificate checks (e.g. if your
    QATrack+ instance is using a self signed certificate)

Http Proxy
    QCPump will try to autodetect your current proxy settings. However if you
    want to manually provide a proxy url you may do so. Proxy authentication
    url e.g. http://10.10.1.10:3128 or socks5://user:pass@host:port

Https Proxy
    QCPump will try to autodetect your current proxy settings. However if you
    want to manually provide a proxy url you may do so.Proxy authentication url
    e.g. https://10.10.1.10:3128 or socks5://user:pass@host:port


Test List (depends on QATrack+ API)
...................................

Name
    Enter a template for searching QATrack+ for the name of the Test List you
    want to upload data to. The default is :

        `MPC: {{ check_type}}`

    In the template `{{ check_type }}` will be replaced by either:

        * Beam and Geometry Checks
        * Enhanced Couch Checks
        * Enhanced MLC Checks

    depending on the results being uploaded
