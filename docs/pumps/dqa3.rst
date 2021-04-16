.. _pump_type-dqa3:




Daily QA3 Pumps: One Beam Per Test List
=======================================

This page refers to Pumps which upload results to a different test list for
each beam.  For example, if you have the following 10 beams configured on a
single unit: 6X, 6FFF, 10X, 10FFF, 6X EDW60, 6E, 9E, 12E, 16E, 20E, then you
will need 10 different test lists assigned to your unit in QATrack+ to record
all of your DQA3 results.  If you prefer to combine all of your results in a
single test list, please see: :ref:`pump_type-dqa3-grouped`.  


.. note::

    There are two disadvantages to using the Multiple Beams Per Test List:

    1. If you have many beams configured this will result in very long test lists
    which can impact performance when uploading data, or reviewing data in QATrack+.
    2. If you perform a measurement twice (e.g. take 2 6X measurements), only the 2nd
    result will be included.


QCPump currently has the ability to retrieve data from the following Daily QA3
data sources:

* DQA3 Firebird Database version 01.03
* DQA3 Firebird Database version 01.04
* DQA3 data from Atlas 1.5


.. note::

    The DQA3 pumps are tested on QATrack+ v3.1.X QCPump is not compatible with
    QATrack v0.3.X


.. contents:: Contents
   :depth: 2


.. _pump_type-dqa3-qatrack:

Configuring QATrack+ for DQA3 Data
----------------------------------

In order to upload DQA3 data to QATrack+ you need to do a bit of setup work in
QATrack+ first.

Create an API Token
...................

In order to upload your data to QATrack+ via the API you will require an API
token.  See the `QATrack+ documentation
<https://docs.qatrackplus.com/en/latest/api/guide.html#getting-an-api-token>`_
for how to create an API token.  You may wish to create a dedicated user in
QATrack+ just for use with QCPump.  The user will only need a single permission
in order to upload data: `qa | test list instance | Can add test list
instance`.


Configure Test Lists
....................

.. note::

    In order to simplify the creation of these test lists, there is a script
    included with QATrack+ v3.1.0+ to generate either a `Test Pack
    <https://docs.qatrackplus.com/en/latest/admin/qa/testpack.html>`_ or to 
    create a TestList directly in your database.  To run the script activate
    your virtualenv, changed to the QATrack+ root directory and then run

    .. code-block::

        # create a 6X test list in the db (replace 6X with your beam type)
        python manage.py runscript create_dqa3_testlist --script-args db 6X

        # or create a 9E test pack (replace 9E with your beam type)
        python manage.py runscript create_dqa3_testlist --script-args testpack 9E


QCPump requires QATrack+ to have a Test List configured for each beam type you
want to upload results for.  For example, if on your linacs you use 6X, 6FFF,
10X, 10FFF, 15X, 6E, 9E, 12E, 16E, 20E beams you will need 10 total test lists
for DQA3 results.  The Test List must have a specific set of attributes:

Test List Name

    The simplest method to have QCPump find the correct test list to upload
    data to is to give the test list a name which contains the name of the DQA3
    Test (e.g. "6 MV", or "6X Daily", or "6 MV EDW60") By default QCPump uses a
    test list name like:

        Daily QA3 Results: {{ beam_name }}

    where QCPump will replace `{{ beam_name }}` with the name of the DQA3 test
    beam (e.g. "Daily QA3 Results: 6X") before searching QATrack+ for the test
    list to perform.  You may also customize your test list name template with
    other variables which include:

    beam_name
        `dqa3_template.tree_name` from a Firebird database (e.g.  "6 MV",
        "6MeV", "6MV WDG", or `MachineTemplate.MachineTestName` from an Atlas
        database. e.g. ("6 MV DQA3 Daily", "6MV EDW60 Weekly", "20 MeV DQA3
        Daily")
    energy
        The beam energy: 6, 9, 10, 15, 18 etc
    beam_type
        One of "Photon", "FFF", or "Electron"
    wedge_type
        Empty for non wedge beams, otherwise "EDW" or "Static"
    wedge_angle
        Empty for non wedge beams, otherwise 30, 45, 60 etc
    wedge_orient
        `dqa3_template.wedgeorient` for FBD databases, or
        `MachineTemplate.WedgeOrient` for Atlas databases.
    device
        Device serial number
    machine_name
        `dqa3_machine.tree_name` for FBD databases, or `Machine.MachineName` for Atlas databases.
    room_name
        `room.tree_name` for FBD databases, or `Machine.RoomNumber` for Atlas databases.


In order to record your data in QATrack+ you will need to add tests to your
Test list with one or more of the following macro names:

data_key: String 
    data_key is a key from the DQA3 database used by QCPump and QATrack+ to
    ensure duplicate entries are not uploaded

signature: String
    signature is used to record the username of who completed the measurement

temperature: Simple numerical
    Temperature measured by the DQA3 device

pressure: Simple numerical
    The pressure measured by the DQA3 device

dose:  Simple Numerical
    The dose measured by the DQA3 Device

dose_baseline: Simple Numerical
    Baseline dose value used

dose_diff: Simple Numerical
    Difference between measured dose and baseline

axsym: Simple Numerical
    Axial symmetry value

axsym_baseline: Simple Numerical
    Axial symmetry baseline value

axsym_diff: Simple Numerical
    Difference between measured axial symmetry and baseline

trsym: Simple Numerical
    Transverse symmetry value

trsym_baseline: Simple Numerical
    Transverse symmetry baseline value

trsym_diff: Simple Numerical
    Difference between measured transverse symmetry and baseline

qaflat: Simple Numerical
    Flatness value

qaflat_baseline: Simple Numerical
    Flatness baseline value

qaflat_diff: Simple Numerical
    Difference between measured flatness and baseline

energy: Simple Numerical
    Measured energy value

energy_baseline: Simple Numerical
    Energy baseline value (always 0)

energy_diff: Simple Numerical
    Difference between measured and baseline energy

xsize: Simple Numerical
    Measured width of profile in x direction

xsize_baseline: Simple Numerical
    Baseline width of profile in x direction

xsize_diff: Simple Numerical
    Difference bewteen measured and baseline width of profile in x direction

ysize: Simple Numerical
    Measured width of profile in y direction
    
ysize_baseline: Simple Numerical
    Baseline width of profile in y direction

ysize_diff: Simple Numerical
    Difference bewteen measured and baseline width of profile in y direction

xshift: Simple Numerical
    Measured shift of center of profile in x direction

xshift_baseline: Simple Numerical
    Baseline shift of center of profile in x direction
    
xshift_diff: Simple Numerical
    Difference between measured and baseline shift of center of profile in x direction

yshift: Simple Numerical
    Measured shift of center of profile in y direction

yshift_baseline: Simple Numerical
    Baseline shift of center of profile in y direction

yshift_diff: Simple Numerical
    Difference between measured and baseline shift of center of profile in y direction


Here is what a sample test list might look like:

.. figure:: images/dqa3/dqa3_single_test_list.png
    :alt: A test list for recording 6MV results

    A test list for recording 6MV results


Assign Test Lists to Units
..........................

Once you have created these Test Lists in QATrack+ you need to `assign them to
units <https://docs.qatrackplus.com/en/latest/admin/qa/assign_to_unit.html>`_
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

        `Daily QA3 Results: {{ energy }}{{ beam_type }}{{ wedge_type }}{{ wedge_angle }}`

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



.. _pump_type-dqa3-fbd:

DQA3: Firebird Individual Beams Pump Type
-----------------------------------------

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
        quit;


.. figure:: images/dqa3/grant-select-1.5.png
    :alt: Grant qcpump user rights

    Grant qcpump user rights


You should now be able to use the username `qcpump` and password `qcpump` for
the `User` and `Password` settings described above.



.. _pump_type-dqa3-atlas:

DQA3: Atlas Individual Beams DQA3 Pump Type
-------------------------------------------


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
