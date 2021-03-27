.. _pump_type-dqa3:




Daily QA3 Pumps
===============

QCPump has the ability to retrieve data from the following Daily QA3 data
sources:

* DQA3 Firebird Database version 01.03
* DQA3 Firebird Database version 01.04
* DQA3 data from Atlas 1.5


.. note::

    The DQA3 pumps are tested on QATrack+ v3.1. QCPump is not 
    currently compatible with QATrack v0.3.X


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
    In order for QCPump to find the correct test list to upload data to, the
    Test List Name must contain both the beam type (X for Photon, E for
    Electron, FFF for flattening filter free).  By default QCPump uses a test list
    name like:

        Daily QA3 Results: {{ energy }}{{ beam_type }}

    where `{{ energy }}` and `{{ beam_type }}` are replaced with the actual
    beam type and energy (e.g. "Daily QA3 Results: 6X" or "Daily QA3 Results: 9E").
    
The test list must also have tests with the following macro names and test
types defined:

data_key: String 
    data_key is a key from the DQA3 database used by QCPump and QATrack+ to
    ensure duplicate entries are not uploaded


The following tests are all optional:

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

        `Daily QA3 Results: {{ energy }}{{ beam_type }}`

    In the template `{{ energy }}` will be replaced by the DQA3 beam energy
    (e.g. 6, 10, 15) and `{{ beam_type }}` will be replaced by the DQA3 beam
    type (e.g. X, E, FFF). This template would result in QCPump trying to find
    a Test List called e.g. "Daily QA3 Results: 6X".

Data Key Test Name
    Enter a template for searching QATrack+ for the name of the Test you
    want to use to ensure duplicate results are not uploaded. The default is :

        `Daily QA3 Results: {{ energy }}{{ beam_type }}: Data Key`

    In the template `{{ energy }}` will be replaced by the DQA3 beam energy
    (e.g. 6, 10, 15) and `{{ beam_type }}` will be replaced by the DQA3 beam
    type (e.g. X, E, FFF). This template would result in QCPump trying to find
    a Test called e.g. "Daily QA3 Results: Data Key 6X".


Unit (depends on QATrack+ API and DQA3Reader configs)
.....................................................

These config options are used to map DQA3 machine names to QATrack+ Unit names.

Dqa3 Name
    Select the DQA3 machine name to map
Unit Name
    Select the QATrack+ Unit name to map the DQA3 name to



.. _pump_type-dqa3-fbd:

Firebird DQA3 Pump Type
-----------------------

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


.. _pump_type-dqa3-atlas:

Atlas (SQL Server) DQA3 Pump Type
---------------------------------


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



Firebird DQA3 File Upload  & Atlas DQA3 File Upload Pump Types
--------------------------------------------------------------

This pump type is the same as the FirebirdDQA3 pump type with the exception
that rather than posting individual test results to QATrack+, all the results
are placed in a csv file which is uploaded through the API.  The format of the
csv file is:

.. code-block:: text

    Field,Value
    dose,123
    dose_baseline,456
    dose_diff,789
    axsym,123
    axsym_baseline,456
    axsm_diff,789
    (and so on)

and includes all the test values as described above. For these pump types your
Test List only requires two tests with the following macro names:

data_key: String 
    data_key is a key from the DQA3 database used by QCPump and QATrack+ to
    ensure duplicate entries are not uploaded

dqa3_upload: Upload
    An upload test type that can be used to parse the uploaded csv file and
    populate other composite tests. An example calculation procedure for this
    looks like:

    .. code-block:: python

        import pandas
        data = pandas.read_csv(FILE)
        dqa3_upload = {}
        for idx, row in data.iterrows()
            dqa3_upload[row['Field']] = pandas.to_numeric(row['Value'], errors="ignore")


    which will results in a dictionary like:

    .. code-block:: python

        dqa3_upload = {
            "signature": "rtaylor",
            "temperature": 123,
            "pressure": 123,
            "dose": 123,
            "dose_baseline": 123,
            "dose_diff": 123,
            "axsym": 123,
            "axsym_baseline": 123,
            "axsym_diff": 123,
            "trsym": 123,
            "trsym_baseline": 123,
            "trsym_diff": 123,
            "qaflat": 123,
            "qaflat_baseline": 123,
            "qaflat_diff": 123,
            "energy": 123,
            "energy_baseline": 123,
            "energy_diff": 123,
            "xsize": 123,
            "xsize_baseline": 123,
            "xsize_diff": 123,
            "ysize": 123,
            "ysize_baseline": 123,
            "ysize_diff": 123,
            "xshift": 123,
            "xshift_baseline": 123,
            "xshift_diff": 123,
            "yshift": 123,
            "yshift_baseline": 123,
            "yshift_diff": 123,
        }


You can then configure other composite tests to be populated by this upload
test. 

The main disadvantage of the file upload pump types is that it may result in
thousands of uploaded files stored on your QATrack+ server hard drive over a
years time.
