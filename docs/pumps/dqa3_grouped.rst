.. _pump_type-dqa3-grouped:


Daily QA3 Pumps: Multiple Beams Per Test List
=============================================

This page refers to Pumps which group together results from a single unit
recorded during a short time period to a single test list.  For example, if you
have the following 10 beams configured on a single unit: 6X, 6FFF, 10X, 10FFF,
6X EDW60, 6E, 9E, 12E, 16E, 20E, and perform measurements for all these beams
in a 10 minute period, then QCPump will combine all of these results and upload
to QATrack+ to perform a single test list.  If you prefer to use a single 
test list per beam type to record your results, please see:
:ref:`pump_type-dqa3`.

.. note::

    There are two disadvantages to using the Multiple Beams Per Test List:

    1. If you have many beams configured this will result in very long test
       lists which can impact performance when uploading data, or reviewing
       data in QATrack+.
    2. If you perform a measurement twice (e.g. take 2 6X measurements), only
       the 2nd result will be included.

QCPump currently has the ability to retrieve data from the following Daily QA3
data sources:

* DQA3 Firebird Database version 01.03
* DQA3 Firebird Database version 01.04
* DQA3 SQL Server Database version 01.06
* DQA3 data from Atlas 1.5


.. note::

    The DQA3 pumps are tested on QATrack+ v3.1.X QCPump is not compatible with
    QATrack v0.3.X


.. contents:: Contents
   :depth: 2


.. _pump_type-dqa3-qatrack-grouped:

Configuring QATrack+ for DQA3 Data
----------------------------------

In order to upload DQA3 data to QATrack+ you need to do a bit of setup work in
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


Configure Test Lists
....................

.. note::

    In order to simplify the creation of these test lists, there is a script
    included with QATrack+ v3.1.0+ to generate either a `Test Pack
    <https://docs.qatrackplus.com/en/stable/admin/qa/testpack.html>`_ or to 
    create a TestList directly in your database.  To run the script activate
    your virtualenv, changed to the QATrack+ root directory and then run

    .. code-block::

        # create a test list in the db for photons
        python manage.py runscript create_grouped_dqa3_testlist --script-args db "Daily QA3 Results: Photons" 6X 6FFF 10X 10FFF "6X EDW60"

        # or create a test pack 
        python manage.py runscript create_grouped_dqa3_testlist --script-args testpack "Daily QA3 Results: Electrons" 6E 9E 12E 16E 20E


QCPump requires QATrack+ to have a single Test List per unit configured to
record all your Daily QA3 Results.  The Test List must have a specific set of
attributes:

Test List Name
    Enter the name of the test list you configured in QATrack+ to record your DQA3 results e.g.:

        Daily QA3 Results: Photons


When QCPump gathers data to post to QATrack+, it will convert the DQA3 test
name, into a QATrack+ macro name for each test result. For example if the DQA3
Test/Beam is named "6 MV EDW60" then QCPump would generate test results for
macros named `dose_6_mv_edw60`, `dose_baseline_6_mv_edw60`,
`dose_diff_6_mv_edw60` and so on.  You will need to create tests with at least
one of the following macro names (where {beam_name} is suitably replaced
according to which beam it is for):

data_key_{beam_name}: String 
    data_key is a key from the DQA3 database used by QCPump and QATrack+ to
    ensure duplicate entries are not uploaded

signature_{beam_name}: String
    signature is used to record the username of who completed the measurement

temperature_{beam_name}: Simple numerical
    Temperature measured by the DQA3 device

pressure_{beam_name}: Simple numerical
    The pressure measured by the DQA3 device

dose_{beam_name}:  Simple Numerical
    The dose measured by the DQA3 Device

dose_baseline_{beam_name}: Simple Numerical
    Baseline dose value used

dose_diff_{beam_name}: Simple Numerical
    Difference between measured dose and baseline

axsym_{beam_name}: Simple Numerical
    Axial symmetry value

axsym_baseline_{beam_name}: Simple Numerical
    Axial symmetry baseline value

axsym_diff_{beam_name}: Simple Numerical
    Difference between measured axial symmetry and baseline

trsym_{beam_name}: Simple Numerical
    Transverse symmetry value

trsym_baseline_{beam_name}: Simple Numerical
    Transverse symmetry baseline value

trsym_diff_{beam_name}: Simple Numerical
    Difference between measured transverse symmetry and baseline

qaflat_{beam_name}: Simple Numerical
    Flatness value

qaflat_baseline_{beam_name}: Simple Numerical
    Flatness baseline value

qaflat_diff_{beam_name}: Simple Numerical
    Difference between measured flatness and baseline

energy_{beam_name}: Simple Numerical
    Measured energy value

energy_baseline_{beam_name}: Simple Numerical
    Energy baseline value (always 0)

energy_diff_{beam_name}: Simple Numerical
    Difference between measured and baseline energy

xsize_{beam_name}: Simple Numerical
    Measured width of profile in x direction

xsize_baseline_{beam_name}: Simple Numerical
    Baseline width of profile in x direction

xsize_diff_{beam_name}: Simple Numerical
    Difference bewteen measured and baseline width of profile in x direction

ysize_{beam_name}: Simple Numerical
    Measured width of profile in y direction
    
ysize_baseline_{beam_name}: Simple Numerical
    Baseline width of profile in y direction

ysize_diff_{beam_name}: Simple Numerical
    Difference bewteen measured and baseline width of profile in y direction

xshift_{beam_name}: Simple Numerical
    Measured shift of center of profile in x direction

xshift_baseline_{beam_name}: Simple Numerical
    Baseline shift of center of profile in x direction
    
xshift_diff_{beam_name}: Simple Numerical
    Difference between measured and baseline shift of center of profile in x direction

yshift_{beam_name}: Simple Numerical
    Measured shift of center of profile in y direction

yshift_baseline_{beam_name}: Simple Numerical
    Baseline shift of center of profile in y direction

yshift_diff_{beam_name}: Simple Numerical
    Difference between measured and baseline shift of center of profile in y direction


Here is an example of what a test list configured with a sublist per beam might
look like:


.. figure:: images/dqa3/dqa3_grouped_parent_test_list.png
    :alt: Parent test list for recording DQA3 results

    Parent test list for recording DQA3 results


and the sublist for recording the 6MV results:

.. figure:: images/dqa3/dqa3_grouped_child_test_list.png
    :alt: Child test list for recording 6MV DQA3 results

    Child test list for recording 6MV DQA3 results


Assign Test Lists to Units
..........................

Once you have created these Test Lists in QATrack+ you need to `assign them to
units <https://docs.qatrackplus.com/en/stable/admin/qa/assign_to_unit.html>`_
you want to record DQA3 data for.


DQA3 Common Configuration Options
---------------------------------

Most of the configuration options are the same for the two DQA3 *Pump Types*.
Those settings are outlined here and the DQA3 database connection specific
options are described below.

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

        `Daily QA3 Results: {{ energy }}{{ beam_type }}`

    In the template `{{ energy }}` will be replaced by the DQA3 beam energy
    (e.g. 6, 10, 15) and `{{ beam_type }}` will be replaced by the DQA3 beam
    type (e.g. X, E, FFF). This template would result in QCPump trying to find
    a Test List called e.g. "Daily QA3 Results: 6X".


Unit (depends on QATrack+ API and DQA3Reader configs)
.....................................................

These config options are used to map DQA3 machine names to QATrack+ Unit names.

Dqa3 Name
    Select the DQA3 machine name to map
Unit Name
    Select the QATrack+ Unit name to map the DQA3 name to



.. _pump_type-dqa3-fbd-grouped:

DQA3: Firebird Multiple Beams Per Test List Pump Type
-----------------------------------------------------

Config options specific to Firebird DQA3 databases (01.03.00.00 & 01.04.00.00).

DQA3Reader
..........

Host
    Enter the host name of the Firebird database server you want to connect to

Database
    Enter the path to the database file you want to connect to on the server.
    For example C:\Users\YourUserName\databases\Sncdata.fdb

User
    Enter the username you want to use to connect to the database with

Password
    Enter the password you want to use to connect to the database with

Port
    Enter the port number that the Firebird Database server is listening on

Driver
    Select the database driver you want to use. Use firebirdsql unless you 
    have a good reason not to.

History Days
    Enter the number of prior days you want to look for data to import.  If you
    are importing historical data you may want to temporarily set this to a large
    number of days (i.e. to get the last years worth of data set History days to 365) but
    normally a small number of days should be used to minimize the number of records
    fetched.

Results group time interval (min)
    Enter the time interval (in minutes) for which results should be grouped
    together.  That is to say, for Beam & Geometry checks how large of a time window
    should be used to consider MPC results part of the same session.  This value
    should be a little bit longer than the typical time it takes you to run all 

Wait for results (min)
    Wait this many minutes for more results to be written to disk before
    uploading grouped results.  In order to ensure all results from an MPC
    session, are written to disk, QCPump will wait this many minutes after the
    most recent Results.csv file it finds for a given machine before uploading
    results to QATrack+.

Beam Types
    Select which beam types (Photon, Electron, All) you want to include for
    this pump.  It is a good idea to create separate pumps for electrons and
    photons and corresponding test lists in QATrack+ for recording photon &
    electron results seperately.  The Photon option will include FFF & wedged
    beams.


Creating a Read-Only User for QCPump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While it is not required, you may wish to create a read only user for QCPump
to connect to your database with.  You may either use the Firebird tools
`gsec` and `isql` to create the user or a third party tool like
`FlameRobin <http://flamerobin.org/>`_ which is a great option for
managing users and databases.

**Using gsec to create a new user**

On the server where your Firebird database is located, open a CMD prompt and
enter the following command to create a user with the username `qcpump` and
password `qcpump`:

.. code:: bash

    # for firebird 1.5
    C:\Program Files (x86)\Firebird\Firebird_1_5\bin\gsec.exe" -user sysdba -password masterkey -database "localhost:C:\Program Files (x86)\Firebird\Firebird_1_5\security.fdb
    
    # for firebird 2.5
    C:\Program Files (x86)\Firebird\Firebird_2_5\bin\gsec.exe" -user sysdba -password masterkey -database "localhost:C:\Program Files (x86)\Firebird\Firebird_1_5\security2.fdb


    GSEC> add qcpump -pw qcpump
    GSEC> q


Next you can grant your user select rights using isql.  Open isql specifying
your username and password on the command line:

.. code:: bash

    # for firebird 1.5
    "C:\Program Files (x86)\Firebird\Firebird_1_5\bin\isql.exe" -user sysdba -password masterkey

    # for firebird 2.5
    "C:\Program Files (x86)\Firebird\Firebird_2_5\bin\isql.exe" -user sysdba -password masterkey


and connect to your database:

.. code:: bash

    CONNECT "localhost:C:\Path\To\Your\Database\Sncdata.fdb";

(*note, you may need to replace `localhost` with your actual server host name*)
then grant your user select rights on the tables required:

    .. code:: sql

        GRANT SELECT ON atlas_master to USER qcpump;
        GRANT SELECT ON dqa3_machine to USER qcpump;
        GRANT SELECT ON dqa3_trend to USER qcpump;
        GRANT SELECT ON dqa3_data to USER qcpump;
        GRANT SELECT ON device to USER qcpump;
        GRANT SELECT ON dqa3_calibration to USER qcpump;
        GRANT SELECT ON dqa3_template to USER qcpump;
        GRANT SELECT ON dqa3_machine to USER qcpump;
        GRANT SELECT ON room to USER qcpump;
        quit;


.. figure:: images/dqa3/grant-select-1.5.png
    :alt: Grant qcpump user rights

    Grant qcpump user rights


You should now be able to use the username `qcpump` and password `qcpump` for
the `User` and `Password` settings described above.


.. _pump_type-dqa3-sqlserver-grouped:

DQA3: SQL Server Multiple Beams Per Test List Pump Type
-------------------------------------------------------

Config options specific to SQL Server DQA3 databases.

DQA3Reader
..........

Host
    Enter the host name of the SQL Server database server you want to connect to

Database
    Enter the name of the database you want to connect to on the server.
    For example 'atlas'

User
    Enter the username you want to use to connect to the database with

Password
    Enter the password you want to use to connect to the database with

Port
    Enter the port number that the SQL Server database server is listening on

Driver
    Select the database driver you want to use. On Windows you will typically
    want to use the `ODBC Driver 17 for SQL Server` driver (ensure you have
    this driver installed on the computer running QCPump!). On Linux you will
    likely want to use one of the TDS drivers.

History Days
    Enter the number of prior days you want to look for data to import.  If you
    are importing historical data you may want to temporarily set this to a large
    number of days (i.e. to get the last years worth of data set History days to 365) but
    normally a small number of days should be used to minimize the number of records
    fetched.

Results group time interval (min)
    Enter the time interval (in minutes) for which results should be grouped
    together.  That is to say, for Beam & Geometry checks how large of a time window
    should be used to consider MPC results part of the same session.  This value
    should be a little bit longer than the typical time it takes you to run all 

Wait for results (min)
    Wait this many minutes for more results to be written to disk before
    uploading grouped results.  In order to ensure all results from an MPC
    session, are written to disk, QCPump will wait this many minutes after the
    most recent Results.csv file it finds for a given machine before uploading
    results to QATrack+.

Beam Types
    Select which beam types (Photon, Electron, All) you want to include for
    this pump.  It is a good idea to create separate pumps for electrons and
    photons and corresponding test lists in QATrack+ for recording photon &
    electron results seperately.  The Photon option will include FFF & wedged
    beams.

.. _pump_type-dqa3-atlas-grouped:

DQA3: Atlas Multiple Beams Per Test List Pump Type
--------------------------------------------------

Config options specific to Atlas DQA3 databases (SQLServer).

DQA3Reader
..........

Host
    Enter the host name of the SQL Server database server you want to connect to

Database
    Enter the name of the database you want to connect to on the server.
    For example 'atlas'

User
    Enter the username you want to use to connect to the database with

Password
    Enter the password you want to use to connect to the database with

Port
    Enter the port number that the SQL Server database server is listening on

Driver
    Select the database driver you want to use. On Windows you will typically
    want to use the `ODBC Driver 17 for SQL Server` driver (ensure you have
    this driver installed on the computer running QCPump!). On Linux you will
    likely want to use one of the TDS drivers.

History Days
    Enter the number of prior days you want to look for data to import.  If you
    are importing historical data you may want to temporarily set this to a large
    number of days (i.e. to get the last years worth of data set History days to 365) but
    normally a small number of days should be used to minimize the number of records
    fetched.

Results group time interval (min)
    Enter the time interval (in minutes) for which results should be grouped
    together.  That is to say, for Beam & Geometry checks how large of a time window
    should be used to consider MPC results part of the same session.  This value
    should be a little bit longer than the typical time it takes you to run all 

Wait for results (min)
    Wait this many minutes for more results to be written to disk before
    uploading grouped results.  In order to ensure all results from an MPC
    session, are written to disk, QCPump will wait this many minutes after the
    most recent Results.csv file it finds for a given machine before uploading
    results to QATrack+.

Beam Types
    Select which beam types (Photon, Electron, All) you want to include for
    this pump.  It is a good idea to create separate pumps for electrons and
    photons and corresponding test lists in QATrack+ for recording photon &
    electron results seperately.  The Photon option will include FFF & wedged
    beams.
