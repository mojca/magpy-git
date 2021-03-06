===========
MagPy
===========

Version Info: (please note: this package is still in development state with lots of modifcations between different uploads, detailed version information will be available here starting with 1.0.0) 

MagPy (GeomagPy) provides tools for geomagnetic analysis with special focus on observatories. MagPy combines basic applications like format conversions, plotting routines and mathematical procedures with special geomagnetic analysis routines like basevalue and baseline calculation, database features and WDC dissemination/ communication. Additional routines (not supported by the standard package) comprise acquisition libraries and real-time streaming support as well as an experimental graphical user interface.  

Typical usage often looks like this::

    #!/usr/bin/env python

    from magpy.stream import *
    import magpy.mpplot import mp
    stream = read(path_or_url='filename')
    mp.plot(stream,['x'])

Below you will find a quick guide for the MagPy package. The quickest approach can be accomplished when skipping everything except the tutorials. 

INSTALL
=======

Requirements: Python2.7,  MySQL (all other requirements are resolved)
Recommended: 
Python: NASA SpacePy (), pexpect (for SSH support on non-Windows machines), netcdf (will be supported in a future version)
Other Software: NasaCDF, NetCDF4 (support is currently in preparation), Webserver (e.g. Apache2, PHP)

Linux/Unix
----------
Please check the above requirements first!

1. # Replace x.x.x by the current version
   gunzip -c GeomagPy-x.x.x.tar.gz | tar xf -
   cd GeomagPy-x.x.x
   python setup.py install

2. # Using setuptools
   sudo easy_install GeomagPy
   ### upgarding:
   ### sudo easy_install GeomagPy --upgrade


Windows
-------
Tested on XP and Win7
1. Get a current version of Python(x,y) and install it
   - optionally select packages ffnet and netcdf during install - for cdf support
2. Get a current version of MySQL and install it
3. Download nasaCDF packagess and install
4. get python-spacepy package
5. download and unpack GeomagPy-x.x.x.tar.gz
6. open a command window
7. go to the unpacked directory e.g. cd c:\user\user\Downloads\GeomagPy\
8. execute "setup.py install"


======================
A Quick guide to MagPy
======================

written by R. Leonhardt, R. Bailey (June 2014)

a Getting started
=================

Start python.... 
then import all methods form the stream object

>>> from magpy.stream import *

You should get something like that (if the :
MagPy version x.x.xxx
Loaded Matplotlib - Version [1, 1, 1]
Loading Numpy and SciPy...
Loading Netcdf4 support ...
Loading SpacePy package cdf support ...
trying CDF lib in /usr/local/cdf
SpacePy: Space Science Tools for Python
SpacePy is released under license.
See __licence__ for details, __citation__ for citation information,
and help() for HTML help.
... success
Loading python's SQL support
... success


b Reading and writing data
==========================

You will find a file 'example.min' and an 'example.cdf' within the example directory. The 'cdf' file is stored along with meta information in the NASA's common data format (cdf). Reading this file requires a working installation of Spacepy cdf and a 'success' information when Loading SpacePy as shown in (a).

1. Reading:
-----------
>>> data = read('example.min') 
or
>>> data = read('/path/to/file/example.min') 
or
>>> data = read('c:\path\to\file\example.min')

Different paths are related to your operating system. In the following we will assume a Linux system. 
Any file is uploaded to the memory and each data column (or header information) is assigned to an internal variable (key). To get a quick overview about the assigned keys you can use the following method:
>>> print data._get_key_headers() 

Now we would like to have a IAGA02 and a WDC output

2. Writing:
-----------

Creating an Intermagnet IMF format:
>>> data.write('/path/to/diretory/',filenamebegins='MyIntermagnetFile_',filenameends='.imf',format_type='IMF')
Creating a WDC format:
>>> data.write('/path/to/diretory/',filenamebegins='MyWDCFile_',filenameends='.wdc',format_type='WDC')

By default, daily files are created and the date is added to the filename inbetween the optional parameters 'filenamebegins' and 'filenameends'. If 'filenameends' is missing, '.txt' is used as default.

3. Other possibilities to read files:
-------------------------------------

All local files within a directory:
>>> data = read('/path/to/file/*.min')
Getting magnetic data from the WDC:
>>> data = read('ftp://thewellknownaddress/single_year/2011/fur2011.wdc')
Getting kp data from the GFZ Potsdam:
>>> data = read('http://')
Getting ACE data from NASA:
>>> data = read('http://')
(please note: data access and usage is subjected to terms and policy of the indvidual data provider. Please make sure to read them before accessing any of these products.)

No format specifications are required for reading. If MagPy can handle the format, it will be automatically recognized. A list of supported formats can be found here soon (a method is in preparation).

Getting data of a specific time window:
Local files:
>>> data = read('/path/to/files/*.min',starttime="2014-01-01", endtime="2014-05-01")
Remote files:
>>> data = read('ftp://address/fur2013.wdc',starttime="2013-1-01", endtime="2013-02-01")

4. Tutorial
-----------

For the ongoing quick example please use the following steps. This will create daily IAGA02 files within the directory. Please make sure that the directory is empty before writing data to it.

1. Obtain data from WDC (requires an active internet connection)
>>> data = read('ftp://ftp.nmh.ac.uk/wdc/obsdata/hourval/single_obs/fur/fur2011.wdc',starttime="2011-01-01", endtime="2011-02-01")
2. Store it locally in your favorite directory
>>> data.write('/my/favorite/directory/',filenamebegins='MyExample_', filenameends='.wdc', format_type='WDC')


c Getting help on options and usage
===================================

1. Pythons help function
------------------------

Information on individual methods and their options can be obtained as follows:

For basic functions:
>>> help(read)
For specific methods related to e.g. a stream object "data":
>>> help(data.fit)
(this reqires the existance of a "data" object, which can be done by data = read(...) or data = DataStream() )


2. Tutorial
-----------

>>> help(data.fit)


d Plotting 
==========

You will find some example plots at the `Conrad Observatory <http://www.conrad-observatory.at>`_.

1. Quick (and not dirty)
------------------------

>>> mp.plot(data)

2. Some options
---------------

Select specific keys:
>>> mp.plot(data,['x','y','z'])

3. Multiple streams
-------------------
These procedures require an additional object
>>> from magpy.mpplot import *

4. Tutorial
-----------
Read a second stream
>>> otherdata = read(WDC)
Plot xyz data from both streams
>>> mp.plotStreams([data,otherdata]) 


e Basic geomagnetic methods 
===========================

1. Filtering
------------
>>> filtereddata = data.nfilter()


2. Outlier identification (spikes)
----------------------------------
Outlier identification is using quartiles.

Getting a spiked record:
>>> datawithspikes = read()
Mark all spikes using defaults options
>>> flaggeddata = datawithspikes.flag_outlier()
Show flagged data data
>>> mp.plot(flaggeddata,['f'],annotate=True)
Remove flagged data
>>> datawithoutspikes = flaggeddata.remove_flagged()
Plot all
>>> mp.plotStream([datawithspikes,datawithoutspikes])

3. Flagging
-----------
>>> flaggeddata = data.flag_stream()
>>> mp.plot(flaggeddata,annotate=True)


4. Fitting
----------

5. Interpolation and derivatives
--------------------------------

6. The art of meta information
------------------------------

7. Further methods at a glance
------------------------------


8. Tutorial
-----------


f Multiple streams 
==================

1. delta values e.g. delta F
----------------------------
>>> variodata = read(vario)
>>> variodata = varidata.correct()
>>> variodata = varidata.calc_f()
>>> scalardata = read(scalar)
>>> diffdata = subtractStreams(variodata, scalardata)
>>> mp.plot(diffdata,['f'])
>>> deltaf = diffdata.mean('f')


g Basic data transfer 
=====================

These procedures require an additional object
>>> from magpy.transfer import *

1. Ftp upload
-------------

2. Secure communication
-----------------------


h DI measurements, basevalues and baselines 
===========================================

These procedures require an additional object
>>> from magpy.absolutes import *

1. Data structure of DI measurements
------------------------------------

2. Reading DI data
------------------
absresult = absoluteAnalysis('/path/to/DI/','path/to/vario/','path/to/scalar/', alpha=alpha, deltaF=2.1)
What happens here? 
Firstly, for each DI data set in path/to/DI the appropriate vario and scalar sequences are loaded.

The resulting "absresult" is a stream object containing the DI analysis, the collimation angles, scale factors and the base values for the selected variometer, beside some additional meta information provided in the data input form.

3. Baselines
------------

4. Tutorial
-----------
Prerequisites:
1. Use the Conrad Obs Input sheet on the webpage to input your data (contact R.Leonhardt for help/access on that)
2. Make sure that you have variometer data available e.g. /MyData/Vario/myvariodataset.min
3. Make sure that you have scalar data available e.g. /MyData/Scalar/myscalardataset.min
4. Create an additional directory /MyData/DI-Analysis/
5. Create an additional directory /MyData/DI-Archive/

Getting started (we need the following packages):
>>> from magpy.stream import *
>>> from magpy.absolutes import *
>>> from magpy.transfer import *

# Get DI data from the Cobs-Server
# ################################
>>> ftptransfer()

# Analyzing the DI measurement
# ################################
>>> diresult = analyzeAbsolute()

# Save the result
# ################################
>>> diresult.write()

i Database support  
==================

These procedures require an additional object
>>> from magpy.database import *

1. Setting up a MagPy database (using MySQL)
--------------------------------------------

2. Adding data to the database
------------------------------

>>> db = db.open()
>>> writeDB(db,data)

3. Reading data
------------------

>>> data = readDB(datainfo)

4. Meta data
--------------------

5. Tutorial
-----------


j Acquisition support  
=====================

k Graphical user interface  
==========================

