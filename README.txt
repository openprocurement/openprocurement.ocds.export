Documentation
=============

OCDS export is a project that creates release packages from Openprocurement Data.

Building
--------

Use following commands to build :

``python bootstrap.py``

``bin/buildout -N``

``bin/supervisord``

Usage
------

**bin/packages** runs the export and send it to S3.
    Usage:
          -c CONFIG, --config CONFIG
                        Path to configuration file
          -d DATES              Start-end dates to generate package
          -n NUMBER, --number NUMBER
          -r, --records         Generate record too
          -rec                  Choose to start dump record packages
          -contracting          Choose to include contracting
Examples
------
::
    bin/packages -n 2048
Each generated json will include 2048 releases. Default value is 4096.
::
    bin/packages -d 2016-09-09 -d 2016-09-10
Generate packages only for data which dateModified is between 2016-09-09 and 2016-09-10.
::
    bin/packages -contracting
Generate packages including contracts from contracting module.

All packages are automatically sended to S3. You can configure your own bucket in **templates/bridge.yaml**. Also you can view OpenProcurement Data in OCDS format at ocds.prozorro.openprocurement.io

Timers
------
To run export every friday you can use **systemd-timers**. Configuration files to start it is at **/etc** direcrory.
Commands to execute
    **cd etc**
    **sudo cp export.service /lib/systemd/system/export.service**
    **sudo cp export.timer /lib/systemd/system/export.timer**
    **sudo systemctl start export.timer**
Now OCDS export will start every friday at 03:00 AM.
