Documentation
=============

OCDS export is a project that dumps release packages from Openprocurement Data to json files and sends it to the S3.

Building
--------

Use following commands to build :

``python bootstrap.py``

``bin/buildout -N``

``bin/supervisord``

Usage
--------
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
To run export repeatedly you can use **systemd-timers**. Configuration for this is at **/etc** direcrory.
Commands to execute:
::

    cd etc
    sudo cp export.service /lib/systemd/system/export.service
    sudo cp export.timer /lib/systemd/system/export.timer
    sudo systemctl start export.timer

Now OCDS export will start every friday at 03:00 AM.
